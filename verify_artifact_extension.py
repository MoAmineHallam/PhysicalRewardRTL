#!/usr/bin/env python3
"""Fail closed unless the artifact-only extension is reproducible and current."""

from analyze_artifact_extension import main


if __name__ == "__main__":
    raise SystemExit(main(["--check"]))
