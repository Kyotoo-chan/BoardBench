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
SIGNED_TOKEN_RE = r"(?:[+-]?\d+|(?:pos|plus|neg|minus|negative|p|m|n|z|zero)[_ -]?\d+)"
QR_RE = re.compile(
    rf"(?<![a-z0-9])q[_:=\s]*(?P<q>{SIGNED_TOKEN_RE})[,;:_\s]*r[_:=\s]*(?P<r>{SIGNED_TOKEN_RE})(?![a-z0-9])"
)


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


def _parse_signed_token(token: str) -> int | None:
    text = _prepare(token).strip(" :;/,()[]{}")
    text = text.replace(" ", "_").replace("-", "_")
    if re.fullmatch(r"[+]?\d+", text):
        return int(text.lstrip("+"))
    if re.fullmatch(r"-\d+", token.strip()):
        return int(token.strip())

    compact = text.replace("_", "")
    if re.fullmatch(r"\d+", compact):
        return int(compact)

    prefixes = {
        "pos": 1,
        "plus": 1,
        "p": 1,
        "neg": -1,
        "negative": -1,
        "minus": -1,
        "m": -1,
        "n": -1,
        "z": 0,
        "zero": 0,
    }
    for prefix, sign in prefixes.items():
        if not compact.startswith(prefix):
            continue
        magnitude_text = compact[len(prefix) :]
        if not magnitude_text.isdigit():
            continue
        magnitude = int(magnitude_text)
        if sign == 0:
            return 0 if magnitude == 0 else None
        return sign * magnitude
    return None


def parse_qr_coordinates(text: str) -> tuple[int, int] | None:
    """Parse common axial q/r coordinate spellings from an action label.

    This is deliberately conservative: it only recognizes labels that explicitly
    mention both q and r axes. It does not map q/r coordinates to another board's
    official labels; optional reference checks may do that separately.
    """

    prepared = _prepare(text)
    match = QR_RE.search(prepared)
    if match is None:
        return None
    q = _parse_signed_token(match.group("q"))
    r = _parse_signed_token(match.group("r"))
    if q is None or r is None:
        return None
    return q, r


def _signed_int_label(value: int) -> str:
    if value < 0:
        return f"n{abs(value)}"
    if value > 0:
        return f"p{value}"
    return "0"


def _normalize_target_label(text: str) -> str:
    coords = parse_qr_coordinates(text)
    if coords is not None:
        q, r = coords
        return f"q{_signed_int_label(q)}_r{_signed_int_label(r)}"
    return _clean_label(text)


def _encode_numeric_signs(text: str) -> str:
    # Keep sign information before punctuation cleanup. Without this,
    # q-1/r-6 and q+1/r-6 both collapse to q1r6.
    text = re.sub(r"\+(\d+)", r"_pos\1", text)
    text = re.sub(r"-(\d+)", r"_neg\1", text)
    return text


def _clean_label(text: str) -> str:
    text = _prepare(text)
    text = _encode_numeric_signs(text)
    text = text.strip(" :;/,()[]{}")
    text = re.sub(r"[^a-z0-9_]+", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
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
        source = _normalize_target_label(source_text)
        target = _normalize_target_label(target_text)
        if source and target:
            return source, target, promotion

    labels = GENERIC_LABEL_RE.findall(text)
    if len(labels) >= 2:
        return _normalize_target_label(labels[0]), _normalize_target_label(labels[1]), promotion
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
            target = _normalize_target_label(text[len(prefix) :])
            return f"place:{target}" if target else "place"

    for prefix in REMOVE_PREFIXES:
        if text.startswith(prefix + " "):
            target = _normalize_target_label(text[len(prefix) :])
            return f"remove:{target}" if target else "remove"

    prefixed = _split_prefix(text)
    if prefixed is not None:
        prefix, body = prefixed
        if prefix == "chance":
            return "chance:" + re.sub(r"[^a-z0-9:_-]+", "", body.replace(" ", ":"))
        if prefix in PLACE_PREFIXES:
            target = _normalize_target_label(body)
            return f"place:{target}" if target else "place"
        if prefix in MOVE_PREFIXES:
            route = _normalize_route(body)
            if route is not None:
                source, target, promotion = route
                suffix = f"={promotion}" if promotion else ""
                return f"move:{source}->{target}{suffix}"
        if prefix in REMOVE_PREFIXES:
            target = _normalize_target_label(body)
            return f"remove:{target}" if target else "remove"

    route = _normalize_route(text)
    if route is not None:
        source, target, promotion = route
        suffix = f"={promotion}" if promotion else ""
        return f"move:{source}->{target}{suffix}"

    target = _normalize_target_label(text)
    return re.sub(r"[^a-z0-9:_>\-=|/]+", "", target)
