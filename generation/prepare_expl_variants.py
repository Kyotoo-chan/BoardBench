#!/usr/bin/env python3
"""Archive the canonical rulebook and create five predeclared input variants."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "inputs" / "game_rules.pdf"
GAME_DIR = REPO_ROOT / "inputs" / "games" / "expl"
VARIANT_DIR = GAME_DIR / "variants"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source block, found {count}")
    return text.replace(old, new, 1)


def remove_block(text: str, start: str, end: str, label: str) -> str:
    start_at = text.find(start)
    end_at = text.find(end, start_at + len(start))
    if start_at < 0 or end_at < 0:
        raise RuntimeError(f"{label}: source block not found")
    return text[:start_at] + f"[Abschnitt {label} fehlt in dieser Fassung.]\n" + text[end_at:]


def anonymize(text: str) -> str:
    replacements = [
        (r"Exploding Kittens?", "Gefahrenkarte"),
        (r"Entschärfung", "Schutzkarte"),
        (r"Blick in die Zukunft", "Vorschau"),
        (r"Hops!", "Überspringen"),
        (r"Angriff", "Doppelzug"),
        (r"Nö!", "Widerspruch"),
        (r"Mischen", "Neuordnen"),
        (r"Wunsch", "Auswahl"),
        (r"Zombiekatze", "Symbolkarte A"),
        (r"Augenmampfende", "Symbolkarte B"),
        (r"Katzen-Karten", "Symbolkarten"),
        (r"EXPLODING KITTENS", "KARTENSPIEL"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"WWW\.EXPLODINGKITTENS\.COM/HOW", "[externer Link entfernt]", text, flags=re.I)
    return text


def omission_variant(text: str) -> str:
    text = remove_block(
        text,
        "Du beendest deinen eigenen Zug, ohne eine Karte\nzu ziehen, und zwingst den nächsten Spieler, zwei",
        "Wenn du ein Exploding Kitten ziehst, kannst du eine",
        "zur Wirkung der Angriffskarte",
    )
    text = remove_block(
        text,
        "Mit NÖ! setzt du eine",
        "Lege danach das Exploding Kitten zurück in den",
        "zur Wirkung und Reaktionszeit der NÖ!-Karte",
    )
    text = remove_block(
        text,
        "Lege danach das Exploding Kitten zurück in den",
        "Ich spiele Blick",
        "zur Wiedereinfügung nach einer Entschärfung",
    )
    text = replace_once(
        text,
        "Wenn du 5 verschiedene Karten (jede mit\neinem anderen Titel) spielst, darfst du dir eine\nbeliebige Karte aus dem Ablagestapel nehmen.\n(Nicht trödeln, sonst hält dich noch jemand mit\neinem NÖ! von deinem Vorhaben ab.)\n",
        "[Regel für fünf verschiedene Kartentitel fehlt in dieser Fassung.]\n",
        "five-card omission",
    )
    text = replace_once(
        text,
        "Wenn du eine Kombination spielst, gelten die\nAnweisungen auf den Karten nicht.\n",
        "[Hinweis zur Auswertung von Kombinationen fehlt in dieser Fassung.]\n",
        "combination omission",
    )
    return text


def error_variant(text: str) -> str:
    text = replace_once(
        text,
        "Schau dir die obersten drei Karten des\nSpielstapels an und lege sie zurück, ohne deren\nReihenfolge zu verändern. Zeige diese Karten bloß\nnicht deinen Mitspielern.",
        "Schau dir die obersten vier Karten des\nSpielstapels an und lege sie in einer Reihenfolge deiner\nWahl zurück. Zeige diese Karten bloß\nnicht deinen Mitspielern.",
        "false preview rule",
    )
    text = replace_once(
        text,
        "Du beendest deinen eigenen Zug, ohne eine Karte\nzu ziehen, und zwingst den nächsten Spieler, zwei\nSpielzüge direkt nacheinander auszuführen. Dein\nOpfer macht seinen ersten Zug und direkt danach\nnoch einen. (Spielt dein Opfer dabei selbst eine Karte\n„Angriff“ aus, ist er nicht mehr an der Reihe und der\nnächste Spieler muss zwei Spielzüge ausführen.)",
        "Du beendest deinen eigenen Zug, ohne eine Karte\nzu ziehen, und zwingst den nächsten Spieler, drei\nSpielzüge direkt nacheinander auszuführen. Dein\nOpfer macht alle drei Züge. Spielt dein Opfer dabei selbst\neine Karte „Angriff“ aus, kommen zwei weitere Spielzüge\nfür denselben Spieler hinzu.",
        "false attack rule",
    )
    text = replace_once(
        text,
        "(Falls du „Hops!“ ausspielst, um einen\nAngriff abzuwehren, überspringst du nur einen der\nzwei Züge. Du müsstest schon zweimal „Hops!“\nausspielen, um beide Züge zu beenden.)",
        "(Falls du „Hops!“ ausspielst, um einen\nAngriff abzuwehren, werden damit sofort alle noch\nausstehenden Züge beendet.)",
        "false skip rule",
    )
    text = replace_once(
        text,
        "Lege danach das Exploding Kitten zurück in den\nSpielstapel, und zwar geheim an eine Stelle deiner\nWahl, ohne die anderen Karten anzusehen oder\numzusortieren.",
        "Lege danach das Exploding Kitten offen ganz oben\nauf den Spielstapel. Eine andere Position darf nicht\ngewählt werden.",
        "false defuse reinsertion",
    )
    text = replace_once(
        text,
        "Wenn du 5 verschiedene Karten (jede mit\neinem anderen Titel) spielst, darfst du dir eine\nbeliebige Karte aus dem Ablagestapel nehmen.",
        "Wenn du 5 verschiedene Karten (jede mit\neinem anderen Titel) spielst, darfst du dir eine\nbeliebige Karte aus dem Ablagestapel nehmen.\nNimmst du dabei ein Exploding Kitten, explodierst du\nsofort, als hättest du es vom Spielstapel gezogen.",
        "false discard-kitten trigger",
    )
    text = replace_once(
        text,
        "Wenn du ein Exploding Kitten ziehst, kannst du eine\n„Entschärfung“ ausspielen, statt zu sterben.",
        "Wenn du ein Exploding Kitten ziehst und eine\n„Entschärfung“ besitzt, darfst du frei entscheiden, ob\ndu sie nutzt oder freiwillig explodierst.",
        "false optional defuse",
    )
    return text


def vague_variant(text: str) -> str:
    text = replace_once(
        text,
        "Mischt die restlichen Karten sorgfältig. Teilt\ndanach an jeden Spieler verdeckt 7 Karten aus.",
        "Mischt die restlichen Karten ausreichend. Gebt\ndanach jedem Spieler eine angemessene Zahl Karten.",
        "vague hand setup",
    )
    text = replace_once(
        text,
        "Nehmt jetzt von den zur Seite gelegten\nExploding Kittens eine Karte weniger als Spieler\nteilnehmen und mischt sie in den Spielstapel.",
        "Nehmt jetzt eine zur Spielerzahl passende Menge\nExploding Kittens und mischt sie in den Spielstapel.",
        "vague hazard setup",
    )
    text = replace_once(
        text,
        "Eine Runde endet, wenn nur noch ein\nSpieler am Leben ist: der Gewinner.",
        "Eine Runde endet, sobald fast alle ausgeschieden\nsind und ein Gewinner hinreichend erkennbar ist.",
        "vague terminal rule",
    )
    text = replace_once(
        text,
        "Schau dir die obersten drei Karten des\nSpielstapels an und lege sie zurück, ohne deren\nReihenfolge zu verändern. Zeige diese Karten bloß\nnicht deinen Mitspielern.",
        "Schau dir einige der nächsten Karten des\nSpielstapels an und lege sie danach passend zurück.\nBehandle diese Information grundsätzlich vertraulich.",
        "vague preview rule",
    )
    text = replace_once(
        text,
        "Du beendest deinen eigenen Zug, ohne eine Karte\nzu ziehen, und zwingst den nächsten Spieler, zwei\nSpielzüge direkt nacheinander auszuführen. Dein\nOpfer macht seinen ersten Zug und direkt danach\nnoch einen. (Spielt dein Opfer dabei selbst eine Karte\n„Angriff“ aus, ist er nicht mehr an der Reihe und der\nnächste Spieler muss zwei Spielzüge ausführen.)",
        "Du beendest deinen eigenen Zug ohne zu ziehen.\nDer nächste Spieler muss anschließend mehrere Züge\nin sinnvoller Folge ausführen. Ein weiterer Angriff\nverlagert oder erweitert diese Verpflichtung angemessen.",
        "vague attack rule",
    )
    text = replace_once(
        text,
        "Lege danach das Exploding Kitten zurück in den\nSpielstapel, und zwar geheim an eine Stelle deiner\nWahl, ohne die anderen Karten anzusehen oder\numzusortieren.",
        "Lege danach das Exploding Kitten verdeckt an einer\ngeeigneten Stelle in den Spielstapel zurück, ohne den\nübrigen Stapel unangemessen zu verändern.",
        "vague defuse reinsertion",
    )
    text = replace_once(
        text,
        "Wenn du 5 verschiedene Karten (jede mit\neinem anderen Titel) spielst, darfst du dir eine\nbeliebige Karte aus dem Ablagestapel nehmen.",
        "Wenn du mehrere hinreichend verschiedene Karten\nzusammen spielst, darfst du eine passende Karte aus\ndem Ablagestapel aufnehmen. Besondere Karten werden\ndabei ihrer Situation entsprechend behandelt.",
        "vague five-card retrieval",
    )
    return text


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    GAME_DIR.mkdir(parents=True, exist_ok=True)
    VARIANT_DIR.mkdir(parents=True, exist_ok=True)

    canonical = GAME_DIR / "game_rules.pdf"
    if canonical.exists() and sha256(canonical) != sha256(SOURCE):
        raise RuntimeError("archived canonical rulebook has a different hash")
    shutil.copy2(SOURCE, canonical)

    faithful_path = VARIANT_DIR / "expl_txt.txt"
    subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-raw", str(SOURCE), str(faithful_path)],
        check=True,
    )
    faithful = faithful_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    faithful_path.write_text(faithful, encoding="utf-8")

    variants = {
        "expl_anon": anonymize(faithful),
        "expl_omit": omission_variant(faithful),
        "expl_error": error_variant(faithful),
        "expl_vague": vague_variant(faithful),
    }
    for stem, content in variants.items():
        (VARIANT_DIR / f"{stem}.txt").write_text(content, encoding="utf-8")

    paths = {
        "expl_pdf": canonical,
        "expl_txt": faithful_path,
        **{stem: VARIANT_DIR / f"{stem}.txt" for stem in variants},
    }
    manifest = {
        "version": 1,
        "canonical_sha256": sha256(canonical),
        "transformations_declared_before_generation": True,
        "variants": {
            stem: {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": sha256(path)}
            for stem, path in paths.items()
        },
    }
    (VARIANT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
