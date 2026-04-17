"""PPO config for Option A — 세밀한 외력 단계별 적응 (2026-04-17)

C2~C4가 외력 도입 충격으로 실패한 것에 대한 대응.
C1(외력 없음, orientation 3.84%)에서 출발해 외력을 매우 세밀하게 올림.

단계 구성:
  D1: 외력 ±1N  (최초 외력 경험 — 아주 약한 충격)
  D2: 외력 ±2N  (소폭 증가)
  D3: 외력 ±3N  (C2가 실패했던 수준 — 이번엔 충분히 적응 후 진입)
  D4: 외력 ±5N  (중간 강건성)
  D5: 외력 ±10N (최종 목표 강건성)

PPO 전략:
  - 모든 D 스테이지는 LR=5e-5 유지 (catastrophic forgetting 방지 최우선)
  - D1~D2: epochs=2 (Stage C1과 동일 — 보수적 적응)
  - D3~D4: epochs=3 (적응 능력 약간 증가)
  - D5: epochs=4 (최종 강화)
  - clip_param: 0.10 유지 (D4까지), D5에서 0.12로 소폭 증가
  - max_iterations: D1~D2=3000, D3~D4=4000, D5=5000
"""

from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg


@configclass
class HylionPPORunnerCfg_StageD1(RslRlOnPolicyRunnerCfg):
    """Stage D1: base_mass ±0.5kg, 외력 ±1N (최초 외력 경험)"""
    num_steps_per_env = 24
    max_iterations = 3000
    save_interval = 100
    experiment_name = "hylion"
    empirical_normalization = False
    obs_groups = {"policy": ["policy"]}
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=0.5,
        actor_hidden_dims=[256, 128, 128],
        critic_hidden_dims=[256, 128, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.10,             # C1과 동일 유지
        entropy_coef=0.007,
        num_learning_epochs=2,       # C1과 동일 — 안정 우선
        num_mini_batches=4,
        learning_rate=5.0e-5,        # 절대 올리지 않음
        schedule="fixed",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.005,
        max_grad_norm=0.05,
    )


@configclass
class HylionPPORunnerCfg_StageD2(RslRlOnPolicyRunnerCfg):
    """Stage D2: base_mass ±0.5kg, 외력 ±2N"""
    num_steps_per_env = 24
    max_iterations = 3000
    save_interval = 100
    experiment_name = "hylion"
    empirical_normalization = False
    obs_groups = {"policy": ["policy"]}
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=0.5,
        actor_hidden_dims=[256, 128, 128],
        critic_hidden_dims=[256, 128, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.10,
        entropy_coef=0.007,
        num_learning_epochs=2,
        num_mini_batches=4,
        learning_rate=5.0e-5,
        schedule="fixed",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.005,
        max_grad_norm=0.05,
    )


@configclass
class HylionPPORunnerCfg_StageD3(RslRlOnPolicyRunnerCfg):
    """Stage D3: base_mass ±0.5kg, 외력 ±3N (C2가 실패했던 수준 — 재도전)"""
    num_steps_per_env = 24
    max_iterations = 4000           # 더 많은 반복 (이전 실패 교훈)
    save_interval = 100
    experiment_name = "hylion"
    empirical_normalization = False
    obs_groups = {"policy": ["policy"]}
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=0.5,
        actor_hidden_dims=[256, 128, 128],
        critic_hidden_dims=[256, 128, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.10,
        entropy_coef=0.007,
        num_learning_epochs=3,       # epochs 소폭 증가
        num_mini_batches=4,
        learning_rate=5.0e-5,
        schedule="fixed",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.005,
        max_grad_norm=0.05,
    )


@configclass
class HylionPPORunnerCfg_StageD4(RslRlOnPolicyRunnerCfg):
    """Stage D4: base_mass ±1.0kg, 외력 ±5N"""
    num_steps_per_env = 24
    max_iterations = 4000
    save_interval = 100
    experiment_name = "hylion"
    empirical_normalization = False
    obs_groups = {"policy": ["policy"]}
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=0.5,
        actor_hidden_dims=[256, 128, 128],
        critic_hidden_dims=[256, 128, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.10,
        entropy_coef=0.008,
        num_learning_epochs=3,
        num_mini_batches=4,
        learning_rate=5.0e-5,
        schedule="fixed",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.005,
        max_grad_norm=0.05,
    )


@configclass
class HylionPPORunnerCfg_StageD5(RslRlOnPolicyRunnerCfg):
    """Stage D5: base_mass ±1.5kg, 외력 ±10N (최종 강건성 목표)"""
    num_steps_per_env = 24
    max_iterations = 5000
    save_interval = 100
    experiment_name = "hylion"
    empirical_normalization = False
    obs_groups = {"policy": ["policy"]}
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=0.5,
        actor_hidden_dims=[256, 128, 128],
        critic_hidden_dims=[256, 128, 128],
        activation="elu",
    )
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.12,             # 최종 단계에서 소폭 허용
        entropy_coef=0.008,
        num_learning_epochs=4,
        num_mini_batches=4,
        learning_rate=5.0e-5,
        schedule="fixed",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.005,
        max_grad_norm=0.05,
    )
