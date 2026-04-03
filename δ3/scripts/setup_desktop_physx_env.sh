#!/bin/bash
# Desktop bootstrap for v6 PhysX training (no Newton).

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
VENV_PATH="${VENV_PATH:-$HOME/env_isaaclab}"
ISAACLAB_ROOT="${ISAACLAB_ROOT:-$HOME/IsaacLab}"
BHL_ROOT="${BHL_ROOT:-$HOME/Berkeley-Humanoid-Lite}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] Python executable not found: $PYTHON_BIN"
  echo "[HINT] Set PYTHON_BIN, e.g. PYTHON_BIN=python3"
  exit 1
fi

if [[ ! -d "$VENV_PATH" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install \
  --extra-index-url https://pypi.nvidia.com \
  -r "$PROJECT_ROOT/requirements_robot_physx.txt"

if [[ ! -d "$ISAACLAB_ROOT/.git" ]]; then
  git clone https://github.com/isaac-sim/IsaacLab.git "$ISAACLAB_ROOT"
fi

pushd "$ISAACLAB_ROOT" >/dev/null
git checkout develop
python -m pip install -e source/isaaclab
python -m pip install -e source/isaaclab_assets
python -m pip install -e source/isaaclab_tasks
python -m pip install -e source/isaaclab_rl
python -m pip install -e source/isaaclab_physx
popd >/dev/null

if [[ ! -d "$BHL_ROOT/.git" ]]; then
  git clone https://github.com/berkeley-humanoid-lite/Berkeley-Humanoid-Lite.git "$BHL_ROOT"
fi

pushd "$BHL_ROOT" >/dev/null
python -m pip install -e source/berkeley_humanoid_lite
python -m pip install rsl-rl-lib==5.0.1
popd >/dev/null

echo "[OK] Desktop PhysX environment is ready."
echo "[INFO] Activate with: source $VENV_PATH/bin/activate"
echo "[INFO] Run launcher: bash $PROJECT_ROOT/δ3/scripts/launch_desktop_physx_v6.sh"
