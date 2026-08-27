#!/usr/bin/env bash
# Guarded L40 launcher for seed_replication_extension_v1.
#
# This is intentionally NOT run_arm.sh: that frozen Study-2 launcher only
# permits the original preregistered seeds.  This script leaves run_arm.sh
# byte-identical and directly invokes the same grpo_oracle.py entry point with
# the prospectively frozen extension arguments.
set -euo pipefail

STUDY="seed_replication_extension_v1"
REPO="/home/adam/mas/mas/fpga"
PY="/home/adam/mas/mas/env_fpga/bin/python"
CONFIG="$REPO/$STUDY/config.json"
VALIDATOR="$REPO/$STUDY/validate.py"
EXPECTED_CONFIG_SHA256="3ae8f352b0cbaf92dbcacd0f15e2791c8c72ee588d51628e51554275985c80ff"
EXPECTED_VALIDATOR_SHA256="394700a3b278eeff07ceca025655a00806357e0bea39b406b21becd18e7885b4"
LOCK="/tmp/${STUDY}.${USER:-adam}.launch.lock"

# This must precede even the read-only preflight. Adam's user site currently
# contains newer torch/Transformers packages that shadow the frozen env unless
# user-site imports are disabled exactly as they were for Study 2.
export PATH="/home/adam/mas/mas/env_fpga/bin:$PATH"
export PYTHONNOUSERSITE=1
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1

die() {
  echo "REFUSING: $*" >&2
  exit 2
}

usage() {
  cat <<'EOF'
Usage:
  launch.sh preflight [run_id ...]
  launch.sh launch-selected run_id [run_id ...]
  launch.sh launch-one run_id
  launch.sh launch-all
  launch.sh status [run_id ...]

Frozen run_id -> physical GPU:
  rf_s3          -> 7
  rf_s4          -> 6
  correctness_s2 -> 5
  correctness_s3 -> 4

No action launches endpoint generation.  A run starts only after the frozen
timing gate says PASS, content hashes match, that run's outputs are absent, and
its assigned physical GPU passes two immediate idle checks.
EOF
}

normalised_sha256() {
  "$PY" - "$1" <<'PY'
import hashlib, pathlib, sys
raw = pathlib.Path(sys.argv[1]).read_bytes().replace(b"\r\n", b"\n")
print(hashlib.sha256(raw).hexdigest())
PY
}

verify_launcher_pins() {
  [ "$(pwd -P)" = "$REPO" ] || die "run from exact repository $REPO"
  [ "$(hostname -s)" = "ubuntu-SYS-420GP-TNR" ] || die "wrong host: $(hostname -s)"
  [ -x "$PY" ] || die "missing isolated Python $PY"
  [ -f "$CONFIG" ] || die "missing $CONFIG"
  [ -f "$VALIDATOR" ] || die "missing $VALIDATOR"
  local actual
  actual="$(normalised_sha256 "$CONFIG")"
  [ "$actual" = "$EXPECTED_CONFIG_SHA256" ] || \
    die "config hash drift: expected $EXPECTED_CONFIG_SHA256, got $actual"
  actual="$(normalised_sha256 "$VALIDATOR")"
  [ "$actual" = "$EXPECTED_VALIDATOR_SHA256" ] || \
    die "validator hash drift: expected $EXPECTED_VALIDATOR_SHA256, got $actual"
}

set_run() {
  RUN_ID="$1"
  case "$RUN_ID" in
    rf_s3)
      REWARD="rf_struct"; SEED=3; GPU=7; MAXG=2000
      OUT="$STUDY/runs/grpo_rf_s3"
      OPTLOG="$STUDY/logs/rf_s3.optimizer.jsonl"
      STDOUT="$STUDY/logs/rf_s3.stdout.log"
      STATUS="$STUDY/status/rf_s3.status.json"
      ;;
    rf_s4)
      REWARD="rf_struct"; SEED=4; GPU=6; MAXG=2000
      OUT="$STUDY/runs/grpo_rf_s4"
      OPTLOG="$STUDY/logs/rf_s4.optimizer.jsonl"
      STDOUT="$STUDY/logs/rf_s4.stdout.log"
      STATUS="$STUDY/status/rf_s4.status.json"
      ;;
    correctness_s2)
      REWARD="correctness"; SEED=2; GPU=5; MAXG=15000
      OUT="$STUDY/runs/grpo_correctness_s2"
      OPTLOG="$STUDY/logs/correctness_s2.optimizer.jsonl"
      STDOUT="$STUDY/logs/correctness_s2.stdout.log"
      STATUS="$STUDY/status/correctness_s2.status.json"
      ;;
    correctness_s3)
      REWARD="correctness"; SEED=3; GPU=4; MAXG=15000
      OUT="$STUDY/runs/grpo_correctness_s3"
      OPTLOG="$STUDY/logs/correctness_s3.optimizer.jsonl"
      STDOUT="$STUDY/logs/correctness_s3.stdout.log"
      STATUS="$STUDY/status/correctness_s3.status.json"
      ;;
    *) die "unknown run_id '$RUN_ID'" ;;
  esac
}

