#!/usr/bin/env python3
"""Optimises Bucky's artwork and app screenshots into static/img.

Every picture is written in a few widths (name-<width>.webp) and listed in
static/img/manifest.json; build.py turns that into srcset attributes, so
phones download small files.

Sources come from the app repo (noisy/Bucky): assets/images, branding/ and
the screenshots rendered by its golden tests (not committed there), e.g.
  flutter test --tags screenshots --update-goldens test/components/screen_screenshots_test.dart
Point BUCKY_APP_DIR at that checkout; by default it is the parent folder,
which is right when this repo is the app's website/ submodule.
The output is committed, so this only runs when the art changes.
"""
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw

SITE = Path(__file__).resolve().parents[1]
APP = Path(os.environ.get("BUCKY_APP_DIR", SITE.parent))
OUT = SITE / "static" / "img"
SHOTS = APP / "test" / "components" / "screenshots" / "screens"
SHOT_DEVICE = "iphone-16-pro-max"
QUALITY = 76
WHITE_THRESHOLD = 40
CREAM = (0xFE, 0xF6, 0xE2)
OG_SIZE = (1200, 630)
OG_MARGIN = 90

ART_WIDTHS = [240, 360, 440, 512]
SHOT_WIDTHS = [280, 460, 660]
MASCOT_WIDTHS = [160, 320]

# (source relative to the app repo, output name, widths)
ARTWORK = [
    ("assets/images/bucky.png", "bucky", [320, 480, 720]),
    ("assets/images/pal.png", "pal", [96, 192]),
    ("assets/images/logo.png", "logo", [200, 400]),
    ("assets/images/lessons/addition.jpg", "lesson-addition", ART_WIDTHS),
    ("assets/images/lessons/multiplication.jpg", "lesson-multiplication", ART_WIDTHS),
    ("assets/images/lessons/dictation.jpg", "lesson-dictation", ART_WIDTHS),
    ("assets/images/bank.jpg", "bank", ART_WIDTHS),
    ("assets/images/bank-building.jpg", "bank-building", ART_WIDTHS),
    ("assets/images/cinema-closed.jpg", "cinema-closed", ART_WIDTHS),
    ("assets/images/bucky-break.jpg", "bucky-break", ART_WIDTHS),
    ("assets/images/bucky-empty.jpg", "bucky-empty", ART_WIDTHS),
    ("assets/images/generic/cinema.jpg", "cinema", ART_WIDTHS),
]

# Screens that show only made-up kid names (never the family's real ones).
SCREENS = [
    "who-is-playing",
    "lesson-addition-with-counters",
    "lesson-split-method",
    "lesson-times-table",
    "lesson-polish-dictation",
    "bank-after-a-day-of-interest",
    "add-videos-channel-with-warnings",
    "kid-settings-addition",
    "parent-home",
]

# Crops from the character sheets, as fractions of the sheet (left, top, right, bottom).
SHEET_CROPS = {
    "branding/mascot/expressions.png": {
        "bucky-happy": (0.009, 0.0, 0.241, 0.425),
        "bucky-excited": (0.259, 0.0, 0.491, 0.425),
        "bucky-thinking": (0.509, 0.0, 0.741, 0.425),
        "bucky-surprised": (0.759, 0.0, 0.991, 0.425),
        "bucky-proud": (0.009, 0.5, 0.241, 0.925),
        "bucky-sleepy": (0.259, 0.5, 0.491, 0.925),
        "bucky-oops": (0.509, 0.5, 0.741, 0.925),
        "bucky-celebrating": (0.759, 0.5, 0.991, 0.925),
    },
    "branding/mascot/fill-states.png": {
        "fill-empty": (0.0, 0.33, 0.245, 0.785),
        "fill-little": (0.25, 0.32, 0.49, 0.785),
        "fill-full": (0.495, 0.29, 0.72, 0.785),
        "fill-overflowing": (0.72, 0.19, 0.995, 0.785),
    },
    "branding/mascot/popcorn-pals.png": {
        "pal-wink": (0.155, 0.645, 0.28, 0.87),
        "pal-sleepy": (0.415, 0.645, 0.54, 0.87),
        "pal-pop": (0.755, 0.56, 0.975, 0.875),
    },
}

manifest: dict[str, dict] = {}


def save_variants(image: Image.Image, name: str, widths: list[int]) -> None:
    widths = sorted({min(width, image.width) for width in widths})
    for width in widths:
        resized = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
        path = OUT / f"{name}-{width}.webp"
        path.parent.mkdir(parents=True, exist_ok=True)
        resized.save(path, "WEBP", quality=QUALITY, method=6)
    manifest[name] = {"widths": widths, "ratio": round(image.height / image.width, 4)}
    print(f"{name}: {widths}")


def save_png(image: Image.Image, name: str) -> None:
    image.save(OUT / f"{name}.png", "PNG", optimize=True)


def social_card() -> Image.Image:
    """The preview image link unfurls show: the logo on the app's cream background."""
    card = Image.new("RGB", OG_SIZE, CREAM)
    logo = Image.open(APP / "assets/images/logo.png").convert("RGBA")
    logo.thumbnail((OG_SIZE[0] - 2 * OG_MARGIN, OG_SIZE[1] - 2 * OG_MARGIN), Image.LANCZOS)
    card.paste(logo, ((OG_SIZE[0] - logo.width) // 2, (OG_SIZE[1] - logo.height) // 2), logo)
    return card


def without_white_background(image: Image.Image) -> Image.Image:
    """Makes the white around a sheet drawing transparent, so it sits on dark pages."""
    image = image.convert("RGBA")
    for corner in ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1)):
        ImageDraw.floodfill(image, corner, (255, 255, 255, 0), thresh=WHITE_THRESHOLD)
    return image.crop(image.getbbox())


def main() -> None:
    for old in OUT.rglob("*.webp"):
        old.unlink()
    for source, name, widths in ARTWORK:
        save_variants(Image.open(APP / source), name, widths)

    for sheet_path, crops in SHEET_CROPS.items():
        sheet = Image.open(APP / sheet_path).convert("RGB")
        for name, (left, top, right, bottom) in crops.items():
            box = (round(left * sheet.width), round(top * sheet.height), round(right * sheet.width), round(bottom * sheet.height))
            save_variants(without_white_background(sheet.crop(box)), name, MASCOT_WIDTHS)

    icon = Image.open(APP / "branding/icon/app-icon.png").convert("RGB")
    save_png(icon.resize((32, 32), Image.LANCZOS), "favicon-32")
    save_png(icon.resize((180, 180), Image.LANCZOS), "apple-touch-icon")
    social_card().save(OUT / "og.jpg", "JPEG", quality=QUALITY, optimize=True)

    for language in ("en", "pl"):
        for screen in SCREENS:
            source = SHOTS / language / SHOT_DEVICE / f"{screen}.png"
            save_variants(Image.open(source).convert("RGB"), f"shots/{language}/{screen}", SHOT_WIDTHS)

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
