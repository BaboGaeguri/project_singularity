#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1:-/home/laba/project_singularity/δ3/hylion_v4_retrain_stable.log}"
INTERVAL="${INTERVAL:-2}"
GUARD_LOG="/home/laba/project_singularity/δ3/hylion_guard.log"

print_once() {
  echo "==== hylion retrain monitor ($(date '+%F %T')) ===="

  if pgrep -af "train_hylion.py" >/dev/null 2>&1; then
    echo "process: RUNNING"
    pgrep -af "train_hylion.py" | head -1
  else
    echo "process: NOT RUNNING"
  fi

  if pgrep -af "auto_guard_hylion_train.sh" >/dev/null 2>&1; then
    echo "guard: RUNNING"
    pgrep -af "auto_guard_hylion_train.sh" | head -1
  else
    echo "guard: NOT RUNNING"
  fi

  if [[ ! -f "$LOG_FILE" ]]; then
    echo "log: not found -> $LOG_FILE"
    return 0
  fi

  echo "log: $LOG_FILE"

  echo "-- setup markers --"
  grep -n "Applying stable-walk fine-tuning configuration\|Loading pretrained checkpoint\|Completed setting up the environment" "$LOG_FILE" | tail -5 || true

  echo "-- latest metrics --"
  grep -n "Learning iteration\|Mean value loss:\|Mean surrogate loss:\|Mean reward:\|Mean action std:" "$LOG_FILE" | tail -12 || true

  local run_dir
  run_dir=$(grep -oE "/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/hylion/[0-9_-]+" "$LOG_FILE" | tail -1 || true)
  if [[ -n "$run_dir" && -d "$run_dir" ]]; then
    echo "-- latest checkpoints --"
    ls -1 "$run_dir"/model_*.pt 2>/dev/null | tail -8 || true
  fi

  echo "-- recent errors --"
  grep -n "Traceback\|ERROR\|Exception\|nan" "$LOG_FILE" | tail -10 || true

  echo "-- guard log --"
  tail -n 8 "$GUARD_LOG" 2>/dev/null || true
}

if [[ "${2:-}" == "--watch" ]]; then
  while true; do
    clear || true
    print_once
    sleep "$INTERVAL"
  done
else
  print_once
fi
