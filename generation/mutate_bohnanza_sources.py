#!/usr/bin/env python3
"""Reproducibly build the preregistered mutated Bohnanza rulebook PDF."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def replace_exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} source fragment(s), found {count}")
    return text.replace(old, new)


def soffice() -> Path:
    found = shutil.which("soffice")
    candidates = [Path(found)] if found else []
    candidates.append(Path(r"C:\Program Files\LibreOffice\program\soffice.exe"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("LibreOffice soffice is required")


def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def build(source: Path, output: Path) -> None:
    source, output = source.resolve(), output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bohnanza_pdf_mutation_") as temporary:
        work = Path(temporary)
        run([str(soffice()), "--headless", "--convert-to", "fodg", "--outdir", str(work), str(source)])
        fodg = work / f"{source.stem}.fodg"
        text = fodg.read_text(encoding="utf-8")

        text = replace_exact(
            text,
            '<text:p text:style-name="P22"><text:span text:style-name="T4">Du darfst </text:span><text:span text:style-name="T5">jederzeit </text:span><text:span text:style-name="T4">im Spiel deine Bohnenfelder abernten, auch wenn du </text:span></text:p>',
            '<text:p text:style-name="P22"><text:span text:style-name="T4">Du darfst nur als aktiver Spieler deine Bohnenfelder abernten. </text:span></text:p>',
            "P1 harvest right",
        )
        text = replace_exact(
            text,
            '<text:p text:style-name="P22"><text:span text:style-name="T4">nicht der aktive Spieler bist. </text:span></text:p>',
            '<text:p text:style-name="P22"><text:span text:style-name="T4"></text:span></text:p>',
            "P1 harvest continuation",
        )
        text = replace_exact(
            text,
            '<text:p text:style-name="P22"><text:span text:style-name="T4">Anders <text:s/>als <text:s/>im <text:s/>Grundspiel <text:s/>zieht </text:span><text:span text:style-name="T5"><text:s/>jeder </text:span><text:span text:style-name="T4"><text:s/>von <text:s/>euch </text:span><text:span text:style-name="T5"><text:s/>eine <text:s/>Karte <text:s/>vom <text:s/>Nach-</text:span></text:p>',
            '<text:p text:style-name="P22"><text:span text:style-name="T4">Anders <text:s/>als <text:s/>im <text:s/>Grundspiel <text:s/>zieht <text:s/>nur <text:s/>der <text:s/>aktive <text:s/>Spieler </text:span><text:span text:style-name="T5">drei <text:s/>Karten <text:s/>vom <text:s/>Nach-</text:span></text:p>',
            "P2 variant draw",
            expected=2,
        )
        text = replace_exact(
            text,
            '<text:p text:style-name="P22"><text:span text:style-name="T5">ziehstapel </text:span><text:span text:style-name="T4">und steckt sie hinter seine letzte Handkarte. Hierbei beginnt </text:span></text:p>',
            '<text:p text:style-name="P22"><text:span text:style-name="T5">ziehstapel </text:span><text:span text:style-name="T4">und steckt sie hinter seine letzte Handkarte.</text:span></text:p>',
            "P2 draw second line",
            expected=2,
        )
        text = replace_exact(
            text,
            '<text:p text:style-name="P22"><text:span text:style-name="T4">der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.</text:span></text:p>',
            '<text:p text:style-name="P22"><text:span text:style-name="T4"></text:span></text:p>',
            "P2 draw continuation",
            expected=2,
        )
        text = replace_exact(
            text,
            '<text:span text:style-name="T10"><text:s/>nicht </text:span>',
            '<text:span text:style-name="T10"></text:span>',
            "P3 immutable order",
        )
        text = replace_exact(text, "Karten nicht sortieren. ", "Karten jederzeit sortieren. ", "P3 sort warning")

        mutated_fodg = work / "game_rules_mutated.fodg"
        mutated_fodg.write_text(text, encoding="utf-8")
        run([str(soffice()), "--headless", "--convert-to", "pdf", "--outdir", str(work), str(mutated_fodg)])
        generated = work / "game_rules_mutated.pdf"
        if not generated.is_file():
            raise RuntimeError("LibreOffice did not create the mutated PDF")
        shutil.copy2(generated, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
