#!/usr/bin/env python3
"""Run exactly one frozen SFT/RF policy on the complete VerilogEvalV2 corpus."""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

from common import (POLICIES, ProtocolError, canonical_json_bytes,
                    check_environment, deterministic_policy_outputs,
                    expected_run_config, load_json, load_protocol,
                    prepare_policy_output, problem_seed, raw_directory_sha256,
                    raw_sha256_bytes, raw_sha256_file, strip_completion,
                    validate_frozen_inputs, validate_problem_shard,
                    write_json_atomic_new)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", choices=POLICIES, required=True)
    ap.add_argument("--frozen", required=True,
                    help="frozen_inputs.json created before any generation")
    ap.add_argument("--frozen-raw-sha256", required=True,
                    help="expected raw-byte SHA-256 printed by freeze_inputs.py")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--gpu-index", type=int, required=True,
                    help="physical L40S index; the process exposes only this GPU")
    ap.add_argument("--resume", action="store_true",
                    help="skip only complete, revalidated 20-sample problem shards")
    return ap


def _one_line(text: str, working_dir: str, limit: int = 300) -> str:
    normalized = text.replace(working_dir, "<TMP>")
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    return (lines[0] if lines else "")[:limit]


def judge(rtl: str, reference: Path, testbench: Path,
          protocol: Mapping[str, Any]) -> Tuple[str, str]:
    """Compile and simulate one retained completion; every anomaly is non-pass."""
    oracle = protocol["oracle"]
    try:
        with tempfile.TemporaryDirectory(prefix="verilogeval_rf_judge_") as work:
            candidate = Path(work) / "candidate.sv"
            executable = Path(work) / "simulation.out"
            candidate.write_text(rtl + ("" if rtl.endswith("\n") else "\n"),
                                 encoding="utf-8", newline="\n")
            command = ([oracle["compiler"], *oracle["compiler_arguments"],
                        "-o", str(executable), str(candidate),
                        str(reference), str(testbench)])
            try:
                compiled = subprocess.run(
                    command, capture_output=True, text=True,
                    timeout=int(oracle["compile_timeout_seconds"]), check=False)
            except subprocess.TimeoutExpired:
                return "compile_timeout", ""
            if compiled.returncode != 0:
                return "compile_fail", _one_line(
                    compiled.stderr or compiled.stdout, work)
            try:
                simulated = subprocess.run(
                    [oracle["simulator"], str(executable)], capture_output=True,
                    text=True, timeout=int(oracle["simulation_timeout_seconds"]),
                    check=False)
            except subprocess.TimeoutExpired:
                return "sim_timeout", ""
            log = simulated.stdout + simulated.stderr
            if simulated.returncode != 0:
                detail = _one_line(log, work)
                return "simulator_error", detail or f"vvp return code {simulated.returncode}"
            verdict = re.search(oracle["verdict_regex"], log)
            if verdict is None:
                return "no_verdict", _one_line(log, work)
            mismatches, samples = int(verdict.group(1)), int(verdict.group(2))
            if samples > 0 and mismatches == 0:
                return "PASS", ""
            return "fail", f"{mismatches}/{samples} mismatches"
    except Exception as exc:  # Kept as an explicit failed draw, never dropped.
        return "judge_error", f"{type(exc).__name__}: {exc}"[:300]


