"""
Downloads the official DocRes checkpoints from the verified Hugging Face
re-hosts (the official host, Microsoft OneDrive, is not reachable from every
environment) and verifies each file's SHA256 against a known-good hash before
it is used for anything.
"""
import hashlib
import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

BENCH_DIR = Path(__file__).resolve().parent

TARGETS = [
    {
        "repo_id": "DaVinciCode/doctra-docres-main",
        "filename": "docres.pkl",
        "dest": BENCH_DIR / "weights" / "DocRes" / "docres.pkl",
        "sha256": "1d6a89d754fe1e58ffd1865eab0ef3f03344798d39197b2d9a77ce4fbc8c02fd",
    },
    {
        "repo_id": "DaVinciCode/doctra-docres-mbd",
        "filename": "mbd.pkl",
        "dest": BENCH_DIR / "weights" / "MBD" / "mbd.pkl",
        "sha256": "7c2dc15a6b0e613adf7c3a794891f44caef544b92c5898ac610ae689e9cd9085",
    },
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for target in TARGETS:
        target["dest"].parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {target['filename']} from {target['repo_id']} ...")
        local_path = hf_hub_download(repo_id=target["repo_id"], filename=target["filename"])
        shutil.copy(local_path, target["dest"])

        actual = sha256_of(target["dest"])
        expected = target["sha256"]
        print(f"  expected sha256: {expected}")
        print(f"  actual   sha256: {actual}")
        if actual != expected:
            print(f"SHA256 MISMATCH for {target['filename']} -- refusing to proceed.", file=sys.stderr)
            sys.exit(1)
        print(f"  OK: {target['dest']} verified.")


if __name__ == "__main__":
    main()
