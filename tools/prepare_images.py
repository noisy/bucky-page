#!/usr/bin/env python3
"""Optimises the repo's artwork and app screenshots into website/static/img.

Artwork comes from assets/images and branding/. Screenshots come from the
golden tests, which are not committed; render them first with
  flutter test --tags screenshots --update-goldens test/components/screen_screenshots_test.dart
The output is committed, so this only needs to run when the art changes.
"""
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "website" / "static" / "img"
SHOTS = REPO / "test" / "components" / "screenshots" / "screens"
SHOT_DEVICE = "iphone-16-pro-max"
SHOT_WIDTH = 440
QUALITY = 82

# (source relative to the repo, output name, width in px)
ARTWORK = [
    ("assets/images/bucky.png", "bucky", 560),
    ("assets/images/pal.png", "pal", 160),
    ("assets/images/logo.png", "logo", 400),
    ("assets/images/lessons/addition.jpg", "lesson-addition", 480),
    ("assets/images/lessons/multiplication.jpg", "lesson-multiplication", 480),
    ("assets/images/lessons/dictation.jpg", "lesson-dictation", 480),
    ("assets/images/bank.jpg", "bank", 480),
    ("assets/images/cinema-closed.jpg", "cinema-closed", 480),
    ("assets/images/bucky-break.jpg", "bucky-break", 480),
    ("assets/images/bucky-empty.jpg", "bucky-empty", 480),
    ("assets/images/generic/cinema.jpg", "cinema", 480),
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

# Expressions sheet: 4 columns x 2 rows, labels below each face.
EXPRESSIONS = ["happy", "excited", "thinking", "surprised", "proud", "sleepy", "oops", "celebrating"]
WHITE_THRESHOLD = 40
CREAM = (0xFE, 0xF6, 0xE2)
OG_SIZE = (1200, 630)
OG_MARGIN = 90
EXPRESSION_FACE_HEIGHT = 0.425
EXPRESSION_INSET = 24  # px, keeps a neighbour's stray confetti out  # of the sheet height, cuts the label off


def save(image: Image.Image, name: str, width: int) -> None:
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    path = OUT / f"{name}.webp"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", quality=QUALITY, method=6)
    print(f"{path.relative_to(REPO)}  {path.stat().st_size // 1024} KB")


def save_png(image: Image.Image, name: str) -> None:
    path = OUT / f"{name}.png"
    image.save(path, "PNG", optimize=True)
    print(f"{path.relative_to(REPO)}  {path.stat().st_size // 1024} KB")


def social_card() -> Image.Image:
    """The preview image link unfurls show: the logo on the app's cream background."""
    card = Image.new("RGB", OG_SIZE, CREAM)
    logo = Image.open(REPO / "assets/images/logo.png").convert("RGBA")
    logo.thumbnail((OG_SIZE[0] - 2 * OG_MARGIN, OG_SIZE[1] - 2 * OG_MARGIN), Image.LANCZOS)
    card.paste(logo, ((OG_SIZE[0] - logo.width) // 2, (OG_SIZE[1] - logo.height) // 2), logo)
    return card


def without_white_background(image: Image.Image) -> Image.Image:
    """Makes the white around a sheet drawing transparent, so it sits on dark pages."""
    image = image.convert("RGBA")
    for corner in ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1)):
        ImageDraw.floodfill(image, corner, (255, 255, 255, 0), thresh=WHITE_THRESHOLD)
    return image


def main() -> None:
    for source, name, width in ARTWORK:
        save(Image.open(REPO / source), name, width)
    icon = Image.open(REPO / "branding/icon/app-icon.png").convert("RGB")
    save_png(icon.resize((32, 32), Image.LANCZOS), "favicon-32")
    save_png(icon.resize((180, 180), Image.LANCZOS), "apple-touch-icon")
    social_card().save(OUT / "og.jpg", "JPEG", quality=QUALITY, optimize=True)

    sheet = Image.open(REPO / "branding/mascot/expressions.png").convert("RGB")
    cell_w, cell_h = sheet.width // 4, sheet.height // 2
    for index, expression in enumerate(EXPRESSIONS):
        left, top = (index % 4) * cell_w + EXPRESSION_INSET, (index // 4) * cell_h
        right, bottom = left + cell_w - 2 * EXPRESSION_INSET, top + round(sheet.height * EXPRESSION_FACE_HEIGHT)
        face = sheet.crop((left, top, right, bottom))
        save(without_white_background(face), f"bucky-{expression}", 320)

    for language in ("en", "pl"):
        for screen in SCREENS:
            source = SHOTS / language / SHOT_DEVICE / f"{screen}.png"
            save(Image.open(source).convert("RGB"), f"shots/{language}/{screen}", SHOT_WIDTH)


if __name__ == "__main__":
    main()
