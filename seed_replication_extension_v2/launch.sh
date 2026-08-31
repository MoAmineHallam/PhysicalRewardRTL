#!/usr/bin/env bash
# Guarded per-host launcher for seed_replication_extension_v2.
set -euo pipefail

STUDY="seed_replication_extension_v2"
REPO="/zeng_gk/Amine/mas/fpga-v100-v2"
PY="/zeng_gk/Amine/mas/env_mas/bin/python"
CONFIG="$REPO/$STUDY/config.json"
VALIDATOR="$REPO/$STUDY/validate.py"
EXPECTED_CONFIG_SHA256="98be47564acf6c344939c4b043fb9476dfac49d4975f3bef7b8df9adae02d81b"
EXPECTED_VALIDATOR_SHA256="d80ee516bc0589985f3f5bcbbf8ae6799f679aa2f4cbf7ac30a6be1b2fa3018a"
LOCK="/tmp/${STUDY}.${USER:-root}.launch.lock"

export PATH="/zeng_gk/Amine/mas/env_mas/bin:$PATH"
export PYTHONNOUSERSITE=1
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1

die() { echo "REFUSING: $*" >&2; exit 2; }

normalised_sha256() {
  "$PY" - "$1" <<'PY'
import hashlib, pathlib, sys
raw = pathlib.Path(sys.argv[1]).read_bytes().replace(b"\r\n", b"\n")
print(hashlib.sha256(raw).hexdigest())
PY
}

host_alias() {
  case "$(hostname -s)" in
    49ed1pm9lmiqe-0) echo v100a ;;
    8cqofmihc71pg-0) echo v100b ;;
    *) die "undeclared host $(hostname -s)" ;;
  esac
}

verify_launcher_pins() {
  [ "$(pwd -P)" = "$REPO" ] || die "run from exact repository $REPO"
  [ -x "$PY" ] || die "missing isolated Python $PY"
  [ "$(normalised_sha256 "$CONFIG")" = "$EXPECTED_CONFIG_SHA256" ] || \
    die "config hash drift"
  [ "$(normalised_sha256 "$VALIDATOR")" = "$EXPECTED_VALIDATOR_SHA256" ] || \
    die "validator hash drift"
}

set_run() {
  RUN_ID="$1"
  case "$RUN_ID" in
    rf_s3)
      ALIAS=v100a; EXPECTED_HOST=49ed1pm9lmiqe-0
      EXPECTED_MODEL="Tesla V100-SXM2-32GB"; GPU=0
      REWARD=rf_struct; SEED=3; MAXG=2000 ;;
    rf_s4)
      ALIAS=v100b; EXPECTED_HOST=8cqofmihc71pg-0
      EXPECTED_MODEL="Tesla V100S-PCIE-32GB"; GPU=0
      REWARD=rf_struct; SEED=4; MAXG=2000 ;;
    correctness_s2)
      ALIAS=v100a; EXPECTED_HOST=49ed1pm9lmiqe-0
      EXPECTED_MODEL="Tesla V100-SXM2-32GB"; GPU=1
      REWARD=correctness; SEED=2; MAXG=15000 ;;
    correctness_s3)
      ALIAS=v100b; EXPECTED_HOST=8cqofmihc71pg-0
      EXPECTED_MODEL="Tesla V100S-PCIE-32GB"; GPU=1
      REWARD=correctness; SEED=3; MAXG=15000 ;;
    *) die "unknown run_id '$RUN_ID'" ;;
  esac
  OUT="$STUDY/runs/grpo_$RUN_ID"
  OPTLOG="$STUDY/logs/$RUN_ID.optimizer.jsonl"
  STDOUT="$STUDY/logs/$RUN_ID.stdout.log"
  STATUS="$STUDY/status/$RUN_ID.status.json"
}

assert_local_run() {
  set_run "$1"
  [ "$(hostname -s)" = "$EXPECTED_HOST" ] || \
    die "$RUN_ID belongs to $EXPECTED_HOST, not $(hostname -s)"
  local model
  model="$(nvidia-smi -i "$GPU" --query-gpu=name --format=csv,noheader | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [ "$model" = "$EXPECTED_MODEL" ] || \
    die "$RUN_ID GPU model changed: expected $EXPECTED_MODEL, got $model"
}

