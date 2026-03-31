# Hylion 어셈블리 작업 기록

> BHL(하체) + SO-ARM(팔)을 조합하여 Hylion 로봇을 구성하는 작업 기록
> 환경 세팅 → `onshape_setup_guide.md` | API 레퍼런스 → `onshape_api_guide.md`

---

## 전체 플로우

```
[1] 환경 세팅 (문서 확보, API key, venv)                 ✅ 완료 → onshape_setup_guide.md
[2] Onshape 어셈블리 배치 스크립트                       ✅ 완료 (중복 삽입 해결됨)
[3] Assembly 상태 조회 + 정리                            ✅ 완료 (2026-03-31)
[4] URDF vs Onshape 일치 검증                            ✅ 완료 — 둘 다 일치 확인
[5] URDF 기반 Hylion 합치기                              🔲 진행 예정
[6] 간섭 체크 + 배치 확정                                🔲 미수행
[7] Export (STEP / URDF)                                 🔲 미수행
```

---

## 방향 전환 (2026-03-31)

### 문제
SO-ARM 원본 Onshape 문서가 view only (소유자: Pepijn / HuggingFace LeRobot)로
Copy workspace 불가 → STEP import 시 **mate 정보 소실** → 어셈블리에서 파트가 뭉침

### 결정
- **Onshape 어셈블리 방식 → URDF 기반 합치기로 전환**
- 각각의 URDF는 원본 Onshape에서 `onshape-to-robot`으로 생성된 것이므로 원본과 동일
- Onshape 어셈블리는 시각적 확인용으로만 유지

### SO-ARM 원본 권한 요청 (병렬 진행)
- 소유자: **Pepijn Kooijmans** (HuggingFace)
- GitHub: `pkooij` / X: `@pepijn2233` / HF: `pepijn223`
- Copy workspace 권한 요청 → 실제 로봇 제작 시 필요

---

## URDF 검증 결과 (2026-03-31)

### SO-ARM

| 항목 | 결과 |
|------|------|
| 파트 완전성 | 완전 일치 — Onshape 17개 instance = URDF 17개 mesh |
| 파트 이름 | 일치 (대소문자 차이만 존재) |
| 위치 데이터 | 일치 — base_link 내 파트 좌표 소수점까지 동일 |
| 관절 | 6 DOF (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper) |

### BHL

| 항목 | 결과 |
|------|------|
| Link/Instance 수 | URDF 27개 / Onshape 26개 (imu dummy link +1) |
| 파트 이름 | 25/26 일치 (imu만 이름 변형) |
| 구동 DOF | 22개 — 팔 10(좌5+우5) + 다리 12(좌6+우6) |
| Base 높이 | z=0.675m (직립 시 torso 중심) |

---

## Document ID

| 문서 | did | wid | eid |
|------|-----|-----|-----|
| **Hylion Assembly** (작업 문서) | `a741aa6d15d9e384d9ffa4d9` | `2105b756950a92f6be143e8a` | `bff9221de0592d13a616f0f2` |
| **BHL 복사본** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `8a738ee5d00bb7ca5f8b3bc0` |
| **SO-ARM 복사본** | `32d468d3a6994ea4b9d0cfa1` | `4702c8115f56790e62e507c5` | `61ca4b83d9996a40877b20fc` |

---

## URDF 합치기 계획

### 작업 내용
1. BHL URDF에서 **기존 팔(arm) link/joint 제거** (좌우 각 5 DOF)
2. SO-ARM의 link/joint 체인을 BHL base에 **연결**
3. 연결 지점: BHL base의 `(0, ±0.133, 0.764)` (기존 팔 어깨 위치)

### BHL 제거 대상 (좌측)
- link: arm_left_shoulder_pitch, shoulder_roll, shoulder_yaw, elbow_pitch, elbow_roll, hand_link
- joint: arm_left_shoulder_pitch_joint ~ hand_l (5 revolute + 1 fixed)
- 우측도 동일

### SO-ARM 연결 체인
base_link → shoulder → upper_arm → lower_arm → wrist → gripper → moving_jaw

### 주의사항
- 각각의 URDF는 검증 완료된 원본 — 수정하지 않음
- 우리가 건드리는 부분은 **연결부(BHL base ↔ SO-ARM base)만**
- 연결부의 좌표/회전은 BHL 기존 팔 어깨 위치 기반으로 설정

---

## TODO

- [x] 중복 BHL instance 삭제 ✅ 2026-03-31
- [x] URDF vs Onshape 일치 검증 ✅ 2026-03-31
- [ ] BHL URDF에서 기존 팔 제거
- [ ] SO-ARM URDF 체인을 BHL base에 연결
- [ ] 합친 URDF 시뮬레이션 검증
- [ ] SO-ARM 원본 Onshape 권한 요청 (병렬)
- [ ] 간섭 체크
- [ ] 배치 확정 후 Export

조회 스크립트: `inspect_assembly.py` → 결과 JSON: `onshape/hylion_dump.json`, `soarm_dump.json`, `bhl_dump.json`