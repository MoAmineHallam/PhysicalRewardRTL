# Phase 0 status — physical-quality scaling plan

Running record of the Phase 0 checklist in the
[plan](PHYSICAL_SCALING_PLAN_20261003.md#13-immediate-next-steps-phase-0-checklist).
Newest entries last.  No access details (addresses, ports, credentials) are
recorded here.

## 2026-10-03 — server inventory (step 1)

Same result on V100a and V100b (they share the filesystem):

| Item | Value | Consequence |
|---|---|---|
| CPU | 104 logical cores, Intel Xeon Gold 6230R, per box | Enough for tens of parallel EDA jobs per box beside the GPU jobs; the EDA-throughput risk is mainly an installation question now |
| RAM | 251 GB per box (V100b had about 62 GB in use at the check) | Vivado and OpenROAD jobs for these small designs fit many at a time; measure peak memory per job in step 5 |
| Shared disk | BeeGFS `/zeng_gk`, 546 TB, 261 TB free | Weights (about 60 GB for 0.5B–14B) and EDA run directories are not a constraint |
| OS | Ubuntu 20.04.3 LTS, glibc 2.31 | Supported by Vivado 2023.1 |
| Containers | `chroot` present; no docker, apptainer or singularity | Container images can only be used as an unpacked root filesystem with `chroot` |
| Network | ModelScope, the TUNA PyPI mirror and the Aliyun mirror reachable; GitHub not | Weights can come from ModelScope directly on the server; Python packages from TUNA; anything on GitHub goes through the laptop |
| Qwen weights present | `models/Qwen/Qwen2___5-Coder-1___5B` (used by Gate 0) and `models/Qwen/Qwen2.5-Coder-1.5B`; 7B only as Instruct (`qwen2.5-coder-7b-instruct`) | Need base 0.5B, 3B, 7B (and 14B) |

Install routes identified (to be tested):

- **Yosys / OpenROAD:** the `litex-hub` conda channel has Linux builds of
  OpenROAD (2.0-12381, February 2024; includes OpenSTA) and Yosys 0.38.  The
  `yowasp-yosys` package on PyPI (installable through TUNA) is a fallback for
  Yosys alone.
- **Vivado 2023.1:** web installer in batch mode on the server if AMD's download
  servers are reachable; otherwise an install image prepared on the laptop.

## 2026-10-03 — software and network check (step 1, continued)

| Item | Value | Consequence |
|---|---|---|
| `env_mas` | Python 3.10.20, torch 2.4.1+cu121, transformers 4.46.3, peft 0.13.2 | Stays frozen for Qwen2.5 work.  Qwen3 (Phase 4) needs transformers ≥ 4.51, so it gets a separate environment. |
| Tools | `/opt/conda/bin/conda`, `/usr/bin/iverilog`; no Yosys, no Vivado; no `modelscope` package | Downloader goes into a separate `--target` directory so `env_mas` is untouched |
| Reachable | conda.anaconda.org, repo.anaconda.com, mirrors.tuna.tsinghua.edu.cn, www.xilinx.com, login.amd.com, download.amd.com (host answers) | Conda install of OpenROAD/Yosys is possible on the server.  Whether the Vivado web installer can download is only known by trying it. |
| Not reachable | github.com, xilinx-ax-dl.entitlenow.com (at the root path) | — |

The `litex-hub` OpenROAD and Yosys builds (py38) depend on boost 1.73, qt
5.9.7, spdlog 1.9, tk 8.6 and zlib 1.2.13, all present in the Anaconda `main`
channel (mirrored by TUNA), so a separate `env_eda` with
`-c litex-hub -c <TUNA main>` and `python=3.8` should resolve.

Started next: Qwen2.5-Coder base 0.5B, 3B, 7B and 14B downloads from ModelScope
into `models/Qwen/Qwen2.5-Coder-<size>`, and the `env_eda` conda environment.

## 2026-10-03 — downloads (steps 2–4 in progress)

- `env_eda` conda environment created without errors (OpenROAD and Yosys from
  `litex-hub`, dependencies from the TUNA `main` mirror); tools not yet tested.
- ModelScope downloads running at 2–17 MB/s per file: 0.5B (954 MB) and 3B
  (5.8 GB) complete, 7B in progress, 14B queued.  The folder
  `models/Qwen/Qwen2.5-Coder-1.5B` is empty (512 bytes); the complete 1.5B base is
  `models/Qwen/Qwen2___5-Coder-1___5B` (2.9 GB), as used by Gate 0.
- Vivado 2023.1 Linux web installer (`Xilinx_Unified_2023.1_0507_1903_Lin64.bin`,
  266 MB) copied to `installers/`.  A 2026.1 installer was also copied by mistake;
  it is kept only as a fallback and is not used for any measurement.

## 2026-10-03 — EDA tools start (step 4) and Vivado installer unpacked (step 3)

- Yosys 0.38+92 runs from `env_eda`.  OpenROAD 2.0-12381-g01bba3695 first failed
  to load (`libGL.so.1` missing, needed only for its Qt GUI); adding `libgl` 1.7.0
  from the TUNA `main` mirror to `env_eda` fixed it, and no shared library is now
  missing.  Both live on the shared filesystem, so both boxes can use them.
- `libtinfo.so.5` and `libncurses.so.5`, required by Vivado 2023.1, are present.
- The Vivado installer passed its integrity check, but unpacking it onto the BeeGFS
  share failed in `tar`.  Unpacked instead to the container's local `/tmp` (4.4 TB
  free); Vivado itself will be installed on the share.

