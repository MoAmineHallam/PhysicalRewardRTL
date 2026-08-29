#!/usr/bin/env python3
"""Validate frozen inputs and one or more complete policy result directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from common import (ProtocolError, raw_sha256_file, validate_complete_policy_dir,
                    validate_frozen_inputs)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--frozen-raw-sha256",
                    help="optional out-of-band raw-byte digest printed by freeze_inputs.py")
    ap.add_argument("--policy-dir", action="append", default=[])
    ap.add_argument("--rehash-inputs", action="store_true",
                    help="rehash all model/adapter directories and benchmark files")
    return ap


def run(args: argparse.Namespace) -> None:
    if args.frozen_raw_sha256:
        observed = raw_sha256_file(args.frozen)
        if observed != args.frozen_raw_sha256.lower():
            raise ProtocolError(
                f"out-of-band frozen-input digest mismatch: {observed}")
    frozen = validate_frozen_inputs(args.frozen, rehash_inputs=args.rehash_inputs)
    print(f"PASS frozen_inputs raw_sha256={frozen['self_raw_sha256']} "
          f"benchmark_raw_dir={frozen['benchmark']['raw_dir_sha256']}")
    policies = set()
    for directory in args.policy_dir:
        validated = validate_complete_policy_dir(directory, frozen)
        policy = validated["run_config"]["policy"]
        if policy in policies:
            raise ProtocolError(f"duplicate policy result supplied: {policy}")
        policies.add(policy)
        overall = validated["summary"]["overall"]
        print(f"PASS {policy} dir={Path(directory).resolve()} "
              f"pass@1={overall['pass_at_1']:.6f} "
              f"samples={overall['total_samples']}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        run(parser().parse_args(argv))
    except ProtocolError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
