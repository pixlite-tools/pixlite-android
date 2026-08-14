# PixLite Scanner Geometry Proof

Standalone native Android app (separate from PixLite and from
`scanner_quality_proof/`) built to answer one question: **does
MakeACopy-style ONNX document-boundary detection give noticeably better
geometry/cropping than PixLite's previous classical OpenCV edge detector
(`scanner_quality_proof/.../BoundaryDetector.kt`)?**

No enhancement/filter pipeline, no OCR, no PDF/Word export, no ads, no home
UI. See `THIRD_PARTY_NOTICES.md` for the ONNX model's license.

## Flow

1. `MainActivity` — CameraX capture at max-quality still-capture resolution
   -> `original.jpg`.
2. `CornerCorrectionActivity` — runs the ONNX DocQuadNet-256 detector
   (`DocQuadOnnxDetector.kt`) on a downscaled preview, draws the detected
   quad -> saves `auto_detected.jpg`, lets the user drag the 4 corners, then
   on confirm saves `manual_corrected.jpg`.
3. `ProcessingActivity` — perspective-warps the **original-resolution**
   image using the confirmed corners (`ScanProcessor.fourPointTransform`,
   OpenCV) -> saves `perspective_result.jpg`. No other processing.
4. `ResultActivity` — flip between all 4 saved images, pinch-zoom, see
   per-stage timings and dimensions, share any of them.

All 4 files land in
`Android/data/com.pixlite.geometryproof/files/PixLiteGeometryProof/<timestamp>/`
on the device.

## Detector

`DocQuadOnnxDetector.kt` is a minimal port of MakeACopy's DocQuadNet-256
pipeline: letterbox to 256x256 (mid-gray pad), NCHW float32 [0,1] input,
ONNX Runtime inference, ARGMAX per corner-heatmap channel -> 64-space ->
256-space -> inverse-letterbox to the input bitmap's coordinate space. Only
the "M6a" minimal/deterministic baseline from MakeACopy's own
`DocQuadPostprocessor` javadoc is used — the production mask-fallback and
multi-guardrail scoring system was intentionally left out for this proof.
