"""Hylion v6 locomotion environment configuration (BG).

env_cfg.py 기반, robot을 HYLION_CFG_BG(v6)로 교체.
gym task ID: Velocity-Hylion-BG-v0
"""

from isaaclab.utils import configclass
from berkeley_humanoid_lite.tasks.locomotion.velocity.velocity_env_cfg import LocomotionVelocityEnvCfg

from .env_cfg import CommandsCfg, ObservationsCfg, ActionsCfg, RewardsCfg, TerminationsCfg, EventsCfg, CurriculumsCfg
from .robot_cfg_BG import HYLION_CFG_BG


@configclass
class HylionEnvCfg_BG(LocomotionVelocityEnvCfg):
    commands: CommandsCfg = CommandsCfg()
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventsCfg = EventsCfg()
    curriculums: CurriculumsCfg = CurriculumsCfg()

    def __post_init__(self):
        super().__post_init__()
        self.decimation = 8  # 25 Hz (200 Hz physics / 8)
        self.scene.robot = HYLION_CFG_BG.replace(prim_path="{ENV_REGEX_NS}/robot")
