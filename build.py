#!/usr/bin/env python3
"""Builds the static site into website/dist: every page in every language plus the shared files.

Usage: python3 website/build.py [page ...]
  e.g. python3 website/build.py download   (publish only the download page)

Settings live in site.json:
  pages              what gets published; the first page is each language's
                     home (/<lang>/), the others live at /<lang>/<page>/
  languages          published languages, each with src/strings/<lang>/
  default_language   used when nothing else picks one
  domain_languages   host name -> language the root page opens (bucky.pl -> pl)
  site_url           absolute base for canonical, hreflang and og: links;
  language_site_urls   per-language override, e.g. an international domain for en
  cname              written to dist/CNAME for GitHub Pages ("" for none)
  apk                path and version of the Android download

Templates are src/pages/<page>.html with {{key}} placeholders ({{key|url}}
URL-encodes) and {{> partial}} includes from src/partials/. Strings come from
src/strings/<lang>/common.json plus src/strings/<lang>/<page>.json. A missing
key fails the build, and so does a page string or a common string that no
page uses, so a translation can't be silently skipped. Links inside the site
are relative, so dist/ works from a domain root or any folder.
"""
import html
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
OG_IMAGE = "static/img/og.jpg"
IMAGE_MANIFEST = ROOT / "static" / "img" / "manifest.json"
IMG_TAG = re.compile(r"<img\b[^>]*>")
IMG_SRC = re.compile(r'src="([^"]*?)static/img/([^"]+)\.webp"')
IMG_SIZE_ATTRS = re.compile(r'\s(?:width|height|srcset)="[^"]*"')
# Common strings the build itself uses (language menus), not the templates.
BUILD_STRINGS = {"language_name", "language_short", "language_menu_label"}


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


