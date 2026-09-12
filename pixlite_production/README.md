# PixLite Production

This is PixLite's canonical, git-tracked production source, seeded from
`PixLite_Android_v13_StableMLKitSource.zip` (the last shipped source) and
updated per the "fast launch + home ads + stable tools" production pass.

**Structural change from earlier versions:** previous production iterations
lived only as opaque zip snapshots at the repo root
(`PixLite_Android_v13_*.zip` etc.), which can't be diffed or reviewed file
by file. Going forward, production work happens directly in this directory
as real, reviewable files. The historical zips are left untouched for
reference.

Build via `.github/workflows/build-pixlite-production.yml` (path-filtered
to this folder) — builds straight from source, no unzip step.

## Scope of this pass

- Fast startup: ads/scanner/OCR are never initialized before the home
  screen is visible; `MobileAds.instance.initialize()` and every
  `BannerAd` load happen on `addPostFrameCallback`, after the first frame.
- Home screen ads: top banner, one large inline banner after Quick Tools,
  and a banner anchored above the bottom nav bar (Home tab only) — using
  Google's public test ad unit IDs.
- Scanner: unchanged Google ML Kit implementation (already audited clean
  in `scanner_audit/` — PixLite doesn't touch ML Kit's output). Copy toned
  down from "Professional Document Scanner" to plain "Document Scanner."
- New tool: Merge (multiple images -> one PDF), using only existing
  dependencies.
- Performance: `CompressScreen`, `ResizeScreen`, and `MergeScreen`'s
  decode/resize/encode/PDF-assembly work now runs via `compute()` on a
  separate isolate, off the UI thread.
- Not in this pass (deliberately deferred, not stubbed into the UI):
  Split, PDF-to-images, OCR/Word, Sign — each needs a new PDF-rendering
  dependency that wasn't worth the added startup/build risk for this
  focused pass. `scanner_quality_proof/`, `scanner_geometry_proof/`, and
  `scanner_natural_proof/` remain isolated experiments and are not part of
  this build.