## 2026-10-03 — Vivado calibration rule (frozen before any server Vivado run)

Tool: `scaling/eda_vivado.py calibrate --ref-dir gate0/vivado`.  It re-implements,
on the server's Vivado 2023.1, the first 20 Gate 0 circuits in SHA-256 order of
their module names, with the same `run_ppa.run_one` and `ppa_synth.tcl`, and
compares with the laptop's `gate0/vivado/ppa.jsonl`.  SHA-256 of the server's
`run_ppa.py` and `ppa_synth.tcl` is recorded with the result and must be
compared with the laptop's copies.

**Pass** if all of the following hold:

- all 20 circuits agree on whether they implement;
- LUT, FF, DSP and BRAM counts are identical for at least 19 of 20;
- `fmax_mhz` is within 1% of the laptop value for at least 18 of 20;
- no circuit differs by more than 3%.

**If it passes:** server and laptop labels are interchangeable, and the Gate 0
and paper numbers stay directly comparable.

**If it fails:** the server becomes its own measurement contract.  Every label in
the scaling study then comes from the server, and comparisons with Gate 0 or the
paper go only through re-implementing those circuits on the server.  Either way,
the run also gives the first throughput number (circuits per hour at the chosen
parallelism).

## 2026-10-03 — weights complete; Vivado installing

- All four ModelScope downloads finished (`ALL_DONE`): Qwen2.5-Coder base 0.5B
  (954 MB), 3B (5.8 GB), 7B (15 GB) and 14B (28 GB) in `models/Qwen/`; the 1.5B base
  is the Gate 0 copy `models/Qwen/Qwen2___5-Coder-1___5B` (2.9 GB).  Weight hashes
  are to be recorded next.
- `env_eda` tools confirmed: Yosys 0.38+92, OpenROAD 2.0-12381-g01bba3695.
- `scaling/` was fetched to the server checkout through jsDelivr (pinned commit), so
  the server can take new code from jsDelivr without the laptop.  The previous
  project's `run_ppa.py` and `ppa_synth.tcl` are in `fpga/`, and the laptop's Gate 0
  results are in `gate0/vivado/ppa.jsonl`.
- Vivado 2023.1: download finished (the checksum error on one file was recovered by
  the installer), and installing onto the share was at 9%.

## 2026-10-03 — flow identity and recipe provenance (step 7, part 1)

- **Same Vivado flow on server and laptop.**  The server's `fpga/run_ppa.py` and
  `fpga/ppa_synth.tcl` hash to `795fc0ef…843c69d` and `36813384…f85593cf`, identical
  to GitHub commit `40acc78`.  The laptop's copies hash to `94c3fcca…ff2b89eb` and
  `3def59ef…f31c72`, which are exactly those files with Windows (CRLF) line endings,
  checked by converting the commit's files to CRLF and hashing them.  The content
  is therefore the same.