local_runs() {
  case "$(host_alias)" in
    v100a) echo "rf_s3 correctness_s2" ;;
    v100b) echo "rf_s4 correctness_s3" ;;
  esac
}

build_command() {
  CMD=("$PY" -u grpo_oracle.py
       --base /zeng_gk/Amine/mas/rtlcoder --sft sft_v6c_out
       --reward "$REWARD")
  [ "$REWARD" != rf_struct ] || CMD+=(--rf rf_struct.joblib)
  CMD+=(--dtype fp16 --seed "$SEED"
        --steps "$MAXG" --max-updates 276 --max-groups "$MAXG"
        --save-at-updates 138,276
        --group 8 --gen-batch 4 --temp 1.0 --max-tokens 1536
        --lr 1e-05 --kl_coef 0.1 --incorrect-reward 0.0
        --out "$OUT" --log "$OPTLOG")
}

gpu_idle_once() {
  local row memory utilization pids
  row="$(nvidia-smi -i "$GPU" --query-gpu=memory.used,utilization.gpu \
    --format=csv,noheader,nounits)" || die "cannot query GPU $GPU"
  IFS=',' read -r memory utilization <<<"$row"
  memory="${memory//[[:space:]]/}"; utilization="${utilization//[[:space:]]/}"
  pids="$(nvidia-smi -i "$GPU" --query-compute-apps=pid \
    --format=csv,noheader,nounits)" || die "cannot query GPU $GPU processes"
  ! grep -Eq '[0-9]+' <<<"$pids" || die "GPU $GPU has compute PID(s): $pids"
  [ "$memory" -le 128 ] || die "GPU $GPU uses ${memory} MiB"
  [ "$utilization" -le 1 ] || die "GPU $GPU utilization is ${utilization}%"
}

gpu_idle_twice() { gpu_idle_once; sleep 2; gpu_idle_once; }

write_status() {
  local state="$1" exit_code="$2" started="$3" ended="$4"; shift 4
  local launcher_sha driver
  launcher_sha="$(normalised_sha256 "$REPO/$STUDY/launch.sh")"
  driver="$(nvidia-smi -i "$GPU" --query-gpu=driver_version --format=csv,noheader | tr -d '[:space:]')"
  "$PY" - "$REPO/$STATUS" "$STUDY" "$RUN_ID" "$state" "$exit_code" \
    "$GPU" "$started" "$ended" "$EXPECTED_HOST" "$EXPECTED_MODEL" "$driver" \
    "$EXPECTED_CONFIG_SHA256" "$EXPECTED_VALIDATOR_SHA256" "$launcher_sha" "$@" <<'PY'
import json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
payload = {
    "schema_version": 1, "study_id": sys.argv[2], "run_id": sys.argv[3],
    "state": sys.argv[4],
    "exit_code": None if sys.argv[5] == "" else int(sys.argv[5]),
    "physical_gpu": int(sys.argv[6]), "started_utc": sys.argv[7],
    "ended_utc": sys.argv[8] or None, "hostname": sys.argv[9],
    "gpu_model": sys.argv[10], "driver_version": sys.argv[11],
    "config_sha256": sys.argv[12], "validator_sha256": sys.argv[13],
    "launcher_sha256": sys.argv[14], "argv": sys.argv[15:],
}
path.parent.mkdir(parents=True, exist_ok=True)
tmp = path.with_name(path.name + ".tmp." + str(os.getpid()))
tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
os.replace(tmp, path)
PY
}

validator_args() {
  local mode="$1"; shift
  VALIDATOR_ARGS=("$VALIDATOR" --config "$CONFIG" --mode "$mode")
  local id
  for id in "$@"; do VALIDATOR_ARGS+=(--run-id "$id"); done
}

preflight() {
  local ids=("$@") id
  [ "${#ids[@]}" -gt 0 ] || read -r -a ids <<<"$(local_runs)"
  verify_launcher_pins
  for id in "${ids[@]}"; do assert_local_run "$id"; done
  validator_args prelaunch "${ids[@]}"
  "$PY" "${VALIDATOR_ARGS[@]}"
}