def _reset_problem_rng(torch: Any, numpy: Any, seed: int) -> None:
    random.seed(seed)
    numpy.random.seed(seed % (2 ** 32))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def generate_problem(model: Any, tokenizer: Any, torch: Any, numpy: Any,
                     spec: str, problem: str,
                     protocol: Mapping[str, Any]) -> list[str]:
    generation = protocol["generation"]
    seed = problem_seed(int(generation["root_seed"]), problem)
    _reset_problem_rng(torch, numpy, seed)
    chat = tokenizer.apply_chat_template(
        [{"role": "system", "content": generation["system_prompt"]},
         {"role": "user", "content": spec}],
        tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(chat, return_tensors="pt",
                       return_token_type_ids=False).to("cuda:0")
    prompt_length = int(inputs["input_ids"].shape[1])
    n = int(generation["n_samples_per_problem"])
    chunk_size = int(generation["generation_batch_size"])
    completions: list[str] = []
    for start in range(0, n, chunk_size):
        chunk = min(chunk_size, n - start)
        with torch.inference_mode():
            sequences = model.generate(
                **inputs,
                max_new_tokens=int(generation["max_new_tokens"]),
                do_sample=bool(generation["do_sample"]),
                temperature=float(generation["temperature"]),
                top_p=float(generation["top_p"]),
                top_k=int(generation["top_k"]),
                typical_p=float(generation["typical_p"]),
                repetition_penalty=float(generation["repetition_penalty"]),
                num_beams=int(generation["num_beams"]),
                num_return_sequences=chunk,
                stop_strings=list(generation["stop_strings"]),
                tokenizer=tokenizer,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )
        completions.extend(
            tokenizer.decode(sequence[prompt_length:], skip_special_tokens=True)
            for sequence in sequences)
        del sequences
        torch.cuda.empty_cache()
    if len(completions) != n:
        raise ProtocolError(
            f"generator returned {len(completions)} samples for {problem}; expected {n}")
    return completions


def make_shard(problem: str, completions: Sequence[str],
               verdicts: Sequence[Tuple[str, str]],
               run_config: Mapping[str, Any],
               benchmark_problem: Mapping[str, Any]) -> dict:
    if len(completions) != len(verdicts):
        raise ProtocolError(f"{problem}: generation/verdict length mismatch")
    samples = []
    for index, (raw, (status, detail)) in enumerate(zip(completions, verdicts)):
        rtl = strip_completion(raw)
        samples.append({
            "sample_index": index,
            "status": status,
            "detail": detail,
            "raw_completion": raw,
            "raw_completion_raw_sha256": raw_sha256_bytes(raw.encode("utf-8")),
            "rtl": rtl,
            "rtl_raw_sha256": raw_sha256_bytes(rtl.encode("utf-8")),
        })
    status_counts = Counter(row["status"] for row in samples)
    generation = run_config["generation"]
    shard = {
        "schema": "verilogeval_rf_problem_shard/1",
        "policy": run_config["policy"],
        "training_seed": run_config["training_seed"],
        "problem": problem,
        "problem_seed": problem_seed(int(generation["root_seed"]), problem),
        "n_samples": generation["n_samples_per_problem"],
        "prompt_raw_sha256": benchmark_problem["prompt"]["raw_sha256"],
        "reference_raw_sha256": benchmark_problem["reference"]["raw_sha256"],
        "testbench_raw_sha256": benchmark_problem["testbench"]["raw_sha256"],
        "run_config_canonical_raw_sha256": raw_sha256_bytes(canonical_json_bytes(run_config)),
        "status_counts": dict(sorted(status_counts.items())),
        "samples": samples,
    }
    validate_problem_shard(shard, run_config, benchmark_problem)
    return shard


def finalize(output: Path, run_config: Mapping[str, Any],
             frozen: Mapping[str, Any]) -> None:
    final = output / "final"
    if final.exists():
        raise ProtocolError(f"final result already exists: {final}")
    jsonl, summary = deterministic_policy_outputs(output, run_config, frozen)
    staging = Path(tempfile.mkdtemp(
        prefix=f".{output.name}.final-partial-", dir=str(output.parent)))
    try:
        (staging / "samples.jsonl").write_bytes(jsonl)
        (staging / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        complete = {
            "schema": "verilogeval_rf_policy_complete/1",
            "policy": run_config["policy"],
            "training_seed": run_config["training_seed"],
            "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "run_config_raw_sha256": raw_sha256_file(output / "run_config.json"),
            "samples_raw_sha256": raw_sha256_file(staging / "samples.jsonl"),
            "summary_raw_sha256": raw_sha256_file(staging / "summary.json"),
            "problem_shards_raw_dir_sha256": raw_directory_sha256(output / "problems"),
        }
        (staging / "COMPLETE.json").write_text(
            json.dumps(complete, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        if final.exists():
            raise ProtocolError(f"final result appeared during publication: {final}")
        os.replace(staging, final)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def run(args: argparse.Namespace) -> None:
    if args.gpu_index < 0:
        raise ProtocolError("GPU index must be nonnegative")
    observed_frozen_hash = raw_sha256_file(args.frozen)
    if observed_frozen_hash != args.frozen_raw_sha256.lower():
        raise ProtocolError(
            f"frozen manifest CLI hash mismatch: {observed_frozen_hash} != "
            f"{args.frozen_raw_sha256.lower()}")

    # Must happen before importing torch.  All other required environment
    # variables must have been exported before Python startup and are verified.
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu_index)
    protocol = load_protocol()
    frozen = validate_frozen_inputs(args.frozen, rehash_inputs=True)
    environment = check_environment(protocol, require_gpu=True)
    output = Path(args.out_dir).resolve()
    run_config = expected_run_config(
        args.policy, args.frozen, frozen, output, args.gpu_index, environment)
    completed = prepare_policy_output(output, run_config, resume=args.resume)

    expected_problems = set(frozen["benchmark"]["problems"])
    unknown = completed - expected_problems
    if unknown:
        raise ProtocolError(f"resume contains unknown problem shards: {sorted(unknown)}")
    for problem in sorted(completed):
        shard = load_json(output / "problems" / f"{problem}.json")
        if shard.get("problem") != problem:
            raise ProtocolError(f"resume shard filename/content mismatch: {problem}")
        validate_problem_shard(
            shard, run_config, frozen["benchmark"]["problems"][problem])

    remaining = sorted(expected_problems - completed)
    print(f"policy={args.policy} validated={len(completed)} remaining={len(remaining)} "
          f"gpu={args.gpu_index}", flush=True)
    if not remaining:
        finalize(output, run_config, frozen)
        print(f"finalized validated shards -> {output / 'final'}", flush=True)
        return

    import numpy
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # Top-p sampling in the frozen torch 2.4.1 stack calls a CUDA cumulative
    # sum without a deterministic implementation. V2 failed before its first
    # sample on the strict setting. Keep deterministic algorithms requested,
    # but retain the runtime warning instead of aborting that declared kernel.
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_float32_matmul_precision("highest")

    base_path = frozen["artifacts"]["base"]["path"]
    adapter_path = frozen["artifacts"][args.policy]["path"]
    tokenizer = AutoTokenizer.from_pretrained(
        base_path, local_files_only=True, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        base_path, torch_dtype=torch.float16, device_map={"": 0},
        local_files_only=True, trust_remote_code=False)
    model = PeftModel.from_pretrained(
        base, adapter_path, is_trainable=False, local_files_only=True).eval()
    if next(model.parameters()).device.type != "cuda":
        raise ProtocolError("model did not load on the isolated CUDA device")

    dataset = Path(frozen["benchmark"]["dataset_dir"])
    total = len(expected_problems)
    for ordinal, problem in enumerate(sorted(expected_problems), start=1):
        if problem in completed:
            continue
        record = frozen["benchmark"]["problems"][problem]
        prompt_path = dataset / record["prompt"]["relative_path"]
        reference = dataset / record["reference"]["relative_path"]
        testbench = dataset / record["testbench"]["relative_path"]
        # Recheck just-in-time in addition to the whole-corpus preflight hash.
        for path, role in ((prompt_path, "prompt"), (reference, "reference"),
                           (testbench, "testbench")):
            if raw_sha256_file(path) != record[role]["raw_sha256"]:
                raise ProtocolError(f"{problem}: {role} changed after preflight")
        spec = prompt_path.read_text(encoding="utf-8")
        started = time.monotonic()
        completions = generate_problem(
            model, tokenizer, torch, numpy, spec, problem, protocol)
        rtls = [strip_completion(raw) for raw in completions]
        workers = min(8, len(rtls))
        with futures.ThreadPoolExecutor(max_workers=workers) as pool:
            verdicts = list(pool.map(
                lambda rtl: judge(rtl, reference, testbench, protocol), rtls))
        shard = make_shard(problem, completions, verdicts, run_config, record)
        shard_path = output / "problems" / f"{problem}.json"
        # Stage beside the policy directory, then atomically move the complete
        # shard in. A hard-kill can leave a non-authoritative sibling temporary,
        # never a partial artifact inside the resumable policy directory.
        write_json_atomic_new(shard_path, shard, staging_parent=output.parent)
        elapsed = time.monotonic() - started
        passed = shard["status_counts"].get("PASS", 0)
        print(f"[{ordinal}/{total}] {problem}: PASS={passed}/"
              f"{protocol['generation']['n_samples_per_problem']} "
              f"elapsed={elapsed:.1f}s", flush=True)

    finalize(output, run_config, frozen)
    print(f"completed policy={args.policy} -> {output / 'final'}", flush=True)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        run(parser().parse_args(argv))
    except ProtocolError as exc:
        print(f"policy-run error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
