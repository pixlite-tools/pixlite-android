# PixLite Scanner Audit (diagnostics-only build)

Standalone Flutter app used solely to forensically audit PixLite v13's
Google ML Kit document-scanner flow. It is **not** a product build, does
**not** replace or modify ML Kit, and does **not** change any image.

It runs the exact same `DocumentScannerOptions` PixLite v13's `ScanScreen`
uses (`SCANNER_MODE_FULL`, JPEG+PDF formats, `pageLimit: 10`,
`isGalleryImport: true`), then for every page image and the PDF:

- records width x height, file size, MIME (via magic bytes), and whether a
  JPEG EXIF (APP1) segment is present
- computes a SHA256 of the raw bytes ML Kit returned
- copies the exact same bytes, unmodified, into 4 named checkpoint folders
  (`mlkit_raw`, `pixlite_after_import`, `pixlite_after_processing`,
  `pixlite_display_source`) and hashes each copy independently, so the
  checkpoints can be verified byte-identical rather than assumed identical
- times the `scanDocument()` call itself

All of this is bundled into a single `audit_report.json` plus a `.zip` of
every checkpoint file, shareable in one tap from the app.

See the top-level forensic audit report for how these diagnostics map to
the 15-point checklist and the static source-level findings.
