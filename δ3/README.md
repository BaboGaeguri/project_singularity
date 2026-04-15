# δ3 — Hylion v6 보행학습 (2026-04-15 기준)

## 디렉토리 구조

```
δ3/
├── README.md
│
├── hylion/                      ← 학습 환경 설정 (핵심)
│   ├── env_cfg.py               # 기본 환경 (보상/관측/명령 정의)
│   ├── env_cfg_BG.py            # v6 오버라이드 (contact sensor 등)
│   ├── robot_cfg.py             # 기본 로봇 설정
│   ├── robot_cfg_BG.py          # v6 로봇 USD 경로, 관절 설정
│   └── agents/
│       └── rsl_rl_ppo_cfg.py    # PPO 하이퍼파라미터
│
├── scripts/                     ← 현재 사용 중인 스크립트
│   ├── train_hylion_physx_BG.py     # 메인 학습 스크립트
│   ├── train_hylion_physx_BG.sh     # 학습 실행 래퍼
│   ├── train_biped_physx.py         # Stage-A (BHL biped) 학습용
│   ├── run_v6_matrix_experiment.sh  # M1~M6 개별 런처
│   ├── run_v6_matrix_smoke_suite.sh # 공정 비교 스위트
│   ├── monitor_stageb_realtime.sh   # 실시간 로그 모니터
│   ├── auto_guard_hylion_train.sh   # 자동 NaN 감시/롤백
│   └── inspect_hylion_contact_state.py  # contact 상태 진단
│
├── docs/
│   ├── active/                  ← 현재 운영 문서
│   │   ├── 20_v6_command_capability_2026-04-15.md       # 명령 가능 범위
│   │   ├── 21_professor_report_timeline_workflow_2026-04-15.md  # 교수님 보고용
│   │   └── 22_project_structure_and_roles_2026-04-15.md # 전체 구조/역할
│   └── archive/                 ← 완료된 기록 (삭제 금지, 추후 참조용)
│       ├── 00~14_*.md           # 초기 환경 셋업, v3/v4 실험 기록
│       ├── 15~16_*.md           # Stage-B 초기 진행 / NaN 복구 보고
│       ├── 17_*.md              # contact sensor 근본 원인 분석
│       ├── 18_*.md              # v6_flat 단계 전환 전략
│       └── 19_*.md              # 전체 실험 이력 (가장 중요한 기록)
│
├── robot/                       ← 로봇 원본 소스 (URDF, STL, 수정 금지)
└── usd/                         ← δ3 초기 변환 자산 (현재 학습에 미사용)
```

---

## 현재 학습 자산 경로 (중요)

```
✅ 실제 사용 중:
   /home/laba/project_singularity/δ1 & ε2/usd/hylion_v6/hylion_v6.usda

❌ 미사용 (fixed-base 문제로 교체됨):
   /home/laba/project_singularity/δ3/usd/hylion_v6/...
```

---

## 체크포인트 경로

```
Stage-A 기점 (BHL biped):
  ~/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/biped/
    └── 2026-04-06_15-27-27/model_5999.pt   ← 학습 시작점

Stage-B 체크포인트:
  ~/Berkeley-Humanoid-Lite/scripts/rsl_rl/logs/rsl_rl/hylion/
    └── 2026-04-15_.../                     ← 현재 진행 중
```

---

## 실험 설정 매트릭스 (M1~M6)

| 설정 | 상체질량(A) | 액추에이터게인(B) | air_threshold | 단기 결과 |
|------|------------|-----------------|---------------|-----------|
| M1 | 0.0 | 1.0 | 0.2 | PASS, air=0.0009 |
| M2 | 0.0 | 1.2 | 0.2 | PASS, air=0.0016 ← 장기 후보 |
| M3 | 0.3 | 1.0 | 0.2 | PASS, air=0.0014 |
| M4 | 0.3 | 1.2 | 0.2 | PASS, air=0.0018 ← 장기 후보 |
| M5 | 0.6 | 1.2 | 0.2 | PASS, air=0.0012 |
| M6 | 1.0 | 1.2 | 0.2 | PASS, air=0.0014 |

현재: M2 장기 관찰 완료 → **M4 장기 런 진행 중**

---

## 자주 쓰는 명령

```bash
# 학습 시작
cd /home/laba/Berkeley-Humanoid-Lite/scripts/rsl_rl
source /home/laba/env_isaaclab/bin/activate
nohup env PYTHONUNBUFFERED=1 LD_PRELOAD="/lib/aarch64-linux-gnu/libgomp.so.1" \
  python /home/laba/project_singularity/δ3/scripts/train_hylion_physx_BG.py \
  --task Velocity-Hylion-BG-v0 --num_envs 1024 --headless \
  --pretrained_checkpoint [ckpt경로] \
  > /tmp/hylion_v6_physx_[런이름].log 2>&1 &

# 모니터링 (로그 경로는 항상 /tmp 절대경로로)
bash /home/laba/project_singularity/δ3/scripts/monitor_stageb_realtime.sh \
  /tmp/hylion_v6_physx_M4.log 2

# 빠른 확인 (watch)
watch -n 2 "grep -E 'Learning iteration|feet_air_time|Mean action std:|Mean episode length:|nan|Traceback' /tmp/hylion_v6_physx_M4.log | tail -30"

# 학습 프로세스 확인/종료
ls /proc/ | xargs -I{} sh -c \
  'cat /proc/{}/cmdline 2>/dev/null | tr "\0" " " | grep -q "train_hylion" && echo {}' 2>/dev/null
kill [PID들]
```

---

## 판정 기준 (매번 확인)

| 지표 | 정상 | 경계 | 즉시 중단 |
|------|------|------|-----------|
| value/surrogate loss | 유한값 안정 | 급등/급락 반복 | nan |
| action std | > 0.1 | 0.05~0.1 | 0.00 고정 20iter+ |
| feet_air_time | > 0.001 | 0.0001 미만 | 0.0000 고정 150iter+ |
| NaN/Traceback | 0건 | — | 1건이라도 |

---

## 현재 진행 단계 (2026-04-15)

```
완료 ✅  Stage-A 학습 (biped model_5999.pt)
완료 ✅  contact sensor 근본 수정 (USD 교체 + contact_sensor.py 패치)
완료 ✅  M1~M6 공정 비교 (전체 PASS)
완료 ✅  M2 장기 런 관찰
진행 🔄  M4 장기 런
다음 ⏳  M2 vs M4 최종 비교 → 주력 설정 확정
다음 ⏳  command tracking 수치 측정
다음 ⏳  이번 주 데모 제작
```