def responsive_images(page_html: str, manifest: dict, where: str) -> str:
    """Gives every <img src=".../static/img/<name>.webp"> the srcset of its generated widths.

    Templates name the picture without a width and say how wide it is shown
    (sizes="..."); the browser then downloads the smallest file that is sharp
    enough, so phones get small WebP files.
    """

    def rewrite(match: re.Match) -> str:
        tag = match.group(0)
        src = IMG_SRC.search(tag)
        if not src:
            return tag
        prefix, name = src.groups()
        if name not in manifest:
            sys.exit(f"{where}: no generated image '{name}' (run tools/prepare_images.py)")
        if "sizes=" not in tag:
            sys.exit(f"{where}: <img> of '{name}' needs a sizes attribute")
        widths, ratio = manifest[name]["widths"], manifest[name]["ratio"]
        srcset = ", ".join(f"{prefix}static/img/{name}-{width}.webp {width}w" for width in widths)
        fallback = widths[len(widths) // 2]
        attributes = (
            f'src="{prefix}static/img/{name}-{fallback}.webp" srcset="{srcset}" '
            f'width="{widths[-1]}" height="{round(widths[-1] * ratio)}"'
        )
        return IMG_SRC.sub(attributes, IMG_SIZE_ATTRS.sub("", tag), count=1)

    return IMG_TAG.sub(rewrite, page_html)


def page_path(pages: list[str], page: str, language: str) -> str:
    """Path of a page from the site root, always ending in '/'."""
    return f"{language}/" if page == pages[0] else f"{language}/{page}/"


def relative(from_path: str, to_path: str) -> str:
    """Relative link between two root-relative paths, so the site works from any folder.

    Absolute URLs (such as a GitHub release asset) are returned unchanged.
    """
    if "://" in to_path:
        return to_path
    return "../" * from_path.count("/") + to_path


def absolute(site: dict, language: str | None, path: str) -> str | None:
    base = site["language_site_urls"].get(language) or site["site_url"]
    return f"{base.rstrip('/')}/{path}" if base else None


class Site:
    def __init__(self, site: dict) -> None:
        self.config = site
        self.pages = site["pages"]
        self.languages = site["languages"]
        self.images = load_json(IMAGE_MANIFEST)
        self.common = {language: load_json(SOURCE / "strings" / language / "common.json") for language in self.languages}

    def name(self, language: str) -> str:
        return html.escape(self.common[language]["language_name"])

    def language_links(self, here: str, page: str, current: str | None, css_class: str) -> str:
        items = []
        for language in self.languages:
            href = relative(here, page_path(self.pages, page, language))
            current_attr = ' aria-current="true"' if language == current else ""
            items.append(
                f'<li><a href="{href}" hreflang="{language}" lang="{language}" '
                f'data-lang-switch="{language}"{current_attr}>{self.name(language)}</a></li>'
            )
        return f'<ul class="{css_class}">{"".join(items)}</ul>'

    def language_menu(self, here: str, page: str, language: str) -> str:
        """Header switcher: a <details> menu, so it works without JavaScript and scales to more languages."""
        common = self.common[language]
        return (
            '<details class="lang-menu" data-lang-menu>'
            f'<summary aria-label="{html.escape(common["language_menu_label"])}">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
            '<path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/></svg>'
            f'<span>{html.escape(common["language_short"])}</span></summary>'
            f'{self.language_links(here, page, language, "lang-options")}</details>'
        )

    def hreflang_links(self, page: str, here: str) -> str:
        links = []
        for language in self.languages:
            path = page_path(self.pages, page, language)
            href = absolute(self.config, language, path) or relative(here, path)
            links.append(f'  <link rel="alternate" hreflang="{language}" href="{href}">')
        root = absolute(self.config, None, "") or relative(here, "")
        links.append(f'  <link rel="alternate" hreflang="x-default" href="{root}">')
        own = absolute(self.config, here.split("/")[0], here) if here else None
        if own:
            links.append(f'  <link rel="canonical" href="{own}">')
        return "\n".join(links)

    def build_page(self, page: str, language: str) -> set[str]:
        here = page_path(self.pages, page, language)
        strings = load_json(SOURCE / "strings" / language / f"{page}.json")
        own_url = absolute(self.config, language, here)
        values = {
            **self.common[language],
            **strings,
            "root": relative(here, ""),
            "home_href": relative(here, page_path(self.pages, self.pages[0], language)),
            "apk_href": relative(here, self.config["apk"]["path"]),
            "apk_version": self.config["apk"]["version"],
            "language_menu": self.language_menu(here, page, language),
            "language_list": self.language_links(here, page, language, "footer-langs"),
            "hreflang_links": self.hreflang_links(page, here),
            "og_image": absolute(self.config, language, OG_IMAGE) or relative(here, OG_IMAGE),
            "og_url": f'  <meta property="og:url" content="{own_url}">' if own_url else "",
        }
        for other in self.pages:
            values[f"href_{other}"] = relative(here, page_path(self.pages, other, language))
        template = with_partials((SOURCE / "pages" / f"{page}.html").read_text())
        page_html, used = fill(template, values, f"{language}/{page}")
        unused = strings.keys() - used
        if unused:
            sys.exit(f"{language}/{page}: unused strings {sorted(unused)}")
        write(here + "index.html", responsive_images(page_html, self.images, f"{language}/{page}"))
        return used

    def build_root_files(self) -> None:
        """Language chooser at /, the 404 page, robots.txt and the GitHub Pages files."""
        home = self.pages[0]
        buttons = "".join(
            f'<li><a class="btn btn-primary" href="{page_path(self.pages, home, language)}" hreflang="{language}" '
            f'lang="{language}" data-lang-switch="{language}">{self.name(language)}</a></li>'
            for language in self.languages
        )
        detection = json.dumps({
            "languages": self.languages,
            "fallback": self.config["default_language"],
            "domains": self.config["domain_languages"],
        })
        values = {
            "language_buttons": buttons,
            "language_detection": detection,
            "hreflang_links": self.hreflang_links(home, ""),
            # The 404 page is served at whatever URL was missing, so it links from the root.
            "home_buttons_absolute": buttons.replace('href="', 'href="/'),
        }
        for name in ("index.html", "404.html"):
            page_html, _ = fill((SOURCE / name).read_text(), values, name)
            write(name, responsive_images(page_html, self.images, name))
        robots = (SOURCE / "robots.txt").read_text()
        sitemap = absolute(self.config, None, "sitemap.xml")
        if sitemap:
            robots += f"Sitemap: {sitemap}\n"
            write("sitemap.xml", self.sitemap())
        write("robots.txt", robots)
        write(".nojekyll", "")
        if self.config["cname"]:
            write("CNAME", self.config["cname"] + "\n")

    def sitemap(self) -> str:
        urls = []
        for page in self.pages:
            for language in self.languages:
                path = page_path(self.pages, page, language)
                alternates = "".join(
                    f'<xhtml:link rel="alternate" hreflang="{other}" href="{absolute(self.config, other, page_path(self.pages, page, other))}"/>'
                    for other in self.languages
                )
                urls.append(f"  <url><loc>{absolute(self.config, language, path)}</loc>{alternates}</url>")
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(urls) + "\n</urlset>\n"
        )


def write(path: str, content: str) -> None:
    target = DIST / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    print(f"dist/{path}")


def main() -> None:
    config = load_json(ROOT / "site.json")
    if len(sys.argv) > 1:
        config["pages"] = sys.argv[1:]
    site = Site(config)
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "static", DIST / "static")
    shutil.copytree(ROOT / "downloads", DIST / "downloads", ignore=shutil.ignore_patterns("*.md", ".gitkeep"))
    for language in site.languages:
        used = set()
        for page in site.pages:
            used |= site.build_page(page, language)
        unused = site.common[language].keys() - used - BUILD_STRINGS
        if unused:
            sys.exit(f"{language}: unused common strings {sorted(unused)}")
    site.build_root_files()


if __name__ == "__main__":
    main()