host_ready() {
  local ids id audit
  read -r -a ids <<<"$(local_runs)"
  verify_launcher_pins
  for id in "${ids[@]}"; do assert_local_run "$id"; done
  audit="$STUDY/readiness/$(hostname -s).json"
  mkdir -p "$REPO/$STUDY/readiness"
  validator_args host-ready "${ids[@]}"
  "$PY" "${VALIDATOR_ARGS[@]}" --out "$audit"
}

reserve_one() {
  local started
  assert_local_run "$1"; build_command
  [ ! -e "$REPO/$OUT" ] || die "output exists: $OUT"
  [ ! -e "$REPO/$OPTLOG" ] || die "optimizer log exists: $OPTLOG"
  [ ! -e "$REPO/$STDOUT" ] || die "stdout log exists: $STDOUT"
  [ ! -e "$REPO/$STATUS" ] || die "status exists: $STATUS"
  gpu_idle_twice
  mkdir -p "$REPO/$STUDY/logs" "$REPO/$STUDY/status" "$REPO/$STUDY/runs"
  started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_status RESERVED "" "$started" "" "${CMD[@]}"
  nohup bash "$REPO/$STUDY/launch.sh" worker "$RUN_ID" \
    >"$REPO/$STDOUT" 2>&1 </dev/null &
  echo "launched $RUN_ID pid=$! host=$EXPECTED_HOST gpu=$GPU"
}

launch_selected() {
  local ids=("$@") id
  [ "${#ids[@]}" -gt 0 ] || die "no run IDs selected"
  exec 9>"$LOCK"; flock -n 9 || die "another launcher holds $LOCK"
  preflight "${ids[@]}"
  for id in "${ids[@]}"; do reserve_one "$id"; done
}

worker() {
  local started rc ended state
  cd "$REPO"; verify_launcher_pins; assert_local_run "$1"; build_command
  [ -f "$REPO/$STATUS" ] || die "missing reservation status"
  started="$("$PY" - "$REPO/$STATUS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1], encoding="utf-8")); assert x["state"] == "RESERVED"
print(x["started_utc"])
PY
)"
  write_status RUNNING "" "$started" "" "${CMD[@]}"
  export CUDA_VISIBLE_DEVICES="$GPU"
  export RTLCODER_PATH="/zeng_gk/Amine/mas/rtlcoder"
  set +e
  "$PY" "$VALIDATOR" --config "$CONFIG" --mode gate --run-id "$RUN_ID"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    "${CMD[@]}"
    rc=$?
  fi
  set -e
  ended="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ "$rc" -eq 0 ]; then state=COMPLETE; else state=FAILED; fi
  write_status "$state" "$rc" "$started" "$ended" "${CMD[@]}"
  exit "$rc"
}

show_status() {
  local ids id
  read -r -a ids <<<"$(local_runs)"
  for id in "${ids[@]}"; do
    assert_local_run "$id"
    echo "== $RUN_ID host=$EXPECTED_HOST gpu=$GPU =="
    nvidia-smi -i "$GPU" --query-gpu=memory.used,utilization.gpu \
      --format=csv,noheader || true
    if [ -f "$REPO/$STATUS" ]; then "$PY" -m json.tool "$REPO/$STATUS"
    else echo "NOT LAUNCHED"; fi
    [ ! -f "$REPO/$STDOUT" ] || tail -n 1 "$REPO/$STDOUT"
  done
}

ACTION="${1:-}"; shift || true
cd "$REPO"
case "$ACTION" in
  host-ready) [ "$#" -eq 0 ] || die "host-ready takes no IDs"; host_ready ;;
  preflight) preflight "$@" ;;
  launch-selected) launch_selected "$@" ;;
  launch-local) [ "$#" -eq 0 ] || die "launch-local takes no IDs";
    read -r -a ids <<<"$(local_runs)"; launch_selected "${ids[@]}" ;;
  launch-one) [ "$#" -eq 1 ] || die "launch-one requires one ID";
    launch_selected "$1" ;;
  status) [ "$#" -eq 0 ] || die "status takes no IDs"; show_status ;;
  worker) [ "$#" -eq 1 ] || die "worker requires one ID"; worker "$1" ;;
  *) echo "Usage: launch.sh {host-ready|preflight|launch-local|launch-one ID|status}"; exit 2 ;;
esac
