#!/usr/bin/env python3
"""Builds the static site into website/dist: every page in every language plus the shared files.

Usage: python3 website/build.py [page ...]
  e.g. python3 website/build.py download   (publish only the download page)

Settings live in site.json. "pages" lists what gets published; the first one
is each language's home (/<lang>/), the others live at /<lang>/<page>/. So
["download"] publishes just the simple download page, ["landing", "download"]
the full site.

Templates are src/pages/<page>.html with {{key}} placeholders ({{key|url}}
URL-encodes) and {{> partial}} includes from src/partials/. Strings come from
src/strings/<lang>/common.json plus src/strings/<lang>/<page>.json. A missing
key fails the build, and so does a page string or a common string that no
page uses, so a translation can't be silently skipped.
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
PARTIAL = re.compile(r"\{\{>\s*([a-z0-9_-]+)\s*\}\}")
PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+)(\|url)?\s*\}\}")
ROOT_FILES = ["index.html", "404.html", "robots.txt"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def with_partials(template: str) -> str:
    return PARTIAL.sub(lambda m: with_partials((SOURCE / "partials" / f"{m.group(1)}.html").read_text()), template)


def fill(template: str, values: dict[str, str], where: str) -> tuple[str, set[str]]:
    used = set()

    def value(match: re.Match) -> str:
        key, url_filter = match.group(1), match.group(2)
        if key not in values:
            sys.exit(f"{where}: missing string '{key}'")
        used.add(key)
        return quote(values[key]) if url_filter else values[key]

    return PLACEHOLDER.sub(value, template), used


def page_path(pages: list[str], page: str, language: str) -> str:
    """Path of a page from the site root, always ending in '/'."""
    return f"{language}/" if page == pages[0] else f"{language}/{page}/"


def relative(from_path: str, to_path: str) -> str:
    """Relative link between two root-relative paths, so the site works from any folder."""
    return "../" * from_path.count("/") + to_path


def build_page(site: dict, page: str, language: str, common: dict, strings: dict) -> set[str]:
    pages = site["pages"]
    here = page_path(pages, page, language)
    values = {**common, **strings}
    values["root"] = relative(here, "")
    values["home_href"] = relative(here, page_path(pages, pages[0], language))
    values["apk_href"] = relative(here, site["apk"]["path"])
    values["apk_version"] = site["apk"]["version"]
    values["other_lang_href"] = relative(here, page_path(pages, page, common["other_lang"]))
    for other in pages:
        values[f"href_{other}"] = relative(here, page_path(pages, other, language))
    template = with_partials((SOURCE / "pages" / f"{page}.html").read_text())
    html, used = fill(template, values, f"{language}/{page}")
    unused = strings.keys() - used
    if unused:
        sys.exit(f"{language}/{page}: unused strings {sorted(unused)}")
    target = DIST / here / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)
    print(f"dist/{here}index.html")
    return used


def main() -> None:
    site = load_json(ROOT / "site.json")
    if len(sys.argv) > 1:
        site["pages"] = sys.argv[1:]
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    shutil.copytree(ROOT / "downloads", DIST / "downloads", ignore=shutil.ignore_patterns("*.md", ".gitkeep"))
    for name in ROOT_FILES:
        shutil.copy(SOURCE / name, DIST / name)
    for language_dir in sorted(p for p in (SOURCE / "strings").iterdir() if p.is_dir()):
        language = language_dir.name
        common = load_json(language_dir / "common.json")
        used = set()
        for page in site["pages"]:
            used |= build_page(site, page, language, common, load_json(language_dir / f"{page}.json"))
        unused = common.keys() - used
        if unused:
            sys.exit(f"{language}: unused common strings {sorted(unused)}")


if __name__ == "__main__":
    main()
