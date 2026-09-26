#!/usr/bin/env python3
"""Fails if any font in static/fonts/ lacks a letter of the Polish alphabet.

A missing letter makes the browser draw it in a fallback font, so Polish
headings mix two typefaces (Fredoka shipped without ą ć ę ń ś ź ż once).

Usage: pip install fonttools brotli && python3 tools/check_fonts.py
"""
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent.parent / "static" / "fonts"
POLISH_ALPHABET = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"


def main() -> int:
    letters = POLISH_ALPHABET + POLISH_ALPHABET.upper()
    fonts = sorted(FONTS.glob("*.woff2"))
    failed = False
    for path in fonts:
        covered = TTFont(path).getBestCmap()
        missing = "".join(letter for letter in letters if ord(letter) not in covered)
        if missing:
            failed = True
            print(f"{path.name}: no glyph for {missing}")
    if not fonts:
        print(f"no fonts in {FONTS}")
        return 1
    print("Some fonts lack Polish letters." if failed else f"All {len(fonts)} fonts have every Polish letter.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
