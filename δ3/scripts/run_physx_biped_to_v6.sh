#!/usr/bin/env bash
set -euo pipefail

BHL_SCRIPTS="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl"
PY_BIN="/home/laba/env_isaaclab/bin/python"
TRAIN_SCRIPT="/home/laba/project_singularity/δ3/scripts/train_hylion_physx_BG.py"
HYLION_V6_USD="/home/laba/project_singularity/δ3/usd/hylion_v6/hylion_v6/hylion_v6.usda"

NUM_ENVS="${NUM_ENVS:-4096}"
BIPED_ITERS="${BIPED_ITERS:-6000}"
V6_ITERS="${V6_ITERS:-6000}"
CHECK_INTERVAL="${CHECK_INTERVAL:-15}"

BIPED_LOG="/tmp/bhl_biped_physx_stageA.log"
V6_LOG="/tmp/hylion_v6_physx_stageB.log"
PIPELINE_LOG="/tmp/physx_pipeline.log"
LOCK_FILE="/tmp/physx_pipeline.lock"

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "$PIPELINE_LOG"
}

latest_checkpoint() {
  local run_dir="$1"
  ls -1 "$run_dir"/model_*.pt 2>/dev/null | sed -E 's/.*model_([0-9]+)\.pt/\1 &/' | sort -n | awk '{print $2}' | tail -n 1
}

extract_run_dir() {
  local log_file="$1"
  grep -oE "/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/[a-zA-Z_-]+/[0-9_-]+" "$log_file" 2>/dev/null | tail -n 1
}

start_biped_if_needed() {
  if pgrep -af "train_hylion_physx_BG.py --task Velocity-Berkeley-Humanoid-Lite-Biped-v0" >/dev/null 2>&1; then
    log "Stage-A already running (biped PhysX)."
    return 0
  fi

  log "Starting Stage-A: biped PhysX training"
  cd "$BHL_SCRIPTS"
  source /home/laba/env_isaaclab/bin/activate
  unset PYTHONPATH PYTHONHOME
  PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
    nohup "$PY_BIN" "$TRAIN_SCRIPT" \
      --task Velocity-Berkeley-Humanoid-Lite-Biped-v0 \
      --num_envs "$NUM_ENVS" \
      --headless \
      --max_iterations "$BIPED_ITERS" \
      > "$BIPED_LOG" 2>&1 &
  log "Stage-A PID: $!"
}

wait_for_biped_finish() {
  log "Waiting for Stage-A completion..."
  while true; do
    if [[ -f "$BIPED_LOG" ]] && grep -qE "Traceback|contains NaN values|Mean value loss: nan|Mean surrogate loss: nan" "$BIPED_LOG"; then
      log "Stage-A failed (error marker detected). Stop pipeline."
      exit 1
    fi

    if pgrep -af "train_hylion_physx_BG.py --task Velocity-Berkeley-Humanoid-Lite-Biped-v0" >/dev/null 2>&1; then
      local iter_line
      iter_line=$(grep -E "Learning iteration" "$BIPED_LOG" 2>/dev/null | tail -n 1 || true)
      if [[ -n "$iter_line" ]]; then
        log "Stage-A progress: $iter_line"
      fi
      sleep "$CHECK_INTERVAL"
      continue
    fi

    local run_dir
    run_dir=$(extract_run_dir "$BIPED_LOG")
    if [[ -z "$run_dir" || ! -d "$run_dir" ]]; then
      log "Stage-A ended but run directory not found. Stop pipeline."
      exit 1
    fi

    local ckpt
    ckpt=$(latest_checkpoint "$run_dir")
    if [[ -z "$ckpt" || ! -f "$ckpt" ]]; then
      log "Stage-A ended but no checkpoint found. Stop pipeline."
      exit 1
    fi

    log "Stage-A complete. Latest checkpoint: $ckpt"
    echo "$ckpt"
    return 0
  done
}

start_v6_from_checkpoint() {
  local ckpt="$1"

  if pgrep -af "train_hylion_physx_BG.py --task Velocity-Hylion-BG-v0" >/dev/null 2>&1; then
    log "Stage-B already running (v6 PhysX)."
    return 0
  fi

  if [[ ! -f "$HYLION_V6_USD" ]]; then
    log "Missing v6 USD: $HYLION_V6_USD"
    exit 1
  fi

  log "Starting Stage-B: v6 PhysX fine-tuning from checkpoint"
  cd "$BHL_SCRIPTS"
  source /home/laba/env_isaaclab/bin/activate
  unset PYTHONPATH PYTHONHOME
  PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
    nohup "$PY_BIN" "$TRAIN_SCRIPT" \
      --task Velocity-Hylion-BG-v0 \
      --hylion_usd_path "$HYLION_V6_USD" \
      --pretrained_checkpoint "$ckpt" \
      --num_envs "$NUM_ENVS" \
      --headless \
      --max_iterations "$V6_ITERS" \
      > "$V6_LOG" 2>&1 &

  log "Stage-B PID: $!"
  log "Stage-B log: $V6_LOG"
}

main() {
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    echo "[INFO] Another pipeline instance is already running."
    exit 0
  fi

  : > "$PIPELINE_LOG"
  log "Pipeline start: PhysX biped -> v6"
  start_biped_if_needed
  ckpt_path=$(wait_for_biped_finish)
  start_v6_from_checkpoint "$ckpt_path"
  log "Pipeline transition complete. Use: tail -f $PIPELINE_LOG and tail -f $V6_LOG"
}

main "$@"
