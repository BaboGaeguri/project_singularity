"""Hylion v3 RL 학습 스크립트.

BHL train.py와 동일하나 hylion task를 추가로 등록한다.
실행 위치: /home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl/
  (cli_args.py가 그 디렉토리에 있으므로)

사용법:
  cd /home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl
  source /home/laba/env_isaaclab/bin/activate
  PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \\
    python /home/laba/project_singularity/δ3/scripts/train_hylion.py \\
      --task Velocity-Hylion-v0 \\
      --num_envs 4096 \\
      --headless \\
      --max_iterations 6000
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import os
import sys

# cli_args.py는 BHL scripts/rsl_rl/ 에 있음 — AppLauncher import 전에 경로 추가
sys.path.insert(0, "/home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl")

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

# add argparse arguments
parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False)
parser.add_argument("--video_length", type=int, default=200)
parser.add_argument("--video_interval", type=int, default=2000)
parser.add_argument("--num_envs", type=int, default=None)
parser.add_argument("--task", type=str, default="Velocity-Hylion-v0")
parser.add_argument("--seed", type=int, default=None)
parser.add_argument("--max_iterations", type=int, default=None)
parser.add_argument("--override_lr", type=float, default=None, help="Override PPO learning rate")
parser.add_argument("--override_entropy", type=float, default=None, help="Override PPO entropy coefficient")
parser.add_argument(
    "--override_schedule",
    type=str,
    default=None,
    choices=["adaptive", "fixed"],
    help="Override PPO learning-rate schedule",
)
parser.add_argument("--override_steps_per_env", type=int, default=None, help="Override PPO rollout steps per env")
parser.add_argument(
    "--newton_stage_a",
    action="store_true",
    default=False,
    help="Apply Newton Stage-A stabilization profile (survival-first curriculum).",
)
parser.add_argument("--pretrained_checkpoint", type=str, default=None, help="BHL biped 등 사전 학습된 체크포인트 경로")
parser.add_argument(
    "--hylion_usd_path",
    type=str,
    default=None,
    help="학습에 사용할 Hylion USD/USDA 경로. 지정 시 robot_cfg 기본 경로를 override.",
)
parser.add_argument(
    "--stable_walk",
    action="store_true",
    default=False,
    help="안정 보행 파인튜닝 모드 (명령/리셋 랜덤성 축소)",
)
parser.add_argument("--stable_walk_lr", type=float, default=None, help="stable_walk 모드 learning_rate override")
parser.add_argument("--stable_walk_entropy", type=float, default=None, help="stable_walk 모드 entropy_coef override")
parser.add_argument(
    "--stable_walk_schedule",
    type=str,
    default="fixed",
    choices=["adaptive", "fixed"],
    help="stable_walk 모드 PPO schedule",
)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

if args_cli.hylion_usd_path:
    os.environ["HYLION_USD_PATH"] = args_cli.hylion_usd_path

if args_cli.video:
    args_cli.enable_cameras = True

sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import importlib.metadata as metadata
import gymnasium as gym
import pickle
import torch
from datetime import datetime

from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import (
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    multi_agent_to_single_agent,
)
from isaaclab.utils.dict import print_dict
from isaaclab.utils.io import dump_yaml
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# BHL 기본 tasks 등록
import berkeley_humanoid_lite.tasks  # noqa: F401

# Hylion task 등록 (δ3/hylion/__init__.py → gym.register)
sys.path.insert(0, "/home/laba/project_singularity/δ3")
import hylion  # noqa: F401

from isaaclab_newton.physics import NewtonCfg

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.deterministic = False
torch.backends.cudnn.benchmark = False


def dump_pickle(filename: str, data: object):
    if not filename.endswith("pkl"):
        filename += ".pkl"
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def apply_stable_walk_tuning(env_cfg, agent_cfg, lr_override=None, entropy_override=None, schedule_override="fixed"):
    """Apply conservative command/randomization settings for stable walking fine-tuning."""
    print("[INFO] Applying stable-walk fine-tuning configuration")

    base_velocity = env_cfg.commands.base_velocity
    base_velocity.debug_vis = False
    base_velocity.heading_command = False
    base_velocity.rel_heading_envs = 0.0
    base_velocity.rel_standing_envs = 0.0

    ranges = base_velocity.ranges
    ranges.lin_vel_x = (0.05, 0.35)
    ranges.lin_vel_y = (0.0, 0.0)
    ranges.ang_vel_z = (0.0, 0.0)
    if hasattr(ranges, "heading"):
        ranges.heading = (0.0, 0.0)

    # Reduce random reset disturbances so the policy can re-learn a stable gait first.
    if hasattr(env_cfg.events, "reset_base") and env_cfg.events.reset_base is not None:
        env_cfg.events.reset_base.params = {
            "pose_range": {"x": (-0.1, 0.1), "y": (-0.1, 0.1), "yaw": (-0.2, 0.2)},
            "velocity_range": {
                "x": (-0.1, 0.1),
                "y": (-0.1, 0.1),
                "z": (0.0, 0.0),
                "roll": (-0.1, 0.1),
                "pitch": (-0.1, 0.1),
                "yaw": (-0.1, 0.1),
            },
        }

    if hasattr(env_cfg.events, "base_external_force_torque"):
        env_cfg.events.base_external_force_torque = None
    if hasattr(env_cfg.events, "add_base_mass"):
        env_cfg.events.add_base_mass = None

    # Fine-tuning often benefits from a smaller entropy/learning-rate than from-scratch training.
    if hasattr(agent_cfg, "algorithm"):
        target_entropy = 0.006 if entropy_override is None else float(entropy_override)
        target_lr = 5.0e-5 if lr_override is None else float(lr_override)

        if hasattr(agent_cfg.algorithm, "entropy_coef"):
            agent_cfg.algorithm.entropy_coef = target_entropy
        if hasattr(agent_cfg.algorithm, "learning_rate"):
            agent_cfg.algorithm.learning_rate = min(float(agent_cfg.algorithm.learning_rate), target_lr)
        if hasattr(agent_cfg.algorithm, "schedule"):
            agent_cfg.algorithm.schedule = schedule_override


def apply_ppo_overrides(agent_cfg, args_cli):
    """Apply explicit PPO overrides from CLI (useful for Newton-only tuning runs)."""
    if args_cli.override_steps_per_env is not None and hasattr(agent_cfg, "num_steps_per_env"):
        agent_cfg.num_steps_per_env = int(args_cli.override_steps_per_env)

    if hasattr(agent_cfg, "algorithm"):
        if args_cli.override_lr is not None and hasattr(agent_cfg.algorithm, "learning_rate"):
            agent_cfg.algorithm.learning_rate = float(args_cli.override_lr)
        if args_cli.override_entropy is not None and hasattr(agent_cfg.algorithm, "entropy_coef"):
            agent_cfg.algorithm.entropy_coef = float(args_cli.override_entropy)
        if args_cli.override_schedule is not None and hasattr(agent_cfg.algorithm, "schedule"):
            agent_cfg.algorithm.schedule = str(args_cli.override_schedule)


def apply_newton_stage_a_tuning(env_cfg, agent_cfg):
    """Apply conservative Stage-A settings for Newton from-scratch stabilization."""
    print("[INFO] Applying Newton Stage-A stabilization profile")

    # Command curriculum: start with easy forward walking only.
    if hasattr(env_cfg, "commands") and hasattr(env_cfg.commands, "base_velocity"):
        base_velocity = env_cfg.commands.base_velocity
        if hasattr(base_velocity, "debug_vis"):
            base_velocity.debug_vis = False
        if hasattr(base_velocity, "heading_command"):
            base_velocity.heading_command = False
        if hasattr(base_velocity, "rel_heading_envs"):
            base_velocity.rel_heading_envs = 0.0
        if hasattr(base_velocity, "rel_standing_envs"):
            base_velocity.rel_standing_envs = 0.0
        if hasattr(base_velocity, "ranges"):
            ranges = base_velocity.ranges
            if hasattr(ranges, "lin_vel_x"):
                ranges.lin_vel_x = (0.0, 0.35)
            if hasattr(ranges, "lin_vel_y"):
                ranges.lin_vel_y = (0.0, 0.0)
            if hasattr(ranges, "ang_vel_z"):
                ranges.ang_vel_z = (0.0, 0.0)
            if hasattr(ranges, "heading"):
                ranges.heading = (0.0, 0.0)

    # Reset and disturbance randomization: reduce early destabilizers.
    if hasattr(env_cfg, "events"):
        if hasattr(env_cfg.events, "reset_base") and env_cfg.events.reset_base is not None:
            env_cfg.events.reset_base.params = {
                "pose_range": {"x": (-0.1, 0.1), "y": (-0.1, 0.1), "yaw": (-0.2, 0.2)},
                "velocity_range": {
                    "x": (-0.1, 0.1),
                    "y": (-0.1, 0.1),
                    "z": (0.0, 0.0),
                    "roll": (-0.1, 0.1),
                    "pitch": (-0.1, 0.1),
                    "yaw": (-0.1, 0.1),
                },
            }
        if hasattr(env_cfg.events, "base_external_force_torque"):
            env_cfg.events.base_external_force_torque = None
        if hasattr(env_cfg.events, "add_base_mass"):
            env_cfg.events.add_base_mass = None

    # Smaller action scale helps prevent early blow-ups in Newton.
    if hasattr(env_cfg, "actions") and hasattr(env_cfg.actions, "joint_pos"):
        if hasattr(env_cfg.actions.joint_pos, "scale"):
            env_cfg.actions.joint_pos.scale = 0.20

    # PPO defaults for Stage-A if user didn't override via CLI.
    if hasattr(agent_cfg, "num_steps_per_env") and args_cli.override_steps_per_env is None:
        agent_cfg.num_steps_per_env = 24
    if hasattr(agent_cfg, "algorithm"):
        if hasattr(agent_cfg.algorithm, "learning_rate") and args_cli.override_lr is None:
            agent_cfg.algorithm.learning_rate = 8e-4
        if hasattr(agent_cfg.algorithm, "entropy_coef") and args_cli.override_entropy is None:
            agent_cfg.algorithm.entropy_coef = 0.012
        if hasattr(agent_cfg.algorithm, "schedule") and args_cli.override_schedule is None:
            agent_cfg.algorithm.schedule = "fixed"


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlOnPolicyRunnerCfg):
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    apply_ppo_overrides(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs
    agent_cfg.max_iterations = (
        args_cli.max_iterations if args_cli.max_iterations is not None else agent_cfg.max_iterations
    )

    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    if args_cli.stable_walk:
        apply_stable_walk_tuning(
            env_cfg,
            agent_cfg,
            lr_override=args_cli.stable_walk_lr,
            entropy_override=args_cli.stable_walk_entropy,
            schedule_override=args_cli.stable_walk_schedule,
        )

    if args_cli.newton_stage_a:
        apply_newton_stage_a_tuning(env_cfg, agent_cfg)

    # Newton GPU 물리 백엔드
    env_cfg.sim.physics = NewtonCfg()
    env_cfg.events.physics_material = None  # PhysX 전용 API

    log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Logging experiment in directory: {log_root_path}")

    isaaclab_log_dir = os.path.join(log_root_path, "isaaclab")
    os.makedirs(isaaclab_log_dir, exist_ok=True)
    if hasattr(env_cfg.sim, "log_dir"):
        env_cfg.sim.log_dir = isaaclab_log_dir

    log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if agent_cfg.run_name:
        log_dir += f"_{agent_cfg.run_name}"
    log_dir = os.path.join(log_root_path, log_dir)

    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "train"),
            "step_trigger": lambda step: step % args_cli.video_interval == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    env = RslRlVecEnvWrapper(env)

    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, metadata.version("rsl-rl-lib"))

    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    runner.add_git_repo_to_log(__file__)

    if agent_cfg.resume:
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
        print(f"[INFO]: Loading model checkpoint from: {resume_path}")
        runner.load(resume_path)

    # BHL biped 체크포인트에서 시작 (다리 구조 동일, SO-ARM 무게 적응용)
    if args_cli.pretrained_checkpoint:
        print(f"[INFO]: Loading pretrained checkpoint from: {args_cli.pretrained_checkpoint}")
        runner.load(args_cli.pretrained_checkpoint)
        print("[INFO]: Pretrained checkpoint loaded. Fine-tuning with SO-ARM weight...")

    dump_yaml(os.path.join(log_dir, "params", "env.yaml"), env_cfg)
    dump_yaml(os.path.join(log_dir, "params", "agent.yaml"), agent_cfg)
    dump_pickle(os.path.join(log_dir, "params", "env.pkl"), env_cfg)
    dump_pickle(os.path.join(log_dir, "params", "agent.pkl"), agent_cfg)

    runner.learn(num_learning_iterations=agent_cfg.max_iterations, init_at_random_ep_len=True)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
