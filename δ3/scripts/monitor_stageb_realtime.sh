#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1:-/tmp/hylion_v6_physx_M4.log}"
INTERVAL="${2:-2}"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "[ERROR] Log file not found: $LOG_FILE"
  exit 1
fi

while true; do
  clear
  date '+%F %T'
  echo "=== Process ==="
  pgrep -af "train_hylion_physx_BG.py --task Velocity-Hylion-BG-v0" || echo "not running"

  echo
  echo "=== Latest Metrics ==="
  grep -nE "Learning iteration|Mean value loss:|Mean surrogate loss:|Mean reward:|Mean episode length:|Mean action std:|feet_air_time" "$LOG_FILE" | tail -n 20 || true

  echo
  echo "=== Error Markers ==="
  grep -nE "Traceback|ValueError|RuntimeError|contains NaN values" "$LOG_FILE" | tail -n 8 || echo "no error markers"

  echo
  echo "=== Capacity Warning (PhysX) ==="
  grep -n "totalAggregatePairsCapacity" "$LOG_FILE" | tail -n 4 || echo "no capacity warning"

  echo
  echo "=== Log Tail ==="
  tail -n 12 "$LOG_FILE" || true

  sleep "$INTERVAL"
done
