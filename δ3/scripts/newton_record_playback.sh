#!/usr/bin/env bash
set -euo pipefail

# Method 1 workflow:
# - keep training/eval physics on Newton (cuda)
# - inspect behavior via headless mp4 recordings

CKPT_DEFAULT="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/hylion/2026-04-02_09-29-44/model_3999.pt"
OUTDIR_DEFAULT="/home/laba/project_singularity/δ3/videos/newton_playback"
STEPS_DEFAULT=480

CKPT="${1:-$CKPT_DEFAULT}"
STEPS="${2:-$STEPS_DEFAULT}"
OUTDIR="${3:-$OUTDIR_DEFAULT}"

PLAY_DIR="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl"
PLAY_SCRIPT="$PLAY_DIR/play_hylion_511.py"
PYTHON_BIN="/home/laba/env_isaaclab/bin/python"

# Use wildcard to avoid hardcoding non-ASCII folder names in command logic.
USD_PATH="$(ls -d /home/laba/project_singularity/*3/usd/hylion_v4/hylion_v4/hylion_v4.usda | head -n 1)"

mkdir -p "$OUTDIR"
LOG_FILE="${OUTDIR}/newton_record_$(date +%Y%m%d_%H%M%S).log"

cd "$PLAY_DIR"

echo "[INFO] Checkpoint: $CKPT"
echo "[INFO] USD: $USD_PATH"
echo "[INFO] Steps: $STEPS"
echo "[INFO] Outdir: $OUTDIR"
echo "[INFO] Log: $LOG_FILE"

# Clean environment to avoid Python 3.11/3.12 path collisions.
env -u PYTHONPATH -u PYTHONHOME -u LD_LIBRARY_PATH \
  LD_PRELOAD=/lib/aarch64-linux-gnu/libgomp.so.1 \
  PYTHONUNBUFFERED=1 \
  "$PYTHON_BIN" "$PLAY_SCRIPT" \
  --task Velocity-Hylion-v0 \
  --num_envs 1 \
  --device cuda:0 \
  --physics_backend auto \
  --headless \
  --video \
  --video_length "$STEPS" \
  --max_steps "$STEPS" \
  --video_folder "$OUTDIR" \
  --hylion_usd_path "$USD_PATH" \
  --hylion_ckpt "$CKPT" \
  > "$LOG_FILE" 2>&1

echo "[INFO] Run finished. Generated files:"
find "$OUTDIR" -maxdepth 1 -type f | sort
