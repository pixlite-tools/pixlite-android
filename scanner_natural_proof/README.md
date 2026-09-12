# PixLite Scanner Natural Proof

Final, focused quality proof: standalone native Android app (separate from
PixLite, `scanner_quality_proof/`, and `scanner_geometry_proof/`) that turns
the existing "Natural" scan result into a genuinely clean document scan
while preserving all original information -- no new scanner engine, no new
SDK, no Document/B&W modes, no enhancement knobs exposed beyond one final
result.

## Flow

1. `MainActivity` — CameraX capture at max-quality still-capture resolution
   -> `original.jpg`.
2. `CornerCorrectionActivity` — ONNX DocQuadNet-256 detection (reused from
   `scanner_geometry_proof/`) on a downscaled preview, manual 4-corner
   drag-to-adjust, confirm.
3. `ProcessingActivity` (all on `Dispatchers.Default`, off the UI thread):
   - Expands the confirmed quad ~2% outward around its centroid as a safety
     margin against clipping text/stamps at the paper edge.
   - Perspective-warps the **original-resolution** image
     (`ScanProcessor.fourPointTransform`).
   - Runs the ONE "Final Natural" enhancement pipeline
     (`ScanProcessor.toFinalNatural`) on that full-resolution crop.
   - Saves `final_natural.jpg`.
4. `ResultActivity` — two buttons only, **ORIGINAL** / **FINAL NATURAL**,
   pinch-zoom, share, and a stats panel: original dimensions, final
   dimensions, crop/detection time, enhancement time, total processing time.

## Final Natural pipeline (`ScanProcessor.toFinalNatural`)

1. **Gray-world white balance** on BGR — corrects color cast before
   anything else.
2. **LAB conversion** — all tonal work below happens on the L (lightness)
   channel only; A/B (color) channels are left untouched, which is what
   keeps blue/red stamp ink and colored signatures from shifting or fading.
3. **Illumination normalization** on L: divide out a large-kernel blurred
   background estimate. The kernel is proportional to image size and
   deliberately large so it captures only the shadow gradient, not
   individual glyph strokes -- a kernel that's too tight "learns" the text
   as background and washes it out, which is what broke the old
   Document/B&W modes.
4. **CLAHE** on the normalized L, conservative clip limit, for local
   text/paper contrast without amplifying noise.
5. **Mild unsharp mask** on L only (low amount) — no color halos, no
   thickened/broken thin Arabic strokes.
6. Merge back with the original A/B, convert to BGR.
7. **Mild bilateral denoise** as the last step, small enough to leave fine
   character strokes and diacritics intact.

No global thresholding anywhere in this path.
