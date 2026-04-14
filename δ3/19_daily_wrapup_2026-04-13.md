# 오늘 작업 정리 (2026-04-13)

## 1) 오늘 결론

- Stage-B 학습은 일단 중지 완료.
- `feet_air_time`이 계속 0으로 나오는 문제를 중심으로 원인 분리/복구를 진행함.
- 내일은 매트릭스 실험(M1 -> M2 순서)로 단계적으로 재개하면 됨.

## 2) 오늘 한 핵심 작업

1. contact sensor/asset 관련 근본 원인 정리
2. NaN 재발/복구 이력 문서화
3. v6_flat 전환 전략 문서화
4. 실험 매트릭스 실행 가능하도록 코드 반영

## 3) 코드/스크립트 변경

- `δ3/hylion/env_cfg_BG.py`
  - 런타임 실험 파라미터 추가:
    - `HYLION_FEET_AIR_THRESHOLD`
    - `HYLION_LEG_GAIN_SCALE`
    - `HYLION_BASE_MASS_ADD_KG`
- `δ3/scripts/run_v6_matrix_experiment.sh` (신규)
  - M1~M6 조합을 바로 실행하는 런처

## 4) 문서 정리 위치

- NaN 복구 보고서: `δ3/16_stageB_nan_recovery_report_2026-04-09.md`
- contact sensor 근본원인: `δ3/17_stageB_contact_sensor_root_cause_2026-04-13.md`
- v6_flat 실행 계획: `δ3/18_v6_flat_training_plan_2026-04-13.md`

## 5) 현재 상태

- Stage-B 프로세스: 중지됨
- 마지막 시도: M1 (`/tmp/hylion_v6_physx_M1.log`)
- 관측: 학습 루프/손실은 유한값 유지, `feet_air_time`은 아직 0.0000

## 6) 내일 바로 시작 순서 (짧은 버전)

1. M1 재실행 또는 이어서 판정
2. 문서 기준 PASS/FAIL 판정
3. M2 실행

실행 명령:

```bash
bash /home/laba/project_singularity/δ3/scripts/run_v6_matrix_experiment.sh M1
```

모니터 명령:

```bash
bash /home/laba/project_singularity/δ3/scripts/monitor_stageb_realtime.sh /tmp/hylion_v6_physx_M1.log 2
```

## 7) 내일 체크 포인트

1. `Mean value loss`, `Mean surrogate loss` NaN 여부
2. `Mean action std`가 0.00으로 붕괴하는지
3. `Episode_Reward/feet_air_time` 비영값 출현 여부

## 8) 메모

- 오늘은 중지 요청에 따라 학습 중단만 수행했고, 추가 실험은 진행하지 않음.
