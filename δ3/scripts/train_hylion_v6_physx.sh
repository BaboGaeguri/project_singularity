#!/bin/bash
# Hylion v6 training (PhysX-only)
# task: Velocity-Hylion-BG-v0
# log: /tmp/hylion_v6_physx_train.log

set -e

BHL_SCRIPTS="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl"
TRAIN_SCRIPT="/home/laba/project_singularity/δ3/scripts/train_hylion_physx_BG.py"
HYLION_V6_USD="/home/laba/project_singularity/δ3/usd/hylion_v6/hylion_v6/hylion_v6.usda"

source /home/laba/env_isaaclab/bin/activate
cd "$BHL_SCRIPTS"

PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  nohup python "$TRAIN_SCRIPT" \
    --task Velocity-Hylion-BG-v0 \
    --hylion_usd_path "$HYLION_V6_USD" \
    --num_envs 4096 \
    --headless \
    --max_iterations 6000 > /tmp/hylion_v6_physx_train.log 2>&1 &

echo "[INFO] PhysX v6 training started (PID: $!)"
echo "[INFO] Log: tail -f /tmp/hylion_v6_physx_train.log"
echo "[INFO] Checkpoints: $BHL_SCRIPTS/logs/rsl_rl/hylion/"
