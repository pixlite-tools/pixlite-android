# DocRes Quality Benchmark

Standalone, offline quality benchmark for the official [DocRes](https://github.com/ZZZHANG-jx/DocRes) model
(`ZZZHANG-jx/DocRes`, MIT license), run independently of the PixLite Android app.
This folder does not build, depend on, or get referenced by the Flutter app or
`scanner_quality_proof/`.

## Status

Blocked on inputs, not yet run. See the full status report (PDF) delivered in
chat for details. Summary:

- **License verified**: MIT, commercial-use compatible. No separate/restrictive
  license found for the model weights.
- **Environment set up**: official repo vendored under `repo/` (stripped of its
  own `.git` history and example images to keep this tree small -- see below),
  CPU-only PyTorch + deps installed.
- **Blocked**: the official weights (`mbd.pkl`, `docres.pkl`) are hosted only on
  Microsoft OneDrive, which this environment's network policy blocks. A known
  Hugging Face mirror of the same official checkpoints (`DaVinciCode/doctra-docres-main`,
  `DaVinciCode/doctra-docres-mbd`) is blocked too.
- **Needed to proceed**: (1) the real test document image, (2) the two weight
  files, downloaded externally and provided here.

## Layout

```
docres_quality_benchmark/
├── repo/          official DocRes source (vendored, .git/example-images stripped)
├── weights/
│   ├── MBD/       -> mbd.pkl goes here (gitignored, not committed)
│   └── DocRes/    -> docres.pkl goes here (gitignored, not committed)
├── input/         the real test document image goes here
└── output/        original.png / deshadowing.png / appearance.png /
                   deblurring.png / binarization.png / end2end.png
```

## Known required patches (not yet applied -- documented for transparency)

`repo/inference.py` casts the model and inputs to FP16 (`.half()`) for the
deshadowing, appearance, deblurring, and binarization tasks -- CUDA-only,
will fail on CPU. `repo/data/MBD/infer.py` hardcodes `.cuda()` in the
dewarping helper used by the `end2end` task. Both will be patched to run in
FP32 on CPU once weights are available; this changes precision/device only,
not the model architecture or weights.