assert_unique_ids() {
  local seen=" " id
  for id in "$@"; do
    set_run "$id"
    case "$seen" in
      *" $id "*) die "duplicate run_id '$id'" ;;
    esac
    seen+="$id "
  done
}

validator_args() {
  local mode="$1"; shift
  VALIDATOR_ARGS=("$VALIDATOR" --config "$CONFIG" --mode "$mode")
  local id
  for id in "$@"; do VALIDATOR_ARGS+=(--run-id "$id"); done
}

build_command() {
  CMD=(
    "$PY" -u grpo_oracle.py
    --base /home/adam/mas/mas/rtlcoder --sft sft_v6c_out
    --reward "$REWARD"
  )
  if [ "$REWARD" = "rf_struct" ]; then
    CMD+=(--rf rf_struct.joblib)
  fi
  CMD+=(
    --dtype fp16 --seed "$SEED"
    --steps "$MAXG" --max-updates 276 --max-groups "$MAXG"
    --save-at-updates 138,276
    --group 8 --gen-batch 4 --temp 1.0 --max-tokens 1536
    --lr 1e-05 --kl_coef 0.1 --incorrect-reward 0.0
    --out "$OUT" --log "$OPTLOG"
  )
}

gpu_idle_once() {
  local gpu="$1" row memory utilization pids
  command -v nvidia-smi >/dev/null || die "nvidia-smi not found"
  row="$(nvidia-smi -i "$gpu" \
    --query-gpu=memory.used,utilization.gpu \
    --format=csv,noheader,nounits)" || die "cannot query GPU $gpu"
  IFS=',' read -r memory utilization <<<"$row"
  memory="${memory//[[:space:]]/}"
  utilization="${utilization//[[:space:]]/}"
  [[ "$memory" =~ ^[0-9]+$ && "$utilization" =~ ^[0-9]+$ ]] || \
    die "unparseable GPU $gpu state: $row"
  pids="$(nvidia-smi -i "$gpu" --query-compute-apps=pid \
    --format=csv,noheader,nounits)" || die "cannot query GPU $gpu compute PIDs"
  if grep -Eq '[0-9]+' <<<"$pids"; then
    die "GPU $gpu has compute process(es): $pids"
  fi
  [ "$memory" -le 128 ] || die "GPU $gpu uses ${memory} MiB (>128 MiB idle ceiling)"
  [ "$utilization" -le 1 ] || die "GPU $gpu utilization is ${utilization}% (>1%)"
  echo "GPU $gpu idle: ${memory} MiB, ${utilization}%, no compute PID"
}

gpu_idle_twice() {
  gpu_idle_once "$1"
  sleep 2
  gpu_idle_once "$1"
}

write_status() {
  local state="$1" exit_code="$2" started="$3" ended="$4"; shift 4
  local launcher_sha
  launcher_sha="$(normalised_sha256 "$REPO/$STUDY/launch.sh")"
  "$PY" - "$REPO/$STATUS" "$STUDY" "$RUN_ID" "$state" "$exit_code" \
    "$GPU" "$started" "$ended" "$EXPECTED_CONFIG_SHA256" \
    "$EXPECTED_VALIDATOR_SHA256" "$launcher_sha" "$@" <<'PY'
import json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "study_id": sys.argv[2],
    "run_id": sys.argv[3],
    "state": sys.argv[4],
    "exit_code": None if sys.argv[5] == "" else int(sys.argv[5]),
    "physical_gpu": int(sys.argv[6]),
    "started_utc": sys.argv[7],
    "ended_utc": sys.argv[8] or None,
    "config_sha256": sys.argv[9],
    "validator_sha256": sys.argv[10],
    "launcher_sha256": sys.argv[11],
    "argv": sys.argv[12:],
}
path.parent.mkdir(parents=True, exist_ok=True)
temporary = path.with_name(path.name + ".tmp." + str(os.getpid()))
temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
PY
}

