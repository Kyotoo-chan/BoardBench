"""Fail-closed validation for original and clarified model source packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASE_ROLES = {"publisher_rulebook", "publisher_companion", "user_observation"}
CLARIFICATION_ROLE = "experimenter_clarification"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_sources(kind: str, sources: list[dict], base_dir: Path | None = None) -> None:
    if kind not in {"original", "clarified"}:
        raise ValueError(f"invalid condition kind: {kind}")
    roles = [source.get("role") for source in sources]
    if roles.count("publisher_rulebook") != 1:
        raise ValueError("source condition needs exactly one publisher_rulebook")
    if roles.count("publisher_companion") > 1 or roles.count("user_observation") > 1:
        raise ValueError("source condition permits at most one companion and one observation")
    clarifications = roles.count(CLARIFICATION_ROLE)
    if clarifications != (kind == "clarified"):
        raise ValueError(f"{kind} condition has invalid clarification count: {clarifications}")
    allowed = BASE_ROLES | ({CLARIFICATION_ROLE} if kind == "clarified" else set())
    invalid_roles = sorted(str(role) for role in set(roles) if role not in allowed)
    if invalid_roles:
        raise ValueError(f"invalid source role(s): {invalid_roles}")

    names = [source.get("packet_name") for source in sources]
    if len(set(names)) != len(names) or any(not name or Path(name).name != name for name in names):
        raise ValueError("packet names must be unique basenames")
    for source in sources:
        digest = source.get("sha256", "")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"invalid source hash: {digest}")
        if base_dir is not None:
            root = base_dir.resolve()
            path = (root / source["path"]).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"source path escapes base directory: {source['path']}") from exc
            if not path.is_file() or _sha256(path) != digest:
                raise ValueError(f"source hash mismatch: {path}")


def validate_pair(
    original: list[dict],
    clarified: list[dict],
    original_base_dir: Path | None = None,
    clarified_base_dir: Path | None = None,
) -> None:
    validate_sources("original", original, original_base_dir)
    validate_sources("clarified", clarified, clarified_base_dir or original_base_dir)
    unchanged = lambda values: sorted(
        (item["packet_name"], item["role"], item["sha256"])
        for item in values if item["role"] != CLARIFICATION_ROLE
    )
    if unchanged(original) != unchanged(clarified):
        raise ValueError("clarified condition changed a non-clarification source")


def validate_packet_files(workspace: Path, allowed: set[str]) -> dict[str, str]:
    files = {path.relative_to(workspace).as_posix(): path for path in workspace.rglob("*") if path.is_file()}
    actual = set(files)
    if actual != allowed:
        raise ValueError(f"model packet mismatch: missing={sorted(allowed - actual)}, extra={sorted(actual - allowed)}")
    return {name: _sha256(files[name]) for name in sorted(files)}


def validate_packet_sources(packet_hashes: dict[str, str], sources: list[dict]) -> None:
    for source in sources:
        name = source["packet_name"]
        if packet_hashes.get(name) != source["sha256"]:
            raise ValueError(f"model packet source mismatch: {name}")


def validate_pdf_renders(workspace: Path, sources: list[dict], image_paths: list[Path]) -> None:
    pdf_sources = [source for source in sources if Path(source["packet_name"]).suffix.lower() == ".pdf"]
    supplied_images = {path.resolve() for path in image_paths}
    expected_images: set[Path] = set()
    manifests = list(workspace.rglob("render_manifest.json"))
    for source in pdf_sources:
        matching = []
        for path in manifests:
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("source_file") == source["packet_name"]:
                matching.append((path, value))
        if len(matching) != 1:
            raise ValueError(f"expected one render manifest for {source['packet_name']}, found {len(matching)}")
        path, value = matching[0]
        if value.get("source_sha256") != source["sha256"] or value.get("dpi") != 150:
            raise ValueError(f"invalid render source or DPI: {path}")
        if not value.get("renderer") or not value.get("renderer_version"):
            raise ValueError(f"missing renderer evidence: {path}")
        pages = value.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError(f"empty render manifest: {path}")
        if [page.get("page") for page in pages] != list(range(1, len(pages) + 1)):
            raise ValueError(f"non-contiguous rendered pages: {path}")
        for page in pages:
            page_path = (path.parent / page.get("file", "")).resolve()
            try:
                page_path.relative_to(workspace.resolve())
            except ValueError as exc:
                raise ValueError(f"rendered page escapes workspace: {page_path}") from exc
            if not page_path.is_file() or _sha256(page_path) != page.get("sha256"):
                raise ValueError(f"rendered page hash mismatch: {page_path}")
            expected_images.add(page_path)
    if len(manifests) != len(pdf_sources):
        raise ValueError("unexpected PDF render manifest")
    if supplied_images != expected_images:
        raise ValueError("image paths do not exactly match rendered PDF pages")
