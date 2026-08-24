#!/usr/bin/env python3
"""
freeze_hashes.py  -  compute a fail-closed sealed-study identity block.

Revision 1 pinned 16-character prefixes of the scripts only. That is enough to
notice an accidental edit and not enough to identify the actual experiment: the
model, the adapter, the reward artifact and the labelled rows were unpinned, and
those are precisely the objects a reader cannot reconstruct from the repository.

HASH BASIS, stated exactly so a reader can reproduce it:

  text files (.py, .tcl, .json, .jsonl, .md)
      SHA-256 of the file content with CRLF newlines normalised to LF. NOT the
      git blob hash: a git blob prepends `blob <bytelen>\\0` before hashing, so
      its digest differs. Normalisation is what makes the digest identical on the
      Windows laptop and the Linux server; without it every file checked out on
      the laptop appears modified.

  binary files (.pt, .joblib, .bit, model weights)
      SHA-256 of the raw bytes, no normalisation.

  directories (base model, LoRA adapters)
      a MANIFEST digest: for every file under the directory, sorted by relative
      POSIX path, feed `<relpath>\\0<filehash>\\n` into one SHA-256. This is
      order-independent of the filesystem and changes if any file is added,
      removed or modified.

    python freeze_hashes.py --out hashes.json
    python freeze_hashes.py --verify hashes.json     # exits non-zero on drift
"""

import os
import sys
import json
import hashlib
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))

TEXT_EXT = {".py", ".tcl", ".json", ".jsonl", ".md", ".txt", ".sv", ".v",
            ".bib", ".sh", ".ps1"}

# Everything whose identity the experiment depends on. Missing entries are
# reported as null rather than skipped, so an unpinned object is visible.
SCRIPTS = [
    "freeze_hashes.py", "canonicalize.py", "check_a_orderability.py", "oracle.py", "grpo_oracle.py",
    "gen_accelerator_catalog.py", "gen_sft_corpus.py", "surrogate_train.py",
    "train_rf_struct.py", "gen_sealed_split.py", "analyze_sealed.py",
    "analyze_sealed_v3.py", "eval_sealed.py", "materialize_rf_candidates.py",
    "verify_sealed_training.py", "verify_sealed_ppa.py", "test_sealed_workflow.py",
    "audit_training_ceiling_failure.py",
    "gen_fmax_candidates.py", "eval_holdout.py", "run_ppa.py",
    "ppa_synth.tcl", "run_arm.sh", "run_sealed_server_stage.sh",
    "run_sealed_laptop_ppa.ps1", "run_sealed_analysis.sh",
    "audit_rf_reward_eligible.py", "run_sealed_server_stage_study2.sh",
    "run_sealed_laptop_ppa_study2.ps1", "run_sealed_handoff_study2.ps1",
    "run_sealed_analysis_study2.sh",
    "reward_invariance_audit.py", "probe_competence.py", "build_dataset.py",
]
DATA = ["sealed_split.json", "rf_rows.json", "preregistration.json",
        "preregistration_study2.json",
        "failed_training_runs/rev5_corr_ceiling4500.json"]
BINARIES = ["surrogate_v3.pt", "rf_struct.joblib"]
DIRS = ["sft_v6c_out"]          # + --model and --adapters from the command line


def sha256_text(path):
    raw = open(path, "rb").read()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def sha256_bytes(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_path(path):
    ext = os.path.splitext(path)[1].lower()
    return sha256_text(path) if ext in TEXT_EXT else sha256_bytes(path)


def sha256_dir(root):
    """Manifest digest over every file under `root`, path-sorted."""
    entries = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            entries.append((rel, sha256_path(p)))
    h = hashlib.sha256()
    for rel, dg in sorted(entries):
        h.update(rel.encode() + b"\0" + dg.encode() + b"\n")
    return h.hexdigest(), len(entries)


def collect(model=None, adapters=(), progress=True):
    """Progress is printed as each entry is computed, not at the end.

    The base model is ~13 GB on network storage, so a silent run looks hung for
    minutes and invites a Ctrl-C. Nothing here is slow by mistake -- hashing the
    weights is the point -- but the user should be able to see it working.
    """
    out = {}

    def note(label, extra=""):
        if progress:
            print(f"  hashing {label}{extra}", flush=True)

    for rel in SCRIPTS + DATA + BINARIES:
        p = os.path.join(HERE, rel)
        if os.path.exists(p):
            sz = os.path.getsize(p)
            note(rel, f"  ({sz/1e6:.1f} MB)" if sz > 5e6 else "")
            out[rel] = sha256_path(p)
        else:
            out[rel] = None
    for rel in list(DIRS) + list(adapters):
        p = rel if os.path.isabs(rel) else os.path.join(HERE, rel)
        if os.path.isdir(p):
            note(rel + "/", "  (directory manifest)")
            dg, n = sha256_dir(p)
            out[rel] = dg
            out[rel + "::n_files"] = n
        else:
            out[rel] = None
    if model:
        if os.path.isdir(model):
            note("BASE MODEL " + model,
                 "  (~13 GB, this is the slow one -- do NOT interrupt)")
            dg, n = sha256_dir(model)
            out["BASE_MODEL:" + model] = dg
            out["BASE_MODEL:" + model + "::n_files"] = n
        else:
            out["BASE_MODEL:" + model] = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "hashes.json"))
    ap.add_argument("--verify", default="")
    ap.add_argument("--model", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapters", nargs="*", default=["sft_v6c_out"])
    args = ap.parse_args()

    got = collect(args.model, args.adapters)
    print()
    basis = ("SHA-256; text files (%s) LF-normalised content, binaries raw "
             "bytes, directories = path-sorted manifest digest. NOT git blob "
             "hashes (a git blob prepends 'blob <len>\\0')."
             % " ".join(sorted(TEXT_EXT)))

    if args.verify:
        ref = json.load(open(args.verify))
        old = ref.get("hashes", ref)
        bad, miss, unpinned = [], [], []
        for k, v in got.items():
            if k.endswith("::n_files"):
                continue
            if v is None:
                miss.append(k)
            elif k not in old:
                unpinned.append(k)
            elif old[k] != v:
                bad.append(k)
        for k in old:
            if k.endswith("::n_files"):
                continue
            if k not in got and k not in miss:
                miss.append(k)
        for k in bad:
            print(f"  CHANGED  {k}\n      was {old[k]}\n      now {got[k]}")
        for k in miss:
            print(f"  MISSING  {k}")
        for k in unpinned:
            print(f"  UNPINNED {k}\n      now {got[k]}")
        print(f"\n{len(old)} pinned, {len(bad)} changed, {len(miss)} missing, "
              f"{len(unpinned)} required-but-unpinned")
        if bad or miss or unpinned:
            print("\nThe preregistered artifacts do not match this checkout. "
                  "Either restore them or record an amendment -- do not proceed "
                  "quietly.")
            sys.exit(1)
        print("all pinned artifacts match")
        return

    n_null = sum(1 for k, v in got.items()
                 if v is None and not k.endswith("::n_files"))
    json.dump({"hash_basis": basis, "hashes": got},
              open(args.out, "w"), indent=1)
    for k in sorted(got):
        if k.endswith("::n_files"):
            continue
        print(f"  {k:44s} {got[k] or 'MISSING'}")
    print(f"\nwrote {args.out}  ({n_null} unresolved)")
    if n_null:
        print("Entries reading MISSING are not yet pinned. Anything still "
              "missing when an arm starts training is an unpinned dependency of "
              "the experiment.")


if __name__ == "__main__":
    main()
