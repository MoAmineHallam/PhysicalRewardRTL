#!/usr/bin/env python3
"""Freeze all real inputs before any repaired-RF VerilogEval generation."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from common import (DEFAULT_PROTOCOL, ProtocolError, check_environment,
                    directory_hash_manifest, load_protocol, package_raw_hashes,
                    raw_sha256_file, verify_benchmark_checkout,
                    write_json_exclusive)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    ap.add_argument("--base", required=True)
    ap.add_argument("--sft-adapter", required=True)
    ap.add_argument("--rf-s1-adapter", required=True)
    ap.add_argument("--rf-s2-adapter", required=True)
    ap.add_argument("--benchmark-repo", required=True)
    ap.add_argument("--out", required=True,
                    help="new frozen_inputs.json path; an existing path is rejected")
    return ap


def run(args: argparse.Namespace) -> Path:
    protocol_path = Path(args.protocol).resolve()
    if protocol_path != DEFAULT_PROTOCOL.resolve():
        raise ProtocolError(
            f"only the package protocol may be frozen: {DEFAULT_PROTOCOL.resolve()}")
    protocol = load_protocol(protocol_path)
    output = Path(args.out).resolve()
    if output.exists():
        raise ProtocolError(f"frozen-input output already exists: {output}")

    # This is deliberately checked before expensive model hashing.  Preparation
    # may run without a visible GPU, but it must use the exact study packages and
    # Icarus stack.  Policy jobs add the exact GPU/driver checks.
    environment = check_environment(protocol, require_gpu=False)
    paths = {
        "base": Path(args.base).resolve(),
        "sft": Path(args.sft_adapter).resolve(),
        "rf_s1": Path(args.rf_s1_adapter).resolve(),
        "rf_s2": Path(args.rf_s2_adapter).resolve(),
    }
    artifacts = {}
    for name, path in paths.items():
        if not path.is_dir():
            raise ProtocolError(f"artifact directory is missing for {name}: {path}")
        observed_manifest = directory_hash_manifest(path)
        observed_raw = observed_manifest["raw_dir_sha256"]
        observed_legacy = observed_manifest["legacy_study2_dir_sha256"]
        expected_legacy = protocol["artifacts"][name]["legacy_study2_dir_sha256"]
        if observed_legacy != expected_legacy:
            raise ProtocolError(
                f"legacy Study 2 artifact identity mismatch for {name}: "
                f"expected {expected_legacy}, observed {observed_legacy}")
        artifacts[name] = {
            "path": str(path),
            "legacy_study2_dir_sha256": observed_legacy,
            "raw_dir_sha256": observed_raw,
            "raw_file_manifest": observed_manifest["raw_file_manifest"],
            "label": protocol["artifacts"][name]["label"],
        }

    benchmark = verify_benchmark_checkout(args.benchmark_repo, protocol)
    expected_files = int(protocol["benchmark"]["expected_dataset_files"])
    if benchmark["file_count"] != expected_files:
        raise ProtocolError(
            f"benchmark must contain exactly {expected_files} files, "
            f"observed {benchmark['file_count']}")

    manifest = {
        "schema": "verilogeval_rf_frozen_inputs/2",
        "protocol_id": protocol["protocol_id"],
        "protocol_path": str(protocol_path),
        "protocol_raw_sha256": raw_sha256_file(protocol_path),
        "frozen_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "freeze_rule": (
            "This manifest was created before policy generation. Every policy "
            "must rehash all artifact directories and the complete benchmark corpus."
        ),
        "package_raw_sha256": package_raw_hashes(),
        "environment_at_freeze": environment,
        "artifacts": artifacts,
        "benchmark": benchmark,
    }
    write_json_exclusive(output, manifest)
    print(f"frozen inputs: {output}")
    print(f"frozen_inputs_raw_sha256={raw_sha256_file(output)}")
    print(f"benchmark_raw_dir_sha256={benchmark['raw_dir_sha256']}")
    for name in ("base", "sft", "rf_s1", "rf_s2"):
        print(f"{name}_legacy_study2_dir_sha256="
              f"{artifacts[name]['legacy_study2_dir_sha256']}")
        print(f"{name}_raw_dir_sha256={artifacts[name]['raw_dir_sha256']}")
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        run(parser().parse_args(argv))
    except ProtocolError as exc:
        print(f"freeze error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
