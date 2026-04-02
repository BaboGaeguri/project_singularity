"""Hylion v3 locomotion task.

이 패키지를 import하면 Isaac Lab gym에 'Velocity-Hylion-v0' 환경이 등록된다.
train_hylion.py에서 sys.path에 δ3/를 추가한 뒤 import한다.
"""

import gymnasium as gym

from . import agents, env_cfg

gym.register(
    id="Velocity-Hylion-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": env_cfg.HylionEnvCfg,
        "rsl_rl_cfg_entry_point": agents.rsl_rl_ppo_cfg.HylionPPORunnerCfg,
    },
)
