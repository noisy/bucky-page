# Downloads

Every Bucky release attaches its APK to a release of this repository with
the same tag, under a versioned name, e.g. `v0.2.0-build.373` with
`bucky-0.2.0-373.apk`. `site.json` points the Download button at that exact
file (`apk.path`) and shows its version (`apk.version`). The Bucky release
workflow does both (`scripts/ci/publish_website_apk.sh` in noisy/Bucky).

By hand:

    gh release create v<version>-build.<N> bucky-<version>-<N>.apk --title "Bucky <version> (<N>)"

then set `apk.path` to
`https://github.com/noisy/bucky-page/releases/download/v<version>-build.<N>/bucky-<version>-<N>.apk`
and `apk.version` to `<version> (<N>)`. APK files are gitignored, so they
never land in the repository.
