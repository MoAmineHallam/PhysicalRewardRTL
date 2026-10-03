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
