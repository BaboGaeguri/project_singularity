#!/bin/bash
# Desktop launcher for v6 PhysX training.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
VENV_PATH="${VENV_PATH:-$HOME/env_isaaclab}"
BHL_ROOT="${BHL_ROOT:-$HOME/Berkeley-Humanoid-Lite}"
NUM_ENVS="${NUM_ENVS:-4096}"
MAX_ITERS="${MAX_ITERS:-6000}"
LOG_FILE="${LOG_FILE:-/tmp/hylion_v6_physx_desktop.log}"
HYLION_V6_USD="${HYLION_V6_USD:-$PROJECT_ROOT/δ3/usd/hylion_v6/hylion_v6/hylion_v6.usda}"

TRAIN_SCRIPT="$PROJECT_ROOT/δ3/scripts/train_hylion_physx_BG.py"
BHL_SCRIPTS="$BHL_ROOT/scripts/rsl_rl"

if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
  echo "[ERROR] Virtual environment not found: $VENV_PATH"
  echo "[HINT] Run setup first: bash $PROJECT_ROOT/δ3/scripts/setup_desktop_physx_env.sh"
  exit 1
fi

if [[ ! -f "$TRAIN_SCRIPT" ]]; then
  echo "[ERROR] Train script not found: $TRAIN_SCRIPT"
  exit 1
fi

if [[ ! -d "$BHL_SCRIPTS" ]]; then
  echo "[ERROR] BHL scripts path not found: $BHL_SCRIPTS"
  echo "[HINT] Set BHL_ROOT to your Berkeley-Humanoid-Lite path"
  exit 1
fi

if [[ ! -f "$HYLION_V6_USD" ]]; then
  echo "[ERROR] v6 USD not found: $HYLION_V6_USD"
  exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$BHL_SCRIPTS"

if [[ -f /lib/aarch64-linux-gnu/libgomp.so.1 ]]; then
  PRELOAD_VAL="/lib/aarch64-linux-gnu/libgomp.so.1"
else
  PRELOAD_VAL=""
fi

PYTHONUNBUFFERED=1 LD_PRELOAD="$PRELOAD_VAL" \
  nohup python "$TRAIN_SCRIPT" \
    --task Velocity-Hylion-BG-v0 \
    --hylion_usd_path "$HYLION_V6_USD" \
    --num_envs "$NUM_ENVS" \
    --headless \
    --max_iterations "$MAX_ITERS" > "$LOG_FILE" 2>&1 &

echo "[INFO] Desktop PhysX v6 training started (PID: $!)"
echo "[INFO] Log: tail -f $LOG_FILE"
echo "[INFO] Checkpoints: $BHL_SCRIPTS/logs/rsl_rl/hylion/"
