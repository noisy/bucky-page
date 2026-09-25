# Downloads

The download page links to the APK attached to the latest GitHub release of
this repository, as `bucky-latest.apk` (the URL and version are in
`../site.json`). To ship a new build, attach it to a new release:

    gh release create v0.1.0-build.N bucky-latest.apk --title "Bucky 0.1.0 (N)"

and bump `apk.version` in `site.json`. To host the file on Pages instead, put
it here and set `apk.path` back to `downloads/bucky-latest.apk`. APK files
are gitignored, so they never land in the repository.
