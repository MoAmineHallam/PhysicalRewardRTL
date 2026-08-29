#!/usr/bin/env python3
"""Pure protocol, hashing, state, and validation helpers.

This module intentionally imports no ML package.  Unit tests and provenance
validation can therefore run without allocating a GPU or loading a model.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


HERE = Path(__file__).resolve().parent
DEFAULT_PROTOCOL = HERE / "protocol.json"
LEGACY_STUDY2_TEXT_EXTENSIONS = {
    ".py", ".json", ".jsonl", ".md", ".sv", ".v", ".tcl", ".txt",
    ".sh",
}
PACKAGE_FILES = (
    ".gitignore",
    "README.md",
    "protocol.json",
    "requirements.lock.txt",
    "common.py",
    "freeze_inputs.py",
    "run_policy.py",
    "aggregate.py",
    "validate.py",
    "launch_three.sh",
    "tests/test_protocol.py",
)
POLICIES = ("sft", "rf_s1", "rf_s2")
STATUS_VALUES = {
    "PASS", "fail", "compile_fail", "compile_timeout", "sim_timeout",
    "simulator_error", "no_verdict", "judge_error",
}


class ProtocolError(RuntimeError):
    """The frozen evaluation contract is absent, inconsistent, or violated."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def raw_sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_hash_pair(path: os.PathLike[str] | str) -> Tuple[str, str]:
    """Return (raw-byte SHA-256, legacy Study 2 SHA-256) in one streaming pass.

    The legacy identity normalized CRLF for text-like files. It is retained only
    to match already recorded model/adapter digests. New evidence always uses
    the first, raw-byte digest.
    """
    target = Path(path)
    raw_digest = hashlib.sha256()
    legacy_digest = hashlib.sha256()
    normalize_legacy = target.suffix.lower() in LEGACY_STUDY2_TEXT_EXTENSIONS
    pending = b""
    try:
        before = target.stat()
        with target.open("rb") as handle:
            while True:
                chunk = handle.read(8 * 1024 * 1024)
                if not chunk:
                    break
                raw_digest.update(chunk)
                if not normalize_legacy:
                    continue
                combined = pending + chunk
                if combined.endswith(b"\r"):
                    combined, pending = combined[:-1], b"\r"
                else:
                    pending = b""
                legacy_digest.update(combined.replace(b"\r\n", b"\n"))
        after = target.stat()
    except OSError as exc:
        raise ProtocolError(f"cannot hash {target}: {exc}") from exc
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ProtocolError(f"file changed while it was being hashed: {target}")
    if not normalize_legacy:
        return raw_digest.hexdigest(), raw_digest.hexdigest()
    legacy_digest.update(pending)
    return raw_digest.hexdigest(), legacy_digest.hexdigest()


def raw_sha256_file(path: os.PathLike[str] | str) -> str:
    return _file_hash_pair(path)[0]


def legacy_study2_file_sha256(path: os.PathLike[str] | str) -> str:
    return _file_hash_pair(path)[1]


def directory_hash_manifest(path: os.PathLike[str] | str) -> dict:
    """Return per-file raw evidence plus raw and legacy directory digests."""
    root = Path(path)
    if not root.is_dir():
        raise ProtocolError(f"directory is missing: {root}")
    entries = []
    for candidate in root.rglob("*"):
        if candidate.is_file():
            rel = candidate.relative_to(root).as_posix()
            raw_hash, legacy_hash = _file_hash_pair(candidate)
            entries.append((rel, candidate.stat().st_size, raw_hash, legacy_hash))
    raw_digest = hashlib.sha256()
    legacy_digest = hashlib.sha256()
    for rel, _size, raw_hash, legacy_hash in sorted(entries):
        prefix = rel.encode("utf-8") + b"\0"
        raw_digest.update(prefix + raw_hash.encode("ascii") + b"\n")
        legacy_digest.update(prefix + legacy_hash.encode("ascii") + b"\n")
    return {
        "raw_dir_sha256": raw_digest.hexdigest(),
        "legacy_study2_dir_sha256": legacy_digest.hexdigest(),
        "raw_file_manifest": [
            {"relative_path": rel, "bytes": size, "raw_sha256": raw_hash}
            for rel, size, raw_hash, _legacy_hash in sorted(entries)
        ],
    }


def directory_hash_pair(path: os.PathLike[str] | str) -> Tuple[str, str]:
    manifest = directory_hash_manifest(path)
    return (manifest["raw_dir_sha256"],
            manifest["legacy_study2_dir_sha256"])


