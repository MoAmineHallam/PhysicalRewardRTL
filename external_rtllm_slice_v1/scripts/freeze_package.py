#!/usr/bin/env python3
"""Hash every protocol/code/input artifact after the package is finalized."""

from __future__ import annotations

from pathlib import Path

from common import canonical_json_bytes, sha256_bytes, sha256_file, write_json


EXCLUDED = {"package_manifest.json", "package_manifest.sha256"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name in EXCLUDED or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    manifest = {
        "schema_version": 1,
        "status": "FROZEN",
        "scope": "all package protocol, code, audit, selected prompt, and oracle files except this self-hash",
        "file_count": len(files),
        "files": files,
    }
    manifest_path = root / "package_manifest.json"
    write_json(manifest_path, manifest)
    digest = sha256_bytes(canonical_json_bytes(manifest))
    (root / "package_manifest.sha256").write_text(digest + "\n", encoding="ascii")
    print(f"PASS package_manifest_sha256={digest} files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
