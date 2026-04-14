#!/bin/bash
# Hylion v6 Newton fine-tuning from a pretrained checkpoint (recommended: biped Stage-A)
# Usage:
#   bash /home/laba/project_singularity/δ3/scripts/train_hylion_v6_newton_from_ckpt.sh <checkpoint_path> [max_iterations]

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "[ERROR] checkpoint_path is required"
  echo "Usage: bash $0 <checkpoint_path> [max_iterations]"
  exit 1
fi

CKPT_PATH="$1"
MAX_ITERS="${2:-6000}"

if [[ ! -f "$CKPT_PATH" ]]; then
  echo "[ERROR] checkpoint not found: $CKPT_PATH"
  exit 1
fi

BHL_SCRIPTS="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl"
TRAIN_SCRIPT="/home/laba/project_singularity/δ3/scripts/train_hylion.py"
HYLION_V6_USD="/home/laba/project_singularity/δ3/usd/hylion_v6/hylion_v6/hylion_v6.usda"
LOG_FILE="/tmp/hylion_v6_newton_stageB_from_biped.log"

source /home/laba/env_isaaclab/bin/activate
cd "$BHL_SCRIPTS"
unset PYTHONPATH PYTHONHOME

PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  nohup /home/laba/env_isaaclab/bin/python "$TRAIN_SCRIPT" \
    --task Velocity-Hylion-v0 \
    --hylion_usd_path "$HYLION_V6_USD" \
    --num_envs 4096 \
    --headless \
    --max_iterations "$MAX_ITERS" \
    --stable_walk \
    --stable_walk_schedule fixed \
    --pretrained_checkpoint "$CKPT_PATH" \
    > "$LOG_FILE" 2>&1 &

echo "[INFO] Stage-B started (PID: $!)"
echo "[INFO] Log: tail -f $LOG_FILE"
echo "[INFO] Checkpoints: $BHL_SCRIPTS/logs/rsl_rl/hylion/"
