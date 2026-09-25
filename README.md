# Bucky website

The public site for Bucky, in English (`/en/`) and Polish (`/pl/`): a
landing page and a simple download page for the Android APK.
Plain static HTML, one stylesheet and a few lines of JavaScript. No
frameworks, no trackers, no third-party requests: fonts and images are
served from this folder.

## Preview locally

```sh
python3 website/build.py
python3 -m http.server 8000 -d website/dist
```

Then open http://localhost:8000/ (it redirects to your browser's language)
or http://localhost:8000/en/ and http://localhost:8000/pl/ directly.

`website/dist/` is generated and not committed; upload that folder to any
static host.

### Early launch: only the download page

```sh
python3 website/build.py download
```

publishes just the download page as each language's home (`/en/`, `/pl/`).
Plain `python3 website/build.py` uses the pages listed in `site.json`
(landing first, then `/<lang>/download/`).

### The APK

Copy the release build to `website/downloads/bucky-latest.apk` before
building (APKs are gitignored and never committed) and set the version in
`site.json` (`apk.version`, a placeholder for now). Installing over an older
version keeps the kids' data because every build is signed with the same
key.

## How it is put together

| Path | What |
|---|---|
| `site.json` | Which pages are published, APK path and version |
| `src/pages/landing.html`, `src/pages/download.html` | Page templates, with `{{key}}` placeholders (`{{key\|url}}` URL-encodes) and `{{> partial}}` includes |
| `src/partials/` | Shared `<head>` tags and the footer |
| `src/strings/<lang>/common.json`, `<page>.json` | All copy per language. The build fails on a missing or unused key |
| `downloads/` | Where the APK goes before a build (gitignored) |
| `src/index.html` | Root page: sends visitors to their saved or browser language, with plain links as a fallback |
| `src/404.html`, `src/robots.txt` | Copied to the site root as they are |
| `static/css/site.css` | All styling. Brand tokens from `branding/palette/colors.json`, light and dark (`prefers-color-scheme`) |
| `static/js/site.js` | Remembers the language picked in the switcher; header hairline on scroll. The page works without it |
| `static/fonts/` | Fredoka and Nunito (SIL OFL), subset to Latin and Polish letters as woff2 |
| `static/img/` | Optimised WebP artwork and app screenshots (generated, see below) |
| `tools/prepare_images.py` | Regenerates `static/img/` from `assets/images/`, `branding/` and the screenshot tests |

To add a language: copy `src/strings/en/` to `src/strings/<lang>/`, translate,
render the app screenshots for that locale and add it to the language
links in `src/page.html` and `src/index.html`.

### Images and screenshots

The app screenshots are the real screens, rendered by the golden tests
(not committed). To refresh them:

```sh
flutter test --tags screenshots --update-goldens test/components/screen_screenshots_test.dart
python3 website/tools/prepare_images.py   # needs Pillow
```

Only screens with the made-up kid names (Little Popper, Big Popper) are
used. Collection covers of third-party cartoons are deliberately not on
the site.

### Fonts

Regenerated from `assets/fonts/` with fontTools:

```sh
pyftsubset assets/fonts/Fredoka-Bold.ttf --flavor=woff2 --layout-features='*' \
  --unicodes='U+0000-00FF,U+0100-017F,U+2010-2027,U+2030-203A,U+20AC,U+2122,U+2190-2193,U+2212' \
  --output-file=website/static/fonts/Fredoka-Bold.woff2
```

(the same for Fredoka-SemiBold, Nunito-Regular and Nunito-Bold).

## TODO

- **Domain and hosting.** Not chosen. Any static host works (GitHub Pages,
  Cloudflare Pages, Netlify); nothing is deployed yet.
- **Absolute URLs** once the domain is known: `og:url`, absolute `og:image`,
  canonical links and a `sitemap.xml` (see the TODO in `src/robots.txt`).
- **Contact / early access.** The button is a `mailto:hello@example.com`
  placeholder (marked `data-todo="contact"` and with a TODO comment in
  `src/page.html`). Replace with the real address or a sign-up form.
- **APK version** in `site.json` is a placeholder (`0.0.0`); set it per release
  (or have the deploy job fill it in).
- **Store links.** Google Play and App Store badges once the listings exist
  (today: GitHub prerelease APKs and TestFlight).
- **Legal pages.** A privacy policy page (the content is in
  `docs/privacy.md`) and an imprint / contact page, needed before app
  store listings anyway.
- **Polish copy** would benefit from a native proofread.
- **Vector mascot.** The artwork is raster (see `branding/BRANDING.md`);
  swap in SVG or Lottie when it exists.
