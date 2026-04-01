# BHL Lowlevel 코드 가이드 — 승민(δ2) 전용

> 나는 승민(δ2), 하이리온 Physical AI 로봇 프로젝트 보행 시스템 오너.
> 이 레포는 NUC에서 돌아가는 BHL 다리 lowlevel 제어 코드다.
> 이 문서를 읽고 코드 질문에 답해줘.

---

## 내 역할 컨텍스트

- **NUC (IPCNUC NUC-1 N95)**: 이 C++ 코드가 실제로 돌아가는 보드
- **Orin**: 상위 제어 (ROS2, 상태 머신) — Orin이 NUC에 UDP로 명령 보냄
- **목표**: NUC에서 Walking RL policy를 250Hz로 실행해서 BHL 다리 12개 관절 제어

---

## 전체 시스템 구조

```
[IsaacLab — NVIDIA GPU]
  RL policy 학습 (수천만 번 시뮬)
        ↓ .onnx 파일
[MuJoCo — sim2sim 검증]
  다른 물리엔진으로 재확인
        ↓ 통과
[Orin — Python]
  run_locomotion.py
  rl_controller.py → ONNX 추론 → 관절 명령 12개
        ↓ UDP (25Hz)
[NUC — C++]
  real_humanoid.cpp → 상태머신
  motor_controller.cpp → CAN 명령
  socketcan.cpp → 실제 전송
        ↓ CAN 버스
[모터 12개]
  왼쪽 6개 (can0) / 오른쪽 6개 (can1)
```

---

## C++ 코드 구조

```
main.cpp
  └─ RealHumanoid.run()
        ├─ initialize()   → CAN 버스 열기, IMU 초기화, UDP 소켓 설정
        └─ 루프 5개 시작:
              loop_control    (100Hz)  ← 핵심: 관절 명령 실행
              loop_udp_recv   (500Hz)  ← policy에서 관절 명령 수신
              loop_imu        (500Hz)  ← IMU 읽기
              loop_keyboard   (20Hz)   ← 키보드 조작
              loop_joystick   (20Hz)   ← 조이스틱 조작
```

---

## 상태 머신 (real_humanoid.cpp)

```
STATE_IDLE
  → 관절 현재 위치 유지 (움직이지 않음)
  → 'r' 키 or UDP mode=2 → STATE_RL_INIT

STATE_RL_INIT
  → 2초에 걸쳐 기본 자세(rl_init_positions)로 천천히 이동
  → 완료 후 't' 키 or UDP mode=3 → STATE_RL_RUNNING

STATE_RL_RUNNING  ← 실제 보행
  → policy가 UDP로 보낸 관절 명령(lowlevel_commands) 그대로 실행
  → 'q' 키 or UDP mode=1 → STATE_IDLE (댐핑 모드로 전환)
```

---

## 통신 구조

```
[Orin — Python policy]                [NUC — C++ lowlevel]
                    ← UDP 10000 ←   관절 상태 35개 float 송신
                    → UDP 10001 →   관절 명령 12개 float 수신
```

### 관절 상태 35개 (NUC → Orin)
```
[0:4]   base_quat        IMU 쿼터니언 (w, x, y, z)
[4:7]   base_ang_vel     IMU 각속도
[7:19]  joint_positions  관절 위치 12개
[19:31] joint_velocities 관절 속도 12개
[31]    state            현재 상태 번호 (1=IDLE, 3=RL_RUNNING 등)
[32:35] command_velocity (vx, vy, vyaw)
```

### 관절 명령 12개 (Orin → NUC)
```
policy가 계산한 목표 관절 위치 12개 (rad)
```

### ⚠️ IP 주소 변경 필요
현재 코드는 127.0.0.1 (같은 머신) 기준. 우리 프로젝트는 Orin↔NUC 분리 구조라서
`csrc/consts.h`의 HOST_IP_ADDR, ROBOT_IP_ADDR을 실제 IP로 변경해야 함.

---

## 관절 순서 (real_humanoid.h)

```
index  이름
  0    left_hip_roll       (can0, CAN ID 1)
  1    left_hip_yaw        (can0, CAN ID 3)
  2    left_hip_pitch      (can0, CAN ID 5)
  3    left_knee_pitch     (can0, CAN ID 7)
  4    left_ankle_pitch    (can0, CAN ID 11)
  5    left_ankle_roll     (can0, CAN ID 13)
  6    right_hip_roll      (can1, CAN ID 2)
  7    right_hip_yaw       (can1, CAN ID 4)
  8    right_hip_pitch     (can1, CAN ID 6)
  9    right_knee_pitch    (can1, CAN ID 8)
  10   right_ankle_pitch   (can1, CAN ID 12)
  11   right_ankle_roll    (can1, CAN ID 14)
```

---

## CAN 통신 구조

