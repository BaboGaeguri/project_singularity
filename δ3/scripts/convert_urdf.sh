#!/bin/bash
# hylion_v3.urdf → hylion_v3.usd 변환
# 출력: /home/laba/project_singularity/δ1 & ε2/usd/hylion_v3.usd
#
# 주의: 변환 스크립트는 URDF의 부모 디렉토리(δ1 & ε2)에 usd/ 폴더를 자동 생성함
#       (source_dir = urdf 파일의 parent.parent = δ1 & ε2/)

set -e

URDF_PATH="/home/laba/project_singularity/δ1 & ε2/urdf/hylion_v3.urdf"
CONVERT_SCRIPT="/home/laba/Berkeley-Humanoid-Lite/source/berkeley_humanoid_lite_assets/scripts/convert_urdf_to_usd.py"

source /home/laba/env_isaaclab/bin/activate

PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  python "$CONVERT_SCRIPT" \
    "$URDF_PATH" \
    --headless \
    --make-instanceable

echo "[DONE] USD 생성 완료: /home/laba/project_singularity/δ1 & ε2/usd/hylion_v3.usd"
