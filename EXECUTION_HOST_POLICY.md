# Execution host policy

## L40S host `ubuntu-SYS-420GP-TNR`

- Physical GPU index **0 is permanently excluded from all model training,
  generation, evaluation, and CUDA canaries**.
- This restriction was explicitly supplied by the user on 2026-08-29 after a
  VerilogEval SFT process on GPU 0 stopped with an illegal-memory CUDA error.
- Read-only `nvidia-smi` inspection is permitted; no compute process may be
  launched or resumed on GPU 0.
- Use another healthy idle L40S device when one is available.

## Prospective V100 fallback

- If every healthy nonzero L40S is occupied when a new job is ready to launch,
  use an idle V100 instead of L40S GPU 0.
- This fallback applies only before a new run starts. Never migrate, resume, or
  splice an active L40S run onto a V100.
- Before first use, the selected V100 host must pass authentication, exact
  environment and artifact checks, disk-space checks, an idle-GPU check, and a
  CUDA/oracle canary. Record the hostname, physical GPU, GPU model, driver,
  environment, command, and hashes in the run status.
- A protocol that froze L40S hardware or fixed physical GPU assignments must be
  prospectively versioned before V100 launch. Retain the old protocol and state
  the deterministic fallback rule; never silently change a frozen experiment.
- V100 and L40S outcomes remain separately identifiable. Do not pool them as if
  the execution hardware were identical unless a prospectively declared
  analysis explicitly permits it.
- The GPU-0 prohibition above is specific to physical GPU 0 on the L40S host.
  An idle V100 GPU may be used only after its own canary passes.

Current readiness boundary (2026-08-29): key-based, non-interactive SSH access
is working for both declared V100 endpoints.  The local aliases are `v100a`
(`10.251.171.18:30194`, host `49ed1pm9lmiqe-0`) and `v100b`
(`10.251.171.18:30797`, host `8cqofmihc71pg-0`).  Both see the shared repository
at `/zeng_gk/Amine/mas/fpga` and the persistent prefix environment at
`/zeng_gk/Amine/mas/env_mas`.

With `PYTHONNOUSERSITE=1` and that environment first on `PATH`, both hosts were
verified against the frozen stack: Python 3.10.20, torch 2.4.1+cu121,
Transformers 4.46.3, PEFT 0.13.2, Accelerate 1.0.1, NumPy 2.2.6, SciPy 1.15.3,
scikit-learn 1.7.2, joblib 1.5.3, and Icarus Verilog 12.0.  A bounded tensor
canary passed independently on physical GPUs 0 and 1 of both V100 hosts; all
four returned to idle afterward.  Shared storage had ample free space at the
readiness check.  A future job must still pass its job-specific artifact hashes,
functional-oracle canary, and launch-time idle/disk checks before it may start.
This readiness does not relax the permanent L40S GPU-0 exclusion.
