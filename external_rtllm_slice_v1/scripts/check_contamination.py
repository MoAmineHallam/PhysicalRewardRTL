#!/usr/bin/env python3
"""Audit exact local fine-tuning contamination without reading evaluation outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import (
    all_text_values,
    load_json,
    normalize_prompt,
    normalize_verilog,
    sha256_bytes,
    sha256_file,
    verify_upstream_identity,
    write_json,
)


PROMPT_KEYS = {"prompt", "spec", "instruction", "design_prompt", "description"}
RTL_KEYS = {"completion", "rtl", "code", "response"}
NAME_KEYS = {"design", "design_name", "task", "task_name", "name"}


def fingerprint_text(text: str) -> tuple[str, str]:
    raw = sha256_bytes(text.encode("utf-8"))
    normalized = sha256_bytes(normalize_prompt(text).encode("utf-8"))
    return raw, normalized


def corpus_from_jsonl(path: Path, repo_root: Path, corpus: dict[str, dict[str, list[str]]]) -> None:
    rel = path.relative_to(repo_root).as_posix()
    with path.open("r", encoding="utf-8", errors="strict") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value: Any = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL {rel}:{line_number}: {exc}") from exc
            for key, text in all_text_values(value):
                key_lower = key.lower()
                source = f"{rel}:{line_number}:{key}"
                if key_lower in NAME_KEYS:
                    corpus["names"].setdefault(text.strip().lower(), []).append(source)
                if key_lower in PROMPT_KEYS:
                    raw, normalized = fingerprint_text(text)
                    corpus["prompt_raw"].setdefault(raw, []).append(source)
                    corpus["prompt_normalized"].setdefault(normalized, []).append(source)
                if key_lower in RTL_KEYS or "module " in text:
                    normalized_rtl = sha256_bytes(normalize_verilog(text).encode("utf-8"))
                    corpus["rtl_normalized"].setdefault(normalized_rtl, []).append(source)


def build_corpus(repo_root: Path, sources: dict) -> tuple[dict, list[dict]]:
    corpus: dict[str, dict[str, list[str]]] = {
        "names": {},
        "prompt_raw": {},
        "prompt_normalized": {},
        "rtl_normalized": {},
    }
    paths: set[Path] = set()
    for rel in sources["repo_relative_jsonl"]:
        path = repo_root / rel
        if not path.is_file():
            raise ValueError(f"declared contamination source is missing: {rel}")
        paths.add(path)
        corpus_from_jsonl(path, repo_root, corpus)
    for pattern in sources["repo_relative_globs"]:
        matches = sorted(repo_root.glob(pattern))
        if not matches:
            raise ValueError(f"declared contamination glob matched no files: {pattern}")
        for path in matches:
            if not path.is_file():
                continue
            paths.add(path)
            rel = path.relative_to(repo_root).as_posix()
            text = path.read_text(encoding="utf-8", errors="strict")
            task_name = path.parent.name.lower()
            corpus["names"].setdefault(task_name, []).append(f"{rel}:directory")
            if path.name == "spec.txt":
                raw, normalized = fingerprint_text(text)
                corpus["prompt_raw"].setdefault(raw, []).append(rel)
                corpus["prompt_normalized"].setdefault(normalized, []).append(rel)
            elif path.suffix.lower() in {".v", ".sv"}:
                normalized_rtl = sha256_bytes(normalize_verilog(text).encode("utf-8"))
                corpus["rtl_normalized"].setdefault(normalized_rtl, []).append(rel)
    file_manifest = [
        {
            "path": path.relative_to(repo_root).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(paths, key=lambda p: p.relative_to(repo_root).as_posix())
    ]
    return corpus, file_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    repo_root = args.repo_root.resolve()
    upstream = args.upstream.resolve()
    pin = load_json(package_root / "upstream_pin.json")
    identity = verify_upstream_identity(upstream, pin)
    audit = load_json(args.audit or package_root / "audit_manifest.json")
    sources = load_json(package_root / "contamination_sources.json")
    corpus, source_files = build_corpus(repo_root, sources)
    task_reports = []
    for task in audit["tasks"]:
        description = (upstream / task["description"]["path"]).read_text(encoding="utf-8")
        reference = (upstream / task["reference"]["path"]).read_text(encoding="utf-8")
        prompt_raw, prompt_normalized = fingerprint_text(description)
        rtl_normalized = sha256_bytes(normalize_verilog(reference).encode("utf-8"))
        hits = {
            "task_name": corpus["names"].get(task["expected_module"].lower(), []),
            "prompt_raw": corpus["prompt_raw"].get(prompt_raw, []),
            "prompt_normalized": corpus["prompt_normalized"].get(prompt_normalized, []),
            "reference_rtl_normalized": corpus["rtl_normalized"].get(rtl_normalized, []),
        }
        clean = not any(hits.values())
        task_reports.append({"task_id": task["task_id"], "clean": clean, "hits": hits})
    report = {
        "schema_version": 1,
        "status": "PASS",
        "scope": sources["scope_note"],
        "upstream": identity,
        "source_file_count": len(source_files),
        "source_files": source_files,
        "task_count": len(task_reports),
        "clean_task_count": sum(task["clean"] for task in task_reports),
        "contaminated_task_count": sum(not task["clean"] for task in task_reports),
        "tasks": task_reports,
        "unresolved_limitation": "The provenance of the base model's public pretraining corpus is unavailable; exact public-pretraining exposure to RTLLM cannot be excluded.",
    }
    output = args.output or package_root / "contamination_report.json"
    write_json(output, report)
    print(
        f"PASS contamination audit tasks={report['task_count']} clean={report['clean_task_count']} "
        f"contaminated={report['contaminated_task_count']} sources={len(source_files)} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
