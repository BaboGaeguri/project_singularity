#!/usr/bin/env bash
set -euo pipefail

INTERVAL="${1:-60}"
OUT="/home/laba/project_singularity/δ3/physx_vs_newton_watch.log"
PHY="/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/biped/2026-03-27_14-36-49/events.out.tfevents.1774589826.spark-8434.2360861.0"

while true; do
  {
    echo "==== physx_vs_newton ($(date '+%F %T')) ===="
    source /home/laba/env_isaaclab/bin/activate
    /home/laba/env_isaaclab/bin/python - << 'PY'
from pathlib import Path
from tensorboard.backend.event_processing import event_accumulator

physx_event=Path('/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/biped/2026-03-27_14-36-49/events.out.tfevents.1774589826.spark-8434.2360861.0')
run_root=Path('/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/biped')
newest=sorted([p for p in run_root.iterdir() if p.is_dir() and p.name[:1].isdigit()], key=lambda p:p.stat().st_mtime, reverse=True)[0]
newton_event=sorted(newest.glob('events.out.tfevents.*'), key=lambda p:p.stat().st_mtime, reverse=True)[0]

def load(path):
    ea=event_accumulator.EventAccumulator(str(path)); ea.Reload(); return ea

def near(events, step):
    return min(events, key=lambda e: abs(e.step-step))

physx=load(physx_event)
newton=load(newton_event)
cur=newton.Scalars('Train/mean_reward')[-1].step
print('newton_run:', newest)
print('current_step:', cur)
for tag in ['Train/mean_reward','Policy/mean_std','Loss/value','Loss/surrogate']:
    p=near(physx.Scalars(tag), cur)
    n=newton.Scalars(tag)[-1]
    print(f'{tag}: PhysX(step={p.step}, v={p.value:.4f}) | Newton(step={n.step}, v={n.value:.4f})')
PY
  } | tee -a "$OUT"
  sleep "$INTERVAL"
done
