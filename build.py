#!/usr/bin/env python3
"""Builds the static site into website/dist: one page per language plus the shared files.

Usage: python3 website/build.py
Every {{key}} in src/page.html must exist in every strings file, and every
string must be used, so a missing translation fails the build.
"""
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src"
DIST = ROOT / "dist"
PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+)(\|url)?\s*\}\}")
ROOT_FILES = ["index.html", "404.html", "robots.txt"]


def render(template: str, strings: dict[str, str], language: str) -> str:
    used = set()

    def fill(match: re.Match) -> str:
        key, url_filter = match.group(1), match.group(2)
        if key not in strings:
            sys.exit(f"{language}: missing string '{key}'")
        used.add(key)
        return quote(strings[key]) if url_filter else strings[key]

    page = PLACEHOLDER.sub(fill, template)
    unused = strings.keys() - used
    if unused:
        sys.exit(f"{language}: unused strings {sorted(unused)}")
    return page


def main() -> None:
    template = (SOURCE / "page.html").read_text()
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    for name in ROOT_FILES:
        shutil.copy(SOURCE / name, DIST / name)
    for strings_file in sorted((SOURCE / "strings").glob("*.json")):
        language = strings_file.stem
        page = render(template, json.loads(strings_file.read_text()), language)
        (DIST / language).mkdir()
        (DIST / language / "index.html").write_text(page)
        print(f"dist/{language}/index.html")


if __name__ == "__main__":
    main()
