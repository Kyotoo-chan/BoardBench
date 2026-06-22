"""Normalize action names into a comparable BoardBench action language.
Why: generated games may use different harmless naming conventions for the same move.

This module never creates actions. It only maps names already emitted by
`action_to_name` into normalized comparison keys. If two different emitted names
normalize to the same key, callers should treat that as an ambiguity instead of
silently merging actions.
"""

from __future__ import annotations

import re
import unicodedata

PROMOTION_WORDS = {
    "q": "q",
    "queen": "q",
    "dame": "q",
    "r": "r",
    "rook": "r",
    "turm": "r",
    "b": "b",
    "bishop": "b",
    "laeufer": "b",
    "läufer": "b",
    "n": "n",
    "knight": "n",
    "springer": "n",
    "k": "k",
    "king": "k",
    "koenig": "k",
    "könig": "k",
}

PASS_WORDS = {"pass", "skip", "wait", "noop", "no-op", "none"}
PLACE_PREFIXES = ("place", "put", "drop", "set", "add")
MOVE_PREFIXES = ("move", "capture", "capt", "take", "jump", "slide", "fly")
REMOVE_PREFIXES = ("remove", "rem", "capture", "capt", "take")

CHESS_SQUARE_RE = re.compile(r"(?<![a-z0-9])[a-h][1-8](?![a-z0-9])")
GENERIC_LABEL_RE = re.compile(r"[a-z][a-z0-9_]*")


def _prepare(name: str) -> str:
    text = unicodedata.normalize("NFKC", str(name)).strip().lower()
    replacements = {
        "→": "->",
        "⟶": "->",
        "⇒": "->",
        "—": "-",
        "–": "-",
        "×": "x",
        "✕": "x",
        "✖": "x",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_label(text: str) -> str:
    text = _prepare(text)
    text = text.strip(" :;/,()[]{}")
    text = re.sub(r"[^a-z0-9_]+", "", text)
    return text


def _split_prefix(text: str) -> tuple[str, str] | None:
    match = re.match(r"^([a-z][a-z0-9_-]*)\s*:\s*(.*)$", text)
    if match is None:
        return None
    return match.group(1).replace("-", "_"), match.group(2).strip()


def _extract_promotion(text: str) -> tuple[str, str]:
    match = re.search(r"(?:=|promote(?:s|d)?(?:-to)?\s+|promotion\s+)\s*([a-zäöü]+)\s*$", text)
    if match is None:
        return text, ""
    promotion = PROMOTION_WORDS.get(match.group(1), "")
    if not promotion:
        return text, ""
    return text[: match.start()].strip(), promotion


def _normalize_route(text: str) -> tuple[str, str, str] | None:
    text, promotion = _extract_promotion(text)
    compact_route = re.sub(r"[^a-z0-9]+", "", text)
    compact_match = re.match(r"^([a-h][1-8])x?([a-h][1-8])([qrbnk])?$", compact_route)
    if compact_match is not None:
        source, target, compact_promotion = compact_match.groups()
        return source, target, promotion or (compact_promotion or "")

    squares = CHESS_SQUARE_RE.findall(text)
    if len(squares) >= 2:
        return squares[0], squares[1], promotion

    for sep in ("->", "=>", " to ", " x ", "-"):
        if sep not in text:
            continue
        source_text, target_text = text.split(sep, 1)
        source = _clean_label(source_text)
        target = _clean_label(target_text)
        if source and target:
            return source, target, promotion

    labels = GENERIC_LABEL_RE.findall(text)
    if len(labels) >= 2:
        return _clean_label(labels[0]), _clean_label(labels[1]), promotion
    return None


def normalize_action_name(name: str) -> str:
    """Return a normalized comparison key for one emitted action name.

    The output uses a small BoardBench grammar such as:
    `place:<target>`, `move:<source>-><target>`, `remove:<target>`,
    `pass`, `chance:<kind>:<value>`, and `p0:<a0>|p1:<a1>`.
    """

    text = _prepare(name)
    if not text:
        return ""

    if "|" in text:
        parts = []
        for raw_part in text.split("|"):
            part = raw_part.strip()
            player_match = re.match(r"^p(\d+)\s*:\s*(.*)$", part)
            if player_match:
                parts.append(f"p{player_match.group(1)}:{normalize_action_name(player_match.group(2))}")
            else:
                parts.append(normalize_action_name(part))
        return "|".join(parts)

    slash_parts = [part.strip() for part in text.split("/") if part.strip()]
    if len(slash_parts) > 1:
        head = normalize_action_name(slash_parts[0])
        suffixes = [normalize_action_name(part) for part in slash_parts[1:]]
        return "/".join([head] + [suffix for suffix in suffixes if suffix])

    compact = re.sub(r"[^a-z0-9_-]+", "", text)
    if compact in PASS_WORDS:
        return "pass"

    if text.startswith(("chance ", "roll ", "deal ")):
        chance_body = text[len("chance ") :] if text.startswith("chance ") else text
        return "chance:" + re.sub(r"[^a-z0-9:_-]+", ":", chance_body).strip(":")

    for prefix in PLACE_PREFIXES:
        if text.startswith(prefix + " "):
            target = _clean_label(text[len(prefix) :])
            return f"place:{target}" if target else "place"

    for prefix in REMOVE_PREFIXES:
        if text.startswith(prefix + " "):
            target = _clean_label(text[len(prefix) :])
            return f"remove:{target}" if target else "remove"

    prefixed = _split_prefix(text)
    if prefixed is not None:
        prefix, body = prefixed
        if prefix == "chance":
            return "chance:" + re.sub(r"[^a-z0-9:_-]+", "", body.replace(" ", ":"))
        if prefix in PLACE_PREFIXES:
            target = _clean_label(body)
            return f"place:{target}" if target else "place"
        if prefix in MOVE_PREFIXES:
            route = _normalize_route(body)
            if route is not None:
                source, target, promotion = route
                suffix = f"={promotion}" if promotion else ""
                return f"move:{source}->{target}{suffix}"
        if prefix in REMOVE_PREFIXES:
            target = _clean_label(body)
            return f"remove:{target}" if target else "remove"

    route = _normalize_route(text)
    if route is not None:
        source, target, promotion = route
        suffix = f"={promotion}" if promotion else ""
        return f"move:{source}->{target}{suffix}"

    return re.sub(r"[^a-z0-9:_>\-=|/]+", "", text)
