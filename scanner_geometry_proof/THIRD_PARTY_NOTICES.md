# Third-party notices

## DocQuadNet-256 ONNX model and detector logic

`app/src/main/assets/docquad/docquadnet256_trained_opset17.ort` and the
post-processing logic in `DocQuadOnnxDetector.kt` are adapted from
**MakeACopy** (https://github.com/egdels/makeacopy), Copyright 2025
Christian Kierdorf.

MakeACopy — including its LICENSE file and its README's "Training data &
models" section — states that the whole repository, **including the
exported ONNX inference model**, is licensed under the **Apache License,
Version 2.0**:

> The exported ONNX inference model is an independently created work and is
> licensed under the Apache License 2.0, consistent with the rest of this
> project.

Only the exported `.ort` model file and the minimal ARGMAX corner-decoding
logic were reused here (adapted from MakeACopy's `DocQuadOrtRunner`,
`DocQuadLetterbox`, `DocQuadPostprocessor.argmaxCorners64ToCorners256`, and
`DocQuadDetector`). MakeACopy's production mask-fallback/guardrail scoring
system, its enhancement/filter pipeline, and its OCR/PDF/export features
were not reused.

A full copy of the Apache License 2.0 is available at
<https://www.apache.org/licenses/LICENSE-2.0>.

## ONNX Runtime

`com.microsoft.onnxruntime:onnxruntime-android` — MIT License.
<https://github.com/microsoft/onnxruntime>

## OpenCV

`org.opencv:opencv` — Apache License 2.0.
<https://opencv.org>
