"""Merges the per-task _fragment_*.json files (written by inference_cpu.py,
one per isolated process/step) into a single output/report.json."""
import glob
import json
import sys
from pathlib import Path

out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")

report = {"tasks": {}}
for frag_path in sorted(glob.glob(str(out_dir / "_fragment_*.json"))):
    with open(frag_path) as f:
        report["tasks"].update(json.load(f))

if "original" in report["tasks"]:
    report["input"] = report["tasks"]["original"]["output_dims"]

with open(out_dir / "report.json", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