def raw_directory_sha256(path: os.PathLike[str] | str) -> str:
    return directory_hash_pair(path)[0]


def legacy_study2_dir_sha256(path: os.PathLike[str] | str) -> str:
    return directory_hash_pair(path)[1]


def raw_directory_digest_from_file_manifest(rows: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    seen = set()
    for row in sorted(rows, key=lambda item: str(item.get("relative_path", ""))):
        relative = row.get("relative_path")
        file_hash = row.get("raw_sha256")
        size = row.get("bytes")
        if (not isinstance(relative, str) or not relative or relative in seen or
                not isinstance(file_hash, str) or
                not re.fullmatch(r"[0-9a-f]{64}", file_hash) or
                not isinstance(size, int) or size < 0):
            raise ProtocolError("invalid or duplicate raw per-file directory manifest row")
        seen.add(relative)
        digest.update(relative.encode("utf-8") + b"\0" +
                      file_hash.encode("ascii") + b"\n")
    return digest.hexdigest()


def load_json(path: os.PathLike[str] | str) -> Any:
    target = Path(path)
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProtocolError(f"cannot read JSON {target}: {exc}") from exc


def write_json_exclusive(path: os.PathLike[str] | str, value: Any) -> None:
    """Create a JSON artifact once; never replace an accepted artifact."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True,
                                    ensure_ascii=False).encode("utf-8"))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ProtocolError(f"refusing to overwrite existing artifact: {target}") from exc


def write_json_atomic_new(path: os.PathLike[str] | str, value: Any, *,
                          staging_parent: Optional[os.PathLike[str] | str] = None) -> None:
    """Publish a complete new JSON artifact with an atomic same-filesystem move."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ProtocolError(f"refusing to replace existing artifact: {target}")
    staging = Path(staging_parent) if staging_parent is not None else target.parent
    staging.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.partial-", dir=str(staging))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True,
                                    ensure_ascii=False).encode("utf-8"))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        if target.exists():
            raise ProtocolError(f"artifact appeared during publication: {target}")
        os.replace(temporary, target)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise


