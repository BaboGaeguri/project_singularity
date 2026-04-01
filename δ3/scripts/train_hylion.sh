#!/bin/bash
# Hylion v3 걷기 학습 — Newton 백엔드
# 실행 전 convert_urdf.sh 로 USD 먼저 생성해야 함
#
# 체크포인트 저장: /home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/hylion/<timestamp>/

set -e

BHL_SCRIPTS="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl"
TRAIN_SCRIPT="/home/laba/project_singularity/δ3/scripts/train_hylion.py"

source /home/laba/env_isaaclab/bin/activate

# cli_args.py가 BHL scripts/rsl_rl/ 에 있으므로 그 디렉토리에서 실행
cd "$BHL_SCRIPTS"

PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  nohup python "$TRAIN_SCRIPT" \
    --task Velocity-Hylion-v0 \
    --num_envs 4096 \
    --headless \
    --max_iterations 6000 > /tmp/hylion_train.log 2>&1 &

echo "[INFO] 학습 시작 (PID: $!)"
echo "[INFO] 로그: tail -f /tmp/hylion_train.log"
echo "[INFO] 체크포인트: $BHL_SCRIPTS/logs/rsl_rl/hylion/"
