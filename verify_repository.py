"""Verify the paper files and reproduce the packaged RF-versus-SFT analysis."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="also run both demo RTL modules with Icarus Verilog",
    )
    args = parser.parse_args()

    record = json.loads(
        (ROOT / "checks/submission-validation.json").read_text(encoding="utf-8")
    )
    documents = {
        "main": ROOT / "paper/manuscript.pdf",
        "supplement": ROOT / "paper/supplement.pdf",
    }
    for name, path in documents.items():
        expected = record["documents"][name]["sha256"]
        actual = digest(path)
        if actual != expected:
            raise RuntimeError(f"Changed {name} PDF: {actual} != {expected}")
    print("PASS: manuscript and supplement match the retained validation record.")

    command = [sys.executable, str(ROOT / "artifact/run_demo.py")]
    if args.simulate:
        command.append("--simulate")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise RuntimeError("The packaged reproduction command failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
