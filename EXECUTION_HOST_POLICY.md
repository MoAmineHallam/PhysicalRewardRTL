# Execution host policy

## L40S host `ubuntu-SYS-420GP-TNR`

- Physical GPU index **0 is permanently excluded from all model training,
  generation, evaluation, and CUDA canaries**.
- This restriction was explicitly supplied by the user on 2026-08-29 after a
  VerilogEval SFT process on GPU 0 stopped with an illegal-memory CUDA error.
- Read-only `nvidia-smi` inspection is permitted; no compute process may be
  launched or resumed on GPU 0.
- Use other idle L40S devices. If none are suitable, wait or use a separately
  validated V100 protocol; never silently substitute hardware in a frozen
  experiment.
