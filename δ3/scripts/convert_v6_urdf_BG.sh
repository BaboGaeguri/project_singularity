#!/bin/bash
# hylion_v6.urdf → USD 변환 (BG)
# IsaacLab 내장 UrdfConverter 사용 → flat 구조 USD 생성 (PhysX contact sensor 호환)
# 출력: /home/laba/project_singularity/δ1 & ε2/usd/hylion_v6.usd

set -e

URDF_PATH="/home/laba/project_singularity/δ1 & ε2/urdf/hylion_v6.urdf"
CONVERT_SCRIPT="/home/laba/Berkeley-Humanoid-Lite/source/berkeley_humanoid_lite_assets/scripts/convert_urdf_to_usd.py"

source /home/laba/env_isaaclab/bin/activate

PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  python "$CONVERT_SCRIPT" \
    "$URDF_PATH" \
    --headless \
    --make-instanceable

echo "[DONE] USD 생성 완료: /home/laba/project_singularity/δ1 & ε2/usd/hylion_v6.usd"
