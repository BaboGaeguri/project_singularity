# Hylion v4 URDF 무게 및 치수 정리

> URDF 파일: `urdf/hylion_v4.urdf` 기준
> 작성일: 2026-04-01

---

## 구성 요약

| 항목 | 내용 |
|------|------|
| 로봇 이름 | hylion |
| BHL base mesh | `base_visual.stl` (원본, Chest 포함) |
| 다리 | BHL 원본 그대로 (좌6 + 우6 = 12 DOF) |
| 팔 | SO-ARM 101 × 2 (좌6 + 우6 = 12 DOF) |
| 총 DOF | 24 (능동 관절) |
| 총 무게 | **13.89 kg** |

---

## 무게 상세

### 몸통 / 센서

| Link | 질량 (kg) |
|------|-----------|
| base | 4.444 |
| imu_2 | 0.002 |
| imu (dummy) | ~0 |
| **소계** | **4.446** |

### 왼다리

| Link | 질량 (kg) |
|------|-----------|
| leg_left_hip_roll | 0.838 |
| leg_left_hip_yaw | 0.838 |
| leg_left_hip_pitch | 0.948 |
| leg_left_knee_pitch | 0.654 |
| leg_left_ankle_pitch | 0.106 |
| leg_left_ankle_roll | 0.706 |
| **소계** | **4.090** |

### 오른다리 (좌와 동일)

| **소계** | **4.090** |
|------|-----------|

### 왼팔 (SO-ARM)

| Link | 질량 (kg) |
|------|-----------|
| soarm_left_base_link | 0.147 |
| soarm_left_shoulder_link | 0.100 |
| soarm_left_upper_arm_link | 0.103 |
| soarm_left_lower_arm_link | 0.104 |
| soarm_left_wrist_link | 0.079 |
| soarm_left_gripper_link | 0.087 |
| soarm_left_moving_jaw_link | 0.012 |
| **소계** | **0.632** |

### 오른팔 (좌와 동일)

| **소계** | **0.632** |
|------|-----------|

### 부위별 총합

| 부위 | 질량 (kg) | 비율 |
|------|-----------|------|
| 몸통 (base + IMU) | 4.446 | 32% |
| 다리 (좌+우) | 8.180 | 59% |
| 팔 (좌+우) | 1.264 | 9% |
| **합계** | **13.89 kg** | 100% |

> 참고: BHL 원본 공식 스펙은 16kg. 차이(~2.1kg)는 배터리/전자부품 등 URDF에 별도 모델링되지 않은 부분으로 추정.

---

## 전체 치수

### 높이 (Z축)

| 구간 | Z 좌표 (m) | 근거 |
|------|-----------|------|
| 발바닥 | ~0.18 | ankle_roll collision box 하단 |
| 발목 | ~0.33 | joint offset 역산 |
| 무릎 | ~0.38 | knee joint |
| 골반 (hip) | 0.54 | leg_hip_roll joint z |
| 토르소 하단 | 0.595 | collision box 하단 |
| 토르소 중심 | 0.675 | base 무게중심 z |
| 토르소 상단 | 0.825 | collision box 상단 |
| SO-ARM 어깨 | 0.82 | base joint z |
| **전체 높이** | **~0.82m** | 발바닥~어깨 |

### 폭 (Y축)

| 구간 | 범위 (m) |
|------|----------|
| 토르소 | ±0.07 (collision box) |
| 골반 (hip) | ±0.08 (hip_roll joint y) |
| SO-ARM 어깨 | ±0.12 (base joint y) |
| **최대 폭** | **~0.24m** (어깨 기준) |

### 깊이 (X축)

| 구간 | 범위 (m) |
|------|----------|
| 토르소 | ±0.075 (collision box) |
| **최대 깊이** | **~0.15m** |

### 팔 길이 (SO-ARM, 쭉 폈을 때)

| 구간 | 길이 (m) | 근거 |
|------|----------|------|
| base → shoulder | 0.062 | shoulder_pan joint z offset |
| shoulder → upper_arm | 0.054 | shoulder_lift joint z offset |
| upper_arm → lower_arm | 0.113 | elbow_flex joint x offset |
| lower_arm → wrist | 0.135 | wrist_flex joint x offset |
| wrist → gripper | 0.061 | wrist_roll joint y offset |
| gripper → tip | 0.098 | gripper_frame joint z offset |
| **팔 전체** | **~0.52m** | |

---

## SO-ARM 마운트 위치

| | 위치 (xyz) | 방향 (rpy) |
|---|---|---|
| 좌팔 | (0, +0.12, 0.82) | (pi, 0, pi/2) |
| 우팔 | (0, -0.12, 0.82) | (pi, 0, -pi/2) |

- y=0.12: collision box 외벽(y=0.07)에서 5cm 여유
- z=0.82: 토르소 상단(z=0.825) 근처
- rpy=(pi,0,...): 뒤집어서 팔이 아래로 늘어뜨려짐

---

## 관절 스펙

### 다리 관절 (BHL, 좌우 동일)

| 관절 | 토크 (Nm) | 속도 (rad/s) | 가동범위 (rad) | 가동범위 (도) |
|------|-----------|-------------|---------------|-------------|
| hip_roll | 20 | 15 | -0.17 ~ 1.57 | -10 ~ 90 |
| hip_yaw | 20 | 15 | -0.98 ~ 0.59 | -56 ~ 34 |
| hip_pitch | 20 | 15 | -1.90 ~ 0.98 | -109 ~ 56 |
| knee_pitch | 20 | 15 | 0 ~ 2.44 | 0 ~ 140 |
| ankle_pitch | 20 | 15 | -0.79 ~ 0.79 | -45 ~ 45 |
| ankle_roll | 20 | 15 | -0.26 ~ 0.26 | -15 ~ 15 |

### 팔 관절 (SO-ARM, 좌우 동일)

| 관절 | 토크 (Nm) | 속도 (rad/s) | 가동범위 (rad) | 가동범위 (도) |
|------|-----------|-------------|---------------|-------------|
| shoulder_pan | 10 | 10 | -1.92 ~ 1.92 | -110 ~ 110 |
| shoulder_lift | 10 | 10 | -1.75 ~ 1.75 | -100 ~ 100 |
| elbow_flex | 10 | 10 | -1.68 ~ 1.68 | -96 ~ 96 |
| wrist_flex | 10 | 10 | -1.66 ~ 1.66 | -95 ~ 95 |
| wrist_roll | 10 | 10 | -2.74 ~ 2.84 | -157 ~ 163 |
| gripper | 10 | 10 | -0.17 ~ 1.75 | -10 ~ 100 |

---

## 킨매틱 트리

```
base
├── imu_2 (fixed) → imu (fixed)
├── soarm_left_base_link (fixed)
│   └── shoulder_pan → shoulder_lift → upper_arm
│       → elbow_flex → lower_arm → wrist_flex → wrist
│         → wrist_roll → gripper → gripper_frame (fixed)
│                                → moving_jaw (revolute)
├── soarm_right_base_link (fixed)
│   └── (좌와 대칭 구조)
├── leg_left_hip_roll (revolute)
│   └── hip_yaw → hip_pitch → knee_pitch → ankle_pitch → ankle_roll
└── leg_right_hip_roll (revolute)
    └── (좌와 대칭 구조)
```