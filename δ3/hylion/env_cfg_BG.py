"""Hylion v6 locomotion environment configuration (BG).

env_cfg.py 기반, robot을 HYLION_CFG_BG(v6)로 교체.
gym task ID: Velocity-Hylion-BG-v0
"""

import os

from isaaclab.sensors import ContactSensorCfg
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

        # Runtime overrides for matrix experiments.
        feet_air_threshold = float(os.environ.get("HYLION_FEET_AIR_THRESHOLD", "0.4"))
        leg_gain_scale = float(os.environ.get("HYLION_LEG_GAIN_SCALE", "1.0"))
        base_mass_add_kg = float(os.environ.get("HYLION_BASE_MASS_ADD_KG", "0.0"))
        contact_body_regex = os.environ.get("HYLION_CONTACT_BODY_REGEX", ".*_ankle_roll")

        if hasattr(self, "rewards") and hasattr(self.rewards, "feet_air_time") and self.rewards.feet_air_time is not None:
            self.rewards.feet_air_time.params["threshold"] = feet_air_threshold
            if "sensor_cfg" in self.rewards.feet_air_time.params:
                self.rewards.feet_air_time.params["sensor_cfg"].body_names = contact_body_regex
        if hasattr(self, "rewards") and hasattr(self.rewards, "feet_slide") and self.rewards.feet_slide is not None:
            if "sensor_cfg" in self.rewards.feet_slide.params:
                self.rewards.feet_slide.params["sensor_cfg"].body_names = contact_body_regex
            if "asset_cfg" in self.rewards.feet_slide.params:
                self.rewards.feet_slide.params["asset_cfg"].body_names = contact_body_regex
        # v6 안정화: 초기 디버그 단계에서는 공격적인 도메인 랜덤화/외력 주입 비활성화.
        if hasattr(self, "events"):
            if hasattr(self.events, "add_base_mass"):
                if abs(base_mass_add_kg) > 1.0e-9:
                    self.events.add_base_mass.params["mass_distribution_params"] = (base_mass_add_kg, base_mass_add_kg)
                    self.events.add_base_mass.params["operation"] = "add"
                else:
                    self.events.add_base_mass = None
            if hasattr(self.events, "base_external_force_torque"):
                self.events.base_external_force_torque = None
            if hasattr(self.events, "scale_all_actuator_torque_constant") and self.events.scale_all_actuator_torque_constant is not None:
                self.events.scale_all_actuator_torque_constant.params["stiffness_distribution_params"] = (
                    leg_gain_scale,
                    leg_gain_scale,
                )
                self.events.scale_all_actuator_torque_constant.params["damping_distribution_params"] = (
                    leg_gain_scale,
                    leg_gain_scale,
                )
            if hasattr(self.events, "reset_base") and self.events.reset_base is not None:
                self.events.reset_base.params["pose_range"] = {
                    "x": (-0.2, 0.2),
                    "y": (-0.2, 0.2),
                    "yaw": (-0.4, 0.4),
                }
                self.events.reset_base.params["velocity_range"] = {
                    "x": (-0.15, 0.15),
                    "y": (-0.15, 0.15),
                    "z": (0.0, 0.0),
                    "roll": (-0.15, 0.15),
                    "pitch": (-0.15, 0.15),
                    "yaw": (-0.15, 0.15),
                }
            if hasattr(self.events, "reset_robot_joints") and self.events.reset_robot_joints is not None:
                self.events.reset_robot_joints.params["position_range"] = (0.9, 1.1)
        # Track both left/right ankle_roll links at the end of each leg chain.
        # Keep explicit leg segment names to preserve a stable path template.
        self.scene.contact_forces = ContactSensorCfg(
            prim_path="{ENV_REGEX_NS}/robot/.*",
            history_length=3,
            track_air_time=True,
        )