- **Old adapters:** `student_v1_out` (base `Qwen2___5-Coder-1___5B`),
  `sft_qwen_out` and `grpo_qwen` (base `qwen2.5-coder-7b-instruct`) are all LoRA
  r=16, alpha=32, matching the `sft_train_v2.py` defaults.  `sft_qwen_out` has
  checkpoints at 22/44/67/88 steps (4 epochs × 22 steps ≈ 352 rows at effective
  batch 16, consistent with `sft_corpus_v5.jsonl`, 358 rows).  `student_v1_out`
  has checkpoints at 25/50/76/100 (`distill_corpus.jsonl`, 407 rows).
  `grpo_qwen` saved `step_300` and `step_400`.
- Weight SHA-256 hashing started in the background (`logs/weights.sha256`).

## 2026-10-03 — recipe provenance (step 7, part 2) and K1 tools (step 8)

- `training_args.bin` of `student_v1_out` and `sft_qwen_out`: **BF16** (FP16 off),
  lr 1e-4, 4 epochs, batch 1 × 16 accumulation; LoRA on q/k/v/o.  First and last
  logged loss 0.161 → 0.0097 (1.5B student, 100 steps) and 0.542 → 0.0108 (7B SFT,
  88 steps).  The server's `sft_train_v2.py` hashes to `044035d5…401faad2`, as at
  `40acc78`.  The script has no seed option (Trainer default 42, LoRA initialisation
  unseeded), so the K1 wrapper adds the seed.  The plan's "FP16 on V100" is corrected
  to BF16 to keep the earlier recipe unchanged.
- K1 protocol frozen ([K1_PROTOCOL_20261003.md](K1_PROTOCOL_20261003.md)) with its
  tools (`scaling/sft.py`, `scaling/k1.py`, `scaling/make_confirmation_split.py`);
  37 CPU tests pass.  K1 training and generation do not need Vivado, so they can
  start while Vivado installs; Vivado is needed only for the physical step.

## 2026-10-03 — Vivado installed; locale failure; calibration run 1 void

- Vivado 2023.1 installed on the share ("Installation completed successfully").
- It cannot start in these containers: `bin/rdiArgs.sh` forces
  `LC_ALL=en_US.UTF-8`, the containers only have `C`, `C.UTF-8` and `POSIX`, and the
  C++ runtime aborts (`locale::facet::_S_create_c_locale name not valid`).
  Overriding `LC_ALL` from outside has no effect.
- The first calibration launch therefore recorded "SYNTH FAIL" for circuits on which
  Vivado never ran.  It was stopped and moved to `phase0/vivado_calib.failed-locale`.
  It is an environment failure, not a measurement, and the frozen calibration rule
  applies to the next run unchanged.
- Fix: compile `en_US.UTF-8` once onto the share (`/zeng_gk/Amine/mas/locale`) from
  Ubuntu's `locales` source package (2.31-0ubuntu9.18, matching glibc 2.31), and pass
  `LOCPATH`.  No Vivado file is edited.  `eda_vivado.py` now sets `LOCPATH`, runs a
  preflight (`vivado -version` must report 2023.1) before any job, and stops without
  recording if a job's output shows that Vivado itself did not run.
- Locale compiled (`/zeng_gk/Amine/mas/locale/en_US.UTF-8`, plus an `en_US.utf8`
  link).  With `LOCPATH` set, Vivado starts: `vivado v2023.1 (64-bit)`, SW Build
  3865809 (7 May 2023), the same build as the laptop's 2023.1.  The Linux build prints
  the version in lower case, so the preflight check was made case-insensitive.

## 2026-10-03 — first K1 launch failed in setup; calibration run 2 void (Vivado crash)

- **K1:** all learning-rate sweep jobs stopped before training.  The wrapper passed
  `data_seed`, which transformers 4.46.3 refuses with the installed `accelerate`
  (< 1.1.0).  `data_seed` is dropped: with it unset the Trainer seeds its data sampler
  from `seed`, which the wrapper sets, so the protocol's seeding is unchanged.  No
  training step ran, so no outcome was seen.  `--retry-failed` now retries each failed
  job once per relaunch instead of looping.
- **Calibration run 2:** Vivado started (locale fixed) but crashed with a segfault
  ("Abnormal program termination (11)") right after "Routing Is Done", before
  `ppa_synth.tcl` wrote its result.  All 20 records are therefore crashes, not
  measurements, and the run is void like run 1.  A manual run of one circuit reproduced
  the crash.  `eda_vivado.py` now stops without recording whenever Vivado writes no
  result file (`run_ppa` adds an `error` field only then); genuine synthesis failures
  still write `{"compiled": 0}` and are recorded.