reserve_one() {
  local id="$1" started
  set_run "$id"
  build_command
  [ ! -e "$REPO/$OUT" ] || die "output already exists: $OUT"
  [ ! -e "$REPO/$OPTLOG" ] || die "optimizer log already exists: $OPTLOG"
  [ ! -e "$REPO/$STDOUT" ] || die "stdout log already exists: $STDOUT"
  [ ! -e "$REPO/$STATUS" ] || die "status already exists: $STATUS"
  gpu_idle_twice "$GPU"
  mkdir -p "$REPO/$STUDY/logs" "$REPO/$STUDY/status" "$REPO/$STUDY/runs"
  started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_status "RESERVED" "" "$started" "" "${CMD[@]}"
  nohup "$REPO/$STUDY/launch.sh" worker "$id" \
    >"$REPO/$STDOUT" 2>&1 </dev/null &
  echo "launched $id pid=$! physical_gpu=$GPU stdout=$STDOUT"
}

worker() {
  local id="${1:?worker requires run_id}" started rc ended state
  cd "$REPO"
  verify_launcher_pins
  set_run "$id"
  build_command
  [ -f "$REPO/$STATUS" ] || die "worker has no reservation status for $id"
  started="$($PY - "$REPO/$STATUS" <<'PY'
import json, sys
x=json.load(open(sys.argv[1], encoding="utf-8"))
assert x.get("state") == "RESERVED", x
print(x["started_utc"])
PY
)" || die "invalid reservation status for $id"
  write_status "RUNNING" "" "$started" "" "${CMD[@]}"

  export CUDA_VISIBLE_DEVICES="$GPU"
  export RTLCODER_PATH="/home/adam/mas/mas/rtlcoder"

  set +e
  "$PY" "$VALIDATOR" --config "$CONFIG" --mode gate --run-id "$id"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    "${CMD[@]}"
    rc=$?
  fi
  set -e
  ended="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ "$rc" -eq 0 ]; then state="COMPLETE"; else state="FAILED"; fi
  write_status "$state" "$rc" "$started" "$ended" "${CMD[@]}"
  exit "$rc"
}

preflight() {
  local ids=("$@")
  if [ "${#ids[@]}" -eq 0 ]; then
    ids=(rf_s3 rf_s4 correctness_s2 correctness_s3)
  fi
  assert_unique_ids "${ids[@]}"
  verify_launcher_pins
  validator_args prelaunch "${ids[@]}"
  "$PY" "${VALIDATOR_ARGS[@]}"
}

launch_selected() {
  local ids=("$@")
  [ "${#ids[@]}" -gt 0 ] || die "launch-selected requires at least one run_id"
  assert_unique_ids "${ids[@]}"
  exec 9>"$LOCK"
  flock -n 9 || die "another $STUDY launcher holds $LOCK"
  preflight "${ids[@]}"
  local id
  for id in "${ids[@]}"; do reserve_one "$id"; done
}

show_status() {
  local ids=("$@") id
  if [ "${#ids[@]}" -eq 0 ]; then
    ids=(rf_s3 rf_s4 correctness_s2 correctness_s3)
  fi
  assert_unique_ids "${ids[@]}"
  for id in "${ids[@]}"; do
    set_run "$id"
    echo "== $id -> GPU $GPU =="
    nvidia-smi -i "$GPU" --query-gpu=memory.used,utilization.gpu \
      --format=csv,noheader || true
    if [ -f "$REPO/$STATUS" ]; then
      "$PY" -m json.tool "$REPO/$STATUS"
    else
      echo "NOT LAUNCHED (no status file)"
    fi
    if [ -f "$REPO/$STDOUT" ]; then
      echo "last log line:"
      tail -n 1 "$REPO/$STDOUT"
    fi
  done
}

ACTION="${1:-}"
case "$ACTION" in
  preflight) shift; cd "$REPO"; preflight "$@" ;;
  launch-selected) shift; cd "$REPO"; launch_selected "$@" ;;
  launch-one) shift; [ "$#" -eq 1 ] || die "launch-one requires exactly one run_id"; cd "$REPO"; launch_selected "$1" ;;
  launch-all) shift; [ "$#" -eq 0 ] || die "launch-all takes no run_id"; cd "$REPO"; launch_selected rf_s3 rf_s4 correctness_s2 correctness_s3 ;;
  status) shift; cd "$REPO"; show_status "$@" ;;
  worker) shift; worker "$@" ;;
  -h|--help|help) usage ;;
  *) usage; exit 2 ;;
esac