def write_bytes_atomic_new(path: os.PathLike[str] | str, raw: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ProtocolError(f"refusing to replace existing artifact: {target}")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.partial-", dir=str(target.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if target.exists():
            raise ProtocolError(f"artifact appeared during publication: {target}")
        os.replace(temporary, target)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise


def load_protocol(path: os.PathLike[str] | str = DEFAULT_PROTOCOL) -> dict:
    protocol = load_json(path)
    if protocol.get("schema") != "verilogeval_rf_extension_protocol/3":
        raise ProtocolError(f"unexpected protocol schema: {protocol.get('schema')!r}")
    if tuple(protocol.get("artifacts", {}).keys()) != ("base", "sft", "rf_s1", "rf_s2"):
        raise ProtocolError("protocol artifact order/content is not base,sft,rf_s1,rf_s2")
    for name, artifact in protocol["artifacts"].items():
        legacy_hash = artifact.get("legacy_study2_dir_sha256")
        if not isinstance(legacy_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", legacy_hash):
            raise ProtocolError(f"protocol lacks a valid legacy Study 2 identity for {name}")
    generation = protocol.get("generation", {})
    if generation.get("n_samples_per_problem") != 20:
        raise ProtocolError("protocol must retain exactly 20 samples/problem")
    if generation.get("generation_batch_size") != 5:
        raise ProtocolError("protocol generation chunking is not the frozen size 5")
    if generation.get("unsupported_deterministic_cuda_ops") != "warn_only":
        raise ProtocolError("unsupported deterministic CUDA operation policy changed")
    if protocol.get("benchmark", {}).get("expected_problems") != 156:
        raise ProtocolError("protocol benchmark size is not the frozen 156")
    auxiliaries = protocol.get("benchmark", {}).get("tracked_auxiliary_files")
    if not isinstance(auxiliaries, list) or len(auxiliaries) != 3:
        raise ProtocolError("protocol must pin exactly three tracked auxiliary files")
    expected_auxiliary = {
        "Prob062_bugs_mux2.sv":
            "020ebc5c365a0c3c23ff64ab2506e84bd2ce9a5046f8090c310fd6c104a525d2",
        "problems-temp.txt":
            "1deeb03bcff897c4042a00877f61f4b92f5c3c9a5a5c1e323470dd5c97d75e3a",
        "problems.txt":
            "301e28ce3c9653a664b4fda2358202eafdaf0f1f8104e08f7a48085a80e6cf06",
    }
    if {row.get("relative_path"): row.get("raw_sha256")
            for row in auxiliaries if isinstance(row, dict)} != expected_auxiliary:
        raise ProtocolError("protocol auxiliary-file identities changed")
    if protocol["benchmark"].get("expected_dataset_files") != 471:
        raise ProtocolError("protocol dataset file count is not 471")
    return protocol


def package_raw_hashes() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for relative in PACKAGE_FILES:
        target = HERE / relative
        if not target.is_file():
            raise ProtocolError(f"evaluation package file is missing: {relative}")
        result[relative] = raw_sha256_file(target)
    return result


def _run(command: Sequence[str], *, cwd: Optional[Path] = None,
         timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(list(command), cwd=str(cwd) if cwd else None,
                              capture_output=True, text=True, timeout=timeout,
                              check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProtocolError(f"command failed ({' '.join(command)}): {exc}") from exc


def _version_major(text: str, label: str) -> int:
    patterns = (
        rf"{re.escape(label)}[^0-9]*(\d+)(?:\.\d+)?",
        r"version[^0-9]*(\d+)(?:\.\d+)?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    raise ProtocolError(f"cannot parse {label} version from: {text[:300]!r}")


def check_environment(protocol: Mapping[str, Any], *, require_gpu: bool) -> dict:
    """Fail unless the execution stack equals the frozen Study 2 stack."""
    expected = protocol["environment"]
    actual_python = platform.python_version()
    if actual_python != expected["python"]:
        raise ProtocolError(
            f"Python mismatch: expected {expected['python']}, observed {actual_python}")

    for key, wanted in expected["required_environment"].items():
        observed = os.environ.get(key)
        if observed != wanted:
            raise ProtocolError(
                f"environment mismatch for {key}: expected {wanted!r}, observed {observed!r}")

    versions: Dict[str, str] = {}
    for package, wanted in expected["packages"].items():
        try:
            observed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ProtocolError(f"required package is missing: {package}") from exc
        versions[package] = observed
        if observed != wanted:
            raise ProtocolError(
                f"package mismatch for {package}: expected {wanted}, observed {observed}")

    iv = _run(["iverilog", "-V"])
    iv_text = (iv.stdout + "\n" + iv.stderr).strip()
    if iv.returncode != 0 or _version_major(iv_text, "Icarus Verilog") != int(expected["iverilog_major"]):
        raise ProtocolError(f"iverilog is not frozen major {expected['iverilog_major']}")
    vp = _run(["vvp", "-V"])
    vp_text = (vp.stdout + "\n" + vp.stderr).strip()
    if vp.returncode != 0 or _version_major(vp_text, "Icarus Verilog") != int(expected["vvp_major"]):
        raise ProtocolError(f"vvp is not frozen major {expected['vvp_major']}")

    snapshot: Dict[str, Any] = {
        "python": actual_python,
        "packages": versions,
        "iverilog_version_text": iv_text.splitlines()[0] if iv_text else "",
        "vvp_version_text": vp_text.splitlines()[0] if vp_text else "",
        "required_environment": dict(expected["required_environment"]),
    }
    if not require_gpu:
        return snapshot

    import torch  # Delayed until the caller has isolated CUDA_VISIBLE_DEVICES.

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ProtocolError(
            "a policy job must see exactly one CUDA device after CUDA_VISIBLE_DEVICES isolation")
    if str(torch.version.cuda) != expected["torch_cuda"]:
        raise ProtocolError(
            f"PyTorch CUDA mismatch: expected {expected['torch_cuda']}, observed {torch.version.cuda}")
    gpu_name = torch.cuda.get_device_name(0)
    capability = list(torch.cuda.get_device_capability(0))
    if gpu_name != expected["gpu_name"]:
        raise ProtocolError(
            f"GPU mismatch: expected {expected['gpu_name']!r}, observed {gpu_name!r}")
    if capability != expected["gpu_compute_capability"]:
        raise ProtocolError(
            f"compute capability mismatch: expected {expected['gpu_compute_capability']}, observed {capability}")

    physical = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if not re.fullmatch(r"\d+", physical):
        raise ProtocolError(
            "CUDA_VISIBLE_DEVICES must contain one explicit physical numeric index")
    smi = _run(["nvidia-smi", "-i", physical,
                "--query-gpu=uuid,name,driver_version", "--format=csv,noheader"])
    fields = [part.strip() for part in smi.stdout.strip().split(",")]
    if (smi.returncode != 0 or len(fields) != 3 or
            fields[1] != expected["gpu_name"] or
            fields[2] != expected["nvidia_driver"]):
        raise ProtocolError(
            "physical GPU provenance mismatch: expected "
            f"{expected['gpu_name']} / driver {expected['nvidia_driver']}, "
            f"observed {fields}")
    snapshot.update({
        "torch_cuda": str(torch.version.cuda),
        "visible_gpu_count": torch.cuda.device_count(),
        "gpu_name": gpu_name,
        "gpu_compute_capability": capability,
        "nvidia_driver": fields[2],
        "gpu_uuid": fields[0],
        "cuda_visible_devices": physical,
    })
    return snapshot


def problem_seed(root_seed: int, problem: str) -> int:
    raw = hashlib.sha256(f"{int(root_seed)}\0{problem}".encode("utf-8")).digest()
    return int.from_bytes(raw[:8], "big") & ((1 << 63) - 1)


def pass_at_k(n: int, c: int, k: int) -> float:
    if not (n > 0 and 0 <= c <= n and 1 <= k <= n):
        raise ProtocolError(f"invalid pass@k arguments n={n}, c={c}, k={k}")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def strip_completion(raw: str) -> str:
    ticks = chr(96) * 3
    rtl = raw.replace(ticks + "verilog", "").replace(ticks, "")
    match = re.search(r"\bmodule\s+\w+\s*[(#;]", rtl)
    if match:
        rtl = rtl[match.start():]
    rtl = rtl.strip()
    end = rtl.find("endmodule")
    if end >= 0:
        rtl = rtl[:end + len("endmodule")]
    return rtl


def build_dataset_inventory(dataset_dir: os.PathLike[str] | str,
                            expected_problems: int,
                            tracked_auxiliary_files: Sequence[Mapping[str, Any]]) -> dict:
    dataset = Path(dataset_dir).resolve()
    if not dataset.is_dir():
        raise ProtocolError(f"benchmark dataset directory is missing: {dataset}")
    all_entries = list(dataset.iterdir())
    if any(entry.is_dir() for entry in all_entries):
        raise ProtocolError("benchmark dataset directory contains a subdirectory")
    if any(entry.is_symlink() for entry in all_entries):
        raise ProtocolError("benchmark dataset may not contain symlinks")
    files = [entry for entry in all_entries if entry.is_file()]
    prompts: Dict[str, Path] = {}
    for path in files:
        match = re.fullmatch(r"(.+)_prompt\.txt", path.name)
        if match:
            prompts[match.group(1)] = path
    if len(prompts) != expected_problems:
        raise ProtocolError(
            f"benchmark must contain {expected_problems} prompt files, observed {len(prompts)}")

    expected_names = set()
    problems: Dict[str, dict] = {}
    for problem in sorted(prompts):
        role_paths = {
            "prompt": dataset / f"{problem}_prompt.txt",
            "reference": dataset / f"{problem}_ref.sv",
            "testbench": dataset / f"{problem}_test.sv",
        }
        for role, path in role_paths.items():
            expected_names.add(path.name)
            if not path.is_file() or path.is_symlink():
                raise ProtocolError(f"{problem} lacks a regular {role} file: {path.name}")
            if path.stat().st_size == 0:
                raise ProtocolError(f"benchmark file is empty: {path.name}")
        try:
            role_paths["prompt"].read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProtocolError(f"prompt is not readable UTF-8: {role_paths['prompt']}") from exc
        problems[problem] = {
            role: {
                "relative_path": path.name,
                "raw_sha256": raw_sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for role, path in role_paths.items()
        }
    auxiliary_by_name = {
        str(row["relative_path"]): str(row["raw_sha256"])
        for row in tracked_auxiliary_files
    }
    auxiliary_records = []
    for name, expected_hash in sorted(auxiliary_by_name.items()):
        path = dataset / name
        if not path.is_file() or path.is_symlink():
            raise ProtocolError(f"tracked benchmark auxiliary is missing: {name}")
        actual_hash = raw_sha256_file(path)
        if actual_hash != expected_hash:
            raise ProtocolError(
                f"tracked benchmark auxiliary changed: {name}: {actual_hash}")
        auxiliary_records.append({"relative_path": name,
                                  "raw_sha256": actual_hash,
                                  "bytes": path.stat().st_size})
    expected_names.update(auxiliary_by_name)
    observed_names = {path.name for path in files}
    if observed_names != expected_names:
        extra = sorted(observed_names - expected_names)
        missing = sorted(expected_names - observed_names)
        raise ProtocolError(
            f"benchmark closed file set mismatch; extra={extra[:5]}, missing={missing[:5]}")
    return {
        "dataset_dir": str(dataset),
        "problem_count": len(problems),
        "file_count": len(files),
        "raw_dir_sha256": raw_directory_sha256(dataset),
        "problems": problems,
        "auxiliary_files": auxiliary_records,
    }


def verify_benchmark_checkout(repo_dir: os.PathLike[str] | str,
                              protocol: Mapping[str, Any]) -> dict:
    repo = Path(repo_dir).resolve()
    if not repo.is_dir():
        raise ProtocolError(f"benchmark repository is missing: {repo}")
    revision = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    head = revision.stdout.strip()
    wanted = protocol["benchmark"]["commit"]
    if revision.returncode != 0 or head != wanted:
        raise ProtocolError(f"benchmark commit mismatch: expected {wanted}, observed {head!r}")
    subdir = protocol["benchmark"]["dataset_subdir"]
    status = _run(["git", "status", "--porcelain", "--untracked-files=all", "--", subdir],
                  cwd=repo)
    if status.returncode != 0 or status.stdout.strip():
        raise ProtocolError(
            "benchmark dataset checkout is modified, staged, or contains untracked files: "
            + status.stdout.strip()[:500])
    inventory = build_dataset_inventory(
        repo / subdir, int(protocol["benchmark"]["expected_problems"]),
        protocol["benchmark"]["tracked_auxiliary_files"])
    inventory.update({
        "repository_dir": str(repo),
        "repository_url": protocol["benchmark"]["repository"],
        "git_commit": head,
        "dataset_subdir": subdir,
    })
    return inventory


def verify_dataset_against_inventory(inventory: Mapping[str, Any]) -> None:
    observed = build_dataset_inventory(
        inventory["dataset_dir"], int(inventory["problem_count"]),
        inventory["auxiliary_files"])
    for field in ("problem_count", "file_count", "raw_dir_sha256", "problems",
                  "auxiliary_files"):
        if observed[field] != inventory[field]:
            raise ProtocolError(f"frozen benchmark content changed: field {field}")


def verify_package_raw_hashes(expected: Mapping[str, str]) -> None:
    observed = package_raw_hashes()
    if observed != dict(expected):
        changed = sorted(set(observed) | set(expected))
        changed = [name for name in changed if observed.get(name) != expected.get(name)]
        raise ProtocolError(f"evaluation package changed after input freeze: {changed}")


def validate_frozen_inputs(path: os.PathLike[str] | str, *,
                           rehash_inputs: bool) -> dict:
    manifest = load_json(path)
    if manifest.get("schema") != "verilogeval_rf_frozen_inputs/3":
        raise ProtocolError(f"unexpected frozen-input schema: {manifest.get('schema')!r}")
    protocol = load_protocol(DEFAULT_PROTOCOL)
    if manifest.get("protocol_raw_sha256") != raw_sha256_file(DEFAULT_PROTOCOL):
        raise ProtocolError("frozen-input manifest does not bind the current protocol")
    if manifest.get("protocol_id") != protocol["protocol_id"]:
        raise ProtocolError("frozen-input protocol_id mismatch")
    verify_package_raw_hashes(manifest.get("package_raw_sha256", {}))
    identities = manifest.get("artifacts", {})
    if set(identities) != {"base", *POLICIES}:
        raise ProtocolError("frozen-input artifact set is incomplete")
    for name in ("base", *POLICIES):
        expected_hash = protocol["artifacts"][name]["legacy_study2_dir_sha256"]
        record = identities[name]
        if record.get("legacy_study2_dir_sha256") != expected_hash:
            raise ProtocolError(f"frozen-input identity mismatch for {name}")
        raw_expected = record.get("raw_dir_sha256")
        if not isinstance(raw_expected, str) or not re.fullmatch(r"[0-9a-f]{64}", raw_expected):
            raise ProtocolError(f"frozen-input raw directory identity is missing for {name}")
        raw_file_manifest = record.get("raw_file_manifest")
        if (not isinstance(raw_file_manifest, list) or
                raw_directory_digest_from_file_manifest(raw_file_manifest) != raw_expected):
            raise ProtocolError(f"raw per-file artifact manifest is inconsistent for {name}")
        if rehash_inputs:
            observed_manifest = directory_hash_manifest(record.get("path", ""))
            observed_raw = observed_manifest["raw_dir_sha256"]
            observed_legacy = observed_manifest["legacy_study2_dir_sha256"]
            if observed_legacy != expected_hash:
                raise ProtocolError(
                    f"legacy Study 2 artifact identity changed for {name}: "
                    f"{observed_legacy} != {expected_hash}")
            if observed_raw != raw_expected:
                raise ProtocolError(
                    f"raw-byte artifact identity changed for {name}: "
                    f"{observed_raw} != {raw_expected}")
            if observed_manifest["raw_file_manifest"] != record.get("raw_file_manifest"):
                raise ProtocolError(f"raw per-file artifact manifest changed for {name}")
    benchmark = manifest.get("benchmark", {})
    if benchmark.get("git_commit") != protocol["benchmark"]["commit"]:
        raise ProtocolError("frozen benchmark revision mismatch")
    if benchmark.get("problem_count") != protocol["benchmark"]["expected_problems"]:
        raise ProtocolError("frozen benchmark problem count mismatch")
    problems = benchmark.get("problems")
    if not isinstance(problems, dict) or len(problems) != benchmark.get("problem_count"):
        raise ProtocolError("frozen benchmark problem manifest is incomplete")
    benchmark_files = []
    for problem in problems.values():
        for role in ("prompt", "reference", "testbench"):
            benchmark_files.append(problem.get(role, {}))
    auxiliary_files = benchmark.get("auxiliary_files")
    if not isinstance(auxiliary_files, list) or len(auxiliary_files) != 3:
        raise ProtocolError("frozen benchmark auxiliary manifest is incomplete")
    benchmark_files.extend(auxiliary_files)
    if raw_directory_digest_from_file_manifest(benchmark_files) != benchmark.get("raw_dir_sha256"):
        raise ProtocolError("frozen benchmark raw per-file manifest is inconsistent")
    if rehash_inputs:
        verify_dataset_against_inventory(benchmark)
    # Runtime-only binding used by result validators; it is not serialized
    # inside the manifest and therefore cannot become a self-referential hash.
    manifest["self_raw_sha256"] = raw_sha256_file(path)
    manifest["self_path"] = str(Path(path).resolve())
    return manifest


def expected_run_config(policy: str, frozen_path: os.PathLike[str] | str,
                        frozen: Mapping[str, Any], output_dir: os.PathLike[str] | str,
                        physical_gpu: int, environment: Mapping[str, Any]) -> dict:
    if policy not in POLICIES:
        raise ProtocolError(f"unknown policy: {policy}")
    protocol = load_protocol(DEFAULT_PROTOCOL)
    return {
        "schema": "verilogeval_rf_policy_run/1",
        "protocol_id": protocol["protocol_id"],
        "protocol_raw_sha256": raw_sha256_file(DEFAULT_PROTOCOL),
        "frozen_inputs_path": str(Path(frozen_path).resolve()),
        "frozen_inputs_raw_sha256": raw_sha256_file(frozen_path),
        "package_raw_sha256": dict(frozen["package_raw_sha256"]),
        "policy": policy,
        "training_seed": int(protocol["artifacts"][policy]["training_seed"]),
        "base_legacy_study2_dir_sha256": frozen["artifacts"]["base"]["legacy_study2_dir_sha256"],
        "base_raw_dir_sha256": frozen["artifacts"]["base"]["raw_dir_sha256"],
        "adapter_legacy_study2_dir_sha256": frozen["artifacts"][policy]["legacy_study2_dir_sha256"],
        "adapter_raw_dir_sha256": frozen["artifacts"][policy]["raw_dir_sha256"],
        "benchmark_raw_dir_sha256": frozen["benchmark"]["raw_dir_sha256"],
        "benchmark_git_commit": frozen["benchmark"]["git_commit"],
        "generation": dict(protocol["generation"]),
        "oracle": dict(protocol["oracle"]),
        "output_dir": str(Path(output_dir).resolve()),
        "physical_gpu_index": int(physical_gpu),
        "environment": dict(environment),
    }


def prepare_policy_output(output_dir: os.PathLike[str] | str,
                          run_config: Mapping[str, Any], *, resume: bool) -> set[str]:
    """Create a fresh result directory or validate a resumable one.

    Returns the set of already complete problem identifiers.  No row-oriented
    output is ever opened for append.
    """
    output = Path(output_dir)
    problems_dir = output / "problems"
    if not resume:
        if output.exists():
            raise ProtocolError(f"fresh policy output must not exist: {output}")
        output.mkdir(parents=True)
        problems_dir.mkdir()
        write_json_exclusive(output / "run_config.json", dict(run_config))
        return set()

    if not output.is_dir():
        raise ProtocolError(f"resume output directory is missing: {output}")
    if (output / "final").exists():
        raise ProtocolError("completed policy output cannot be resumed or overwritten")
    allowed = {"run_config.json", "problems"}
    observed = {entry.name for entry in output.iterdir()}
    if observed != allowed:
        raise ProtocolError(
            f"resume output has an unrecognized or partial top-level file: {sorted(observed - allowed)}")
    if not problems_dir.is_dir() or problems_dir.is_symlink():
        raise ProtocolError("resume problems path is not a regular directory")
    if load_json(output / "run_config.json") != dict(run_config):
        raise ProtocolError("resume run configuration differs from the frozen invocation")
    completed = set()
    for entry in problems_dir.iterdir():
        if entry.is_symlink() or not entry.is_file() or not re.fullmatch(r".+\.json", entry.name):
            raise ProtocolError(f"unrecognized or partial problem artifact: {entry.name}")
        completed.add(entry.stem)
    return completed


def validate_problem_shard(shard: Mapping[str, Any], run_config: Mapping[str, Any],
                           benchmark_problem: Mapping[str, Any]) -> None:
    generation = run_config["generation"]
    problem = shard.get("problem")
    expected_seed = problem_seed(int(generation["root_seed"]), str(problem))
    if shard.get("schema") != "verilogeval_rf_problem_shard/1":
        raise ProtocolError(f"{problem}: invalid shard schema")
    exact = {
        "policy": run_config["policy"],
        "training_seed": run_config["training_seed"],
        "problem_seed": expected_seed,
        "n_samples": generation["n_samples_per_problem"],
        "prompt_raw_sha256": benchmark_problem["prompt"]["raw_sha256"],
        "reference_raw_sha256": benchmark_problem["reference"]["raw_sha256"],
        "testbench_raw_sha256": benchmark_problem["testbench"]["raw_sha256"],
        "run_config_canonical_raw_sha256": raw_sha256_bytes(canonical_json_bytes(run_config)),
    }
    for key, wanted in exact.items():
        if shard.get(key) != wanted:
            raise ProtocolError(
                f"{problem}: shard field {key} mismatch ({shard.get(key)!r} != {wanted!r})")
    samples = shard.get("samples")
    n = int(generation["n_samples_per_problem"])
    if not isinstance(samples, list) or len(samples) != n:
        raise ProtocolError(f"{problem}: shard must retain exactly {n} samples")
    if [row.get("sample_index") for row in samples] != list(range(n)):
        raise ProtocolError(f"{problem}: sample indices are missing, duplicated, or reordered")
    for row in samples:
        status = row.get("status")
        if status not in STATUS_VALUES:
            raise ProtocolError(f"{problem}: invalid sample status {status!r}")
        raw = row.get("raw_completion")
        rtl = row.get("rtl")
        if not isinstance(raw, str) or not isinstance(rtl, str):
            raise ProtocolError(f"{problem}: raw_completion and rtl must be strings")
        if row.get("raw_completion_raw_sha256") != raw_sha256_bytes(raw.encode("utf-8")):
            raise ProtocolError(f"{problem}: raw completion hash mismatch")
        if row.get("rtl_raw_sha256") != raw_sha256_bytes(rtl.encode("utf-8")):
            raise ProtocolError(f"{problem}: extracted RTL hash mismatch")
    statuses = Counter(row["status"] for row in samples)
    if shard.get("status_counts") != dict(sorted(statuses.items())):
        raise ProtocolError(f"{problem}: status-count accounting mismatch")


def problem_statistics(shard: Mapping[str, Any]) -> dict:
    statuses = [row["status"] for row in shard["samples"]]
    n = len(statuses)
    correct = statuses.count("PASS")
    compile_and_verdict = sum(value in {"PASS", "fail"} for value in statuses)
    return {
        "n": n,
        "correct": correct,
        "compile_and_verdict": compile_and_verdict,
        "compile_and_verdict_rate": compile_and_verdict / n,
        "pass_at_1": pass_at_k(n, correct, 1),
        "pass_at_5": pass_at_k(n, correct, 5),
        "pass_at_10": pass_at_k(n, correct, 10),
        "pass_at_20": pass_at_k(n, correct, 20),
        "status_counts": dict(sorted(Counter(statuses).items())),
    }


def deterministic_policy_outputs(output_dir: os.PathLike[str] | str,
                                 run_config: Mapping[str, Any],
                                 frozen: Mapping[str, Any]) -> Tuple[bytes, dict]:
    output = Path(output_dir)
    problem_ids = sorted(frozen["benchmark"]["problems"])
    jsonl_rows = []
    by_problem: Dict[str, dict] = {}
    total_status = Counter()
    for problem in problem_ids:
        path = output / "problems" / f"{problem}.json"
        if not path.is_file():
            raise ProtocolError(f"policy output is missing problem shard: {problem}")
        shard = load_json(path)
        if shard.get("problem") != problem:
            raise ProtocolError(f"problem filename/content mismatch for {problem}")
        validate_problem_shard(shard, run_config,
                               frozen["benchmark"]["problems"][problem])
        stats = problem_statistics(shard)
        by_problem[problem] = stats
        total_status.update(stats["status_counts"])
        for row in shard["samples"]:
            jsonl_rows.append(canonical_json_bytes({
                "policy": run_config["policy"],
                "training_seed": run_config["training_seed"],
                "problem": problem,
                **row,
            }))
    metrics = ("compile_and_verdict_rate", "pass_at_1", "pass_at_5",
               "pass_at_10", "pass_at_20")
    overall = {
        metric: sum(row[metric] for row in by_problem.values()) / len(by_problem)
        for metric in metrics
    }
    overall.update({
        "problem_count": len(by_problem),
        "n_samples_per_problem": run_config["generation"]["n_samples_per_problem"],
        "total_samples": len(jsonl_rows),
        "status_counts": dict(sorted(total_status.items())),
    })
    summary = {
        "schema": "verilogeval_rf_policy_summary/1",
        "policy": run_config["policy"],
        "training_seed": run_config["training_seed"],
        "primary_metric": "pass_at_1",
        "overall": overall,
        "by_problem": by_problem,
    }
    return b"".join(jsonl_rows), summary


def validate_complete_policy_dir(output_dir: os.PathLike[str] | str,
                                 frozen: Mapping[str, Any]) -> dict:
    output = Path(output_dir).resolve()
    if not output.is_dir():
        raise ProtocolError(f"policy output directory is missing: {output}")
    allowed = {"run_config.json", "problems", "final"}
    observed = {entry.name for entry in output.iterdir()}
    if observed != allowed:
        raise ProtocolError(
            f"complete output closed file set mismatch: {sorted(observed ^ allowed)}")
    config = load_json(output / "run_config.json")
    if config.get("output_dir") != str(output):
        raise ProtocolError("policy output path differs from its run configuration")
    if config.get("frozen_inputs_raw_sha256") != frozen.get("self_raw_sha256"):
        raise ProtocolError("policy output did not use this frozen-input manifest")
    if config.get("package_raw_sha256") != frozen.get("package_raw_sha256"):
        raise ProtocolError("policy run package hashes differ from frozen inputs")
    expected_config = expected_run_config(
        str(config.get("policy")), frozen["self_path"], frozen, output,
        int(config.get("physical_gpu_index", -1)), config.get("environment", {}))
    if config != expected_config:
        raise ProtocolError("policy run configuration is not the frozen deterministic configuration")
    final = output / "final"
    if (not final.is_dir() or final.is_symlink() or
            {entry.name for entry in final.iterdir()} !=
            {"samples.jsonl", "summary.json", "COMPLETE.json"}):
        raise ProtocolError("final directory closed file set mismatch")
    jsonl_expected, summary_expected = deterministic_policy_outputs(output, config, frozen)
    if (final / "samples.jsonl").read_bytes() != jsonl_expected:
        raise ProtocolError("samples.jsonl is not the deterministic projection of shards")
    if load_json(final / "summary.json") != summary_expected:
        raise ProtocolError("summary.json is not the deterministic projection of shards")
    complete = load_json(final / "COMPLETE.json")
    exact = {
        "schema": "verilogeval_rf_policy_complete/1",
        "policy": config["policy"],
        "training_seed": config["training_seed"],
        "run_config_raw_sha256": raw_sha256_file(output / "run_config.json"),
        "samples_raw_sha256": raw_sha256_file(final / "samples.jsonl"),
        "summary_raw_sha256": raw_sha256_file(final / "summary.json"),
        "problem_shards_raw_dir_sha256": raw_directory_sha256(output / "problems"),
    }
    for key, wanted in exact.items():
        if complete.get(key) != wanted:
            raise ProtocolError(f"COMPLETE field mismatch: {key}")
    return {"run_config": config, "summary": summary_expected, "complete": complete}
