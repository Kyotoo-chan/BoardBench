"""Build LLM judge review packets (code + rulebook). Shared by notebook and calibration."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO_ROOT / "prompts" / "rulebook_to_python.txt"
JUDGE_PROMPT_PATH = REPO_ROOT / "prompts" / "llm_judge_review.md"
BACKBONE_PATH = REPO_ROOT / "prompts" / "open_spiel_backbone.md"


def read_rules_text(rules_path: Path) -> str:
    if rules_path.suffix.lower() == ".txt":
        return rules_path.read_text(encoding="utf-8")
    if rules_path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("PDF rulebooks require pypdf") from exc
        reader = PdfReader(str(rules_path))
        return "\n\n".join(
            page_text.strip()
            for page in reader.pages
            for page_text in [page.extract_text() or ""]
            if page_text.strip()
        )
    raise ValueError(f"Unsupported rules file: {rules_path}")


def build_judge_packet(
    *,
    code_path: Path,
    rules_path: Path,
    output_path: Path,
    game_label: str,
    variant: str = "oneshot",
    open_spiel_game: str = "none",
    note: str | None = None,
) -> Path:
    if not code_path.exists():
        raise FileNotFoundError(f"Missing code: {code_path}")
    if not rules_path.exists():
        raise FileNotFoundError(f"Missing rulebook: {rules_path}")
    if not JUDGE_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing judge prompt: {JUDGE_PROMPT_PATH}")

    sections = [
        "# BoardBench judge packet",
        f"- game label: {game_label}",
        f"- OpenSpiel reference: {open_spiel_game}",
        f"- variant: {variant}",
        f"- generated code: {code_path.as_posix()}",
        f"- rulebook: {rules_path.as_posix()}",
    ]
    if note:
        sections.append(f"- calibration note: {note}")
    sections += [
        "",
        "## Judge prompt",
        JUDGE_PROMPT_PATH.read_text(encoding="utf-8"),
        "",
        f"## Generation prompt ({PROMPT_PATH.as_posix()})",
        PROMPT_PATH.read_text(encoding="utf-8"),
    ]
    if BACKBONE_PATH.exists():
        sections += [
            "",
            f"## OpenSpiel backbone ({BACKBONE_PATH.as_posix()})",
            BACKBONE_PATH.read_text(encoding="utf-8"),
        ]

    rules_text = read_rules_text(rules_path)
    if rules_text.strip():
        sections += ["", f"## Rule text ({rules_path.as_posix()})", rules_text]
    else:
        sections += [
            "",
            f"## Rulebook PDF ({rules_path.as_posix()})",
            "_No extractable text — use rendered page images if attached separately._",
        ]

    sections += [
        "",
        f"## Generated code ({code_path.as_posix()})",
        "```python\n" + code_path.read_text(encoding="utf-8") + "\n```",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(sections), encoding="utf-8")
    return output_path
