# Bucky website

The public site for Bucky, in English (`/en/`) and Polish (`/pl/`): a
landing page, a simple download page for the Android APK, and the iPhone
and iPad beta sign-up with its privacy note.
Plain static HTML, one stylesheet and a few lines of JavaScript. No
frameworks, no trackers, no third-party requests: fonts and images are
served from this folder. The one exception is the beta form, which loads
Google's Firebase SDK when it is sent (see iOS beta sign-up).

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

The download button links to a versioned APK, e.g. `bucky-0.2.0-373.apk`,
attached to the release of the same tag in this repository (`apk.path` in
`site.json`), and the version shows under the button (`apk.version`). APKs
are never committed or deployed with the site. Each Bucky release does this
automatically (`scripts/ci/publish_website_apk.sh` in noisy/Bucky); see
`downloads/README.md`. Installing over an older
version keeps the kids' data because every build is signed with the same
key.

## How it is put together

| Path | What |
|---|---|
| `site.json` | Pages, languages, domains, `CNAME`, APK path and version |
| `src/pages/landing.html`, `download.html`, `beta.html`, `beta-privacy.html` | Page templates, with `{{key}}` placeholders (`{{key\|url}}` URL-encodes) and `{{> partial}}` includes. Links between pages are `{{href_<page>}}`, with `-` written as `_` (`{{href_beta_privacy}}`) |
| `src/partials/` | Shared `<head>` tags and the footer |
| `src/strings/<lang>/common.json`, `<page>.json` | All copy per language. The build fails on a missing or unused key |
| `downloads/` | How to ship an APK (the file itself lives in releases) |
| `src/index.html` | Root page: picks the language (see Languages), with plain links as a fallback |
| `src/404.html`, `src/robots.txt` | Site-root files; the build adds `CNAME`, `.nojekyll` and `sitemap.xml` |
| `static/css/site.css` | All styling, mobile first: base rules for 360-430px phones, `min-width` queries add tablet (600px), laptop (900px) and wide (1100px). Brand tokens from the app palette, light and dark (`prefers-color-scheme`) |
| `static/js/site.js` | Remembers the language picked in the switcher, closes the menus, hides the phone download dock while the hero button is on screen. The page works without it |
| `static/js/beta.js` | The iOS beta sign-up form (only on `/<lang>/beta/`) |
| `static/fonts/` | Fredoka and Nunito (SIL OFL), subset to Latin and Polish letters as woff2 |
| `static/img/` | Optimised WebP artwork and app screenshots (generated, see below) |
| `tools/prepare_images.py` | Regenerates `static/img/` (all widths and the manifest) from the app repo art and screenshots |

### Languages

English and Polish today; everything is keyed by language, so more can be
added without touching the templates:

1. Copy `src/strings/en/` to `src/strings/<lang>/` and translate it
   (`language_name` is the language's own name, e.g. "Deutsch").
2. Add the code to `languages` in `site.json`.
3. Render the app screenshots for that locale (see below) or point the
   landing template at an existing locale's screenshots.

The switcher in the header and the footer lists every language and keeps
the visitor on the same page. The root page `/` picks a language in this
order: an explicit earlier choice (saved in `localStorage` when a language
link is clicked), the domain (`domain_languages`: bucky.pl opens Polish),
the browser's `navigator.languages`, then `default_language` (English).
Every page has its own `<html lang>`, translated title and description,
`hreflang` alternates, a canonical link and `og:` tags.

### Hosting (GitHub Pages)

The build is made for GitHub Pages on a custom domain, but nothing is
deployed from here. Publish the contents of `website/dist/` (for example
with `actions/upload-pages-artifact` + `actions/deploy-pages`, running
`python3 website/build.py` first). `dist/` already contains:

- `CNAME` with `bucky.club` (from `cname` in `site.json`),
- `404.html` (root-relative links, as GitHub Pages serves it at any path),
- `.nojekyll`, `robots.txt` and `sitemap.xml`.

Links between pages are relative, so the site also works from a subfolder
(except the 404 page). Absolute URLs (canonical, hreflang, `og:image`,
sitemap) come from `site_url` (`https://bucky.club`), the one main domain.
The other domains redirect to it: buckyclub.com and bucky.kids forward to
https://bucky.club (GoDaddy), and bucky.pl lands on https://bucky.club/pl/
(the noisy/bucky-pl-redirect Pages site), so Polish visitors stay in Polish.

### iOS beta sign-up

`/<lang>/beta/` collects emails for the private TestFlight beta; the
download page's iPhone note and the landing page's early access box link
to it. The form writes one document, `betaSignups/<SHA-256 of the email>`,
to Firestore in the Bucky Firebase project. The Firestore rules and the
invite workflow live in noisy/Bucky (`firestore.rules`, `docs/beta.md`).

`beta` in `site.json`:

| Key | What |
|---|---|
| `firebase` | Firebase web config. `projectId` is enough for Firestore; `apiKey` and `appId` come from a registered Firebase Web app and are needed for App Check. They are public values, not secrets. An empty `projectId` makes the form say sign-ups open soon |
| `sdk_url` | Firebase JS SDK on the official CDN (`www.gstatic.com/firebasejs/<version>`). It is imported only when the form is sent, so opening the page makes no third-party request |
| `app_check` | `enabled`, `provider` (`recaptcha-enterprise` or `recaptcha-v3`) and `site_key`. Off until the keys exist; turning it on also means mentioning reCAPTCHA in the privacy note |
| `consent_version` | Date of the privacy note, stored with every sign-up. Bump it whenever the note changes |
| `contact_email` | Where deletion requests go (shown on the privacy note) |

Test the form locally against the Firestore emulator (in a Bucky checkout:
`firebase emulators:start --only firestore --project demo-bucky`), with
`projectId` set to `demo-bucky` and `?emulator=127.0.0.1:8080` added to the
page URL on localhost.

### Images and screenshots

Every picture is committed in a few widths (`static/img/<name>-<width>.webp`,
listed in `static/img/manifest.json`). Templates reference it without a
width, `<img src="{{root}}static/img/bank.webp" sizes="...">`, and the build
fills in `src`, `srcset`, `width` and `height`, so phones download small
files. An `<img>` of a generated picture without `sizes` fails the build.

The pictures come from the app repo: `assets/images/`, the character sheets
in `branding/mascot/` (expressions, fill states and Pals are cut out of
them) and the app screenshots rendered by its golden tests (not committed).
To refresh them, in an app checkout:

```sh
flutter test --tags screenshots --update-goldens test/components/screen_screenshots_test.dart
BUCKY_APP_DIR=<app checkout> python3 tools/prepare_images.py   # needs Pillow
```

(`BUCKY_APP_DIR` defaults to the parent folder, which is right when this repo
is the app's `website/` submodule.)

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

- **Contact address.** `beta.contact_email` in `site.json` must be a real,
  read mailbox before the beta form goes live.
- **APK version** in `site.json` is a placeholder (`0.0.0`); bump it with each
  release.
- **Store links.** Google Play and App Store badges once the listings exist
  (today: GitHub prerelease APKs and TestFlight).
- **Legal pages.** A privacy policy page (the content is in
  `docs/privacy.md`) and an imprint / contact page, needed before app
  store listings anyway.
- **Polish copy** would benefit from a native proofread.
- **Vector mascot.** The artwork is raster (see `branding/BRANDING.md`);
  swap in SVG or Lottie when it exists.