### CAN ID 구성 (11비트)
```
[10:7] FUNC_ID (4비트)  |  [6:0] DEVICE_ID (7비트)
```

### PDO vs SDO
- **PDO**: 실시간 제어용. write_pdo_2() = position_target 전송, read_pdo_2() = position_measured 수신
- **SDO**: 초기화용. kp/kd/torque_limit 설정할 때만 씀

### update_joints() 패턴
```
좌우 같은 관절끼리 쌍으로 처리 (can0, can1 동시 전송 가능)
hip → knee → ankle 순서
```

---

## 보정 레이어

```cpp
// 보낼 때
set_target_position((position_target[i] + position_offsets[i]) * joint_axis_directions[i])

// 받을 때
position_measured[i] = get_measured_position() * joint_axis_directions[i] - position_offsets[i]
```

- **position_offsets**: 모터 물리 영점 ↔ 설계 영점 보정 (calibration.yaml)
- **joint_axis_directions**: 방향 반전 보정 (+1/-1)

---

## 안전 레이어 3단계

```
Python   → action_limit 클램핑 (policy 이상 출력 방어)
C++      → torque_limit 세팅, RL_INIT 2초 보간, Ctrl+C → DAMPING
모터 펌웨어 → Watchdog timeout, 과전류/과열/과전압 자동 정지
```

---

## Policy 개념

- **정의**: 관측값(observation) → 행동(action) 을 출력하는 신경망
- **학습**: IsaacLab에서 RL로 수천만 번 시뮬 후 .onnx 파일로 저장
- **입력 (observation)**: command_velocity(3) + base_ang_vel(3) + projected_gravity(3) + joint_pos(12) + joint_vel(12) + prev_actions(12) + history
- **출력 (action)**: 관절 목표 위치 12개 (raw) → action_scale 적용 후 실제 rad 값

---

## Policy 실행 흐름 (scripts/run_locomotion.py)

```python
cfg = Cfg.from_arguments()        # yaml 설정 로드
controller = RlController(cfg)    # policy 준비
controller.load_policy()          # ONNX 모델 로드
robot = Humanoid()                # UDP 소켓 연결
obs = robot.reset()               # 초기 상태 받기

while True:
    actions = controller.update(obs)  # policy 추론 → 관절 명령
    obs = robot.step(actions)         # NUC에 명령 보내고 상태 받기
    rate.sleep()                      # policy_dt 주기 유지
```

- `.pt` (PyTorch) 또는 `.onnx` 둘 다 지원
- 우리는 ONNX 사용 예정

---

## sim2sim (MuJoCo)

```
IsaacLab (학습) → MuJoCo (sim2sim 검증) → NUC 실제 배포
```

- MuJoCo에서 잘 걸으면 실제 로봇도 높은 확률로 됨
- 실행: `python ./scripts/sim2sim/play_mujoco.py --config ./configs/policy_latest.yaml`
- BHL 메인 레포(`Berkeley-Humanoid-Lite`)에 있음, 이 레포 아님

---

## 주요 파일 목록

| 파일 | 역할 |
|------|------|
| `csrc/consts.h` | IP/포트/관절 수 상수 |
| `csrc/real_humanoid.h` | 상태 정의, 관절 enum, 클래스 선언 |
| `csrc/real_humanoid.cpp` | 상태 머신, 제어 루프 구현 |
| `csrc/motor_controller.h/.cpp` | 개별 모터 CAN 통신 |
| `csrc/motor_controller_conf.h` | CAN 패킷 포맷, 모터 모드/에러 정의 |
| `csrc/socketcan.h/.cpp` | CAN 버스 소켓 |
| `csrc/imu.h/.cpp` | IMU 읽기 |
| `berkeley_humanoid_lite_lowlevel/policy/rl_controller.py` | Policy 추론 (ONNX/PT) |
| `berkeley_humanoid_lite_lowlevel/policy/config.py` | yaml 설정 로드 |
| `scripts/run_locomotion.py` | 전체 실행 진입점 |
| `scripts/calibrate_joints.py` | 관절 캘리브레이션 |
| `scripts/check_connection.py` | CAN 연결 확인 |

---

## NUC 세팅 진행 상황

- [x] IPCNUC NUC-1 N95 조립 (DDR4 16GB SO-DIMM + M.2 2280 NVMe SSD)
- [x] Ubuntu 22.04 LTS 설치
- [x] 시스템 업데이트 완료 (`sudo apt update && sudo apt upgrade -y`)
- [x] VS Code 설치 (`sudo snap install --classic code`)
- [ ] xanmod RT 커널 설치
- [ ] CAN-USB 드라이버 활성화 + socketcan 설정
- [ ] cyclictest latency 테스트 (<1ms 목표)
- [ ] ROS2 Humble 설치
- [ ] BHL 코드 클론 + 빌드
