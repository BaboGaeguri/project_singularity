# Hylion URDF 버전 기록

---

## hylion_v1.urdf

**날짜:** 2026-03-31

**내용:** BHL + SO-ARM 최초 합치기

**변경사항:**
- BHL URDF에서 기존 팔(arm) link/joint 제거 (좌우 각 5 DOF + fixed 1)
- SO-ARM 좌/우 link/joint 체인을 BHL base에 fixed joint로 연결
- SO-ARM link/joint 이름에 `soarm_left_` / `soarm_right_` prefix 추가

**SO-ARM 연결:**
- 위치: `(0, ±0.133, 0.764)` — BHL 원본 팔 어깨 joint 위치
- 방향: `rpy=(0, 0, 0)`

**문제:** SO-ARM이 BHL 토르소 내부에 겹침

---

## hylion_v2.urdf

**날짜:** 2026-03-31

**내용:** 위치를 Onshape API mate 데이터 기반으로 수정

**SO-ARM 연결:**
- 위치: `(-0.028, ±0.08, 0.544)` — BHL Actuator-6512 월드 좌표
- 방향: `rpy=(0, 0, 0)`
- 근거: `bhl_dump.json` occurrence transform

**문제:** SO-ARM이 BHL 토르소를 관통

---

## hylion_v3.urdf ← 현재 가장 나은 상태

**날짜:** 2026-03-31

**내용:** SO-ARM을 뒤집어서 팔이 아래로 늘어뜨려지게 변경

**SO-ARM 연결:**
- 위치: `(0, ±0.10, 0.544)` — 토르소 외벽 바깥 (y 반폭 0.07 + 0.03 여유)
- 방향: `rpy=(3.14159, 0, 0)` — x축 180도 회전, 팔이 아래로

**결과:** 팔 방향은 좋음. BHL 어깨 모터(Chest)와 SO-ARM base가 아직 겹침

---

## hylion_v4.urdf (이전 시도 — 실패)

**날짜:** 2026-03-31

**내용:** BHL base mesh에서 어깨 모터 제거 시도

**시도한 것:**
1. Onshape에서 `base_no_actuator_BG` 탭 생성 → Chest 삭제 → STL export
2. 원본 `base_visual.stl` 대신 이 STL 사용
3. **실패 원인:** `onshape-to-robot`이 생성한 STL과 Onshape 직접 export STL의 좌표계가 다름 (x/y축 뒤바뀜)

**교훈:**
- Onshape 직접 export STL ≠ `onshape-to-robot` STL (좌표계가 다름)
- base mesh 교체 시 동일한 도구(`onshape-to-robot`)로 추출해야 함

---

## hylion_v4.urdf (재작성) ← 현재

**날짜:** 2026-04-01

**내용:** 방향 전환 — Chest 제거를 포기하고, 원본 `base_visual.stl`을 그대로 사용. SO-ARM을 토르소 상단 양 옆에 충돌 없이 배치.

**전략:**
- BHL base mesh: `base_visual.stl` 원본 그대로 (Chest 포함)
- BHL base collision box: x=±0.075, y=±0.07, z=0.595~0.825
- SO-ARM을 collision box **밖**에 배치

**SO-ARM 연결 (좌):**
- 위치: `(0, +0.12, 0.82)` — y=0.12는 box 외벽(0.07)에서 0.05m 여유
- 방향: `rpy=(pi, 0, pi/2)` — 뒤집어서 팔이 아래로, 90도 회전하여 팔이 옆으로 뻗음

**SO-ARM 연결 (우):**
- 위치: `(0, -0.12, 0.82)` — 좌우 대칭
- 방향: `rpy=(pi, 0, -pi/2)` — 좌우 미러

**구성:**
- BHL 다리: 12 DOF (좌6 + 우6) — 원본 그대로
- SO-ARM 팔: 12 DOF (좌6 + 우6) — shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
- IMU: 원본 그대로
- 총 DOF: 24 (능동 관절)

**link/joint 이름 규칙:**
- 좌: `soarm_left_` prefix
- 우: `soarm_right_` prefix

---

## hylion_v5.urdf

**날짜:** 2026-04-02

**내용:** v4에서 SO-ARM 위치/방향 조정 + shoulder_lift 초기 포즈 변경

**변경사항:**
- SO-ARM z 위치: `0.82` → `0.71` (collision box 중심)
- SO-ARM base_joint rpy: 시행착오를 거쳐 `(0, pi/2, ±pi/2)`로 설정
- shoulder_lift 초기 포즈: `rpy=(-pi/2, -pi/2, 0)` → `rpy=(-pi/2, 0, 0)` — ㄱ자 꺾임을 차렷 자세로 변경

**교훈:**
- revolute joint의 origin rpy에서 axis에 해당하는 성분(yaw)만 바꾸면 모터 방향으로 초기 포즈 변경 가능
- axis에 해당하지 않는 성분을 바꾸면 파트 분리 위험
- fixed joint의 rpy는 자유롭게 변경 가능
- 상세 규칙 → `08_coordinate_transform.md`

---

## hylion_v6.urdf ← 현재

**날짜:** 2026-04-02

**내용:** v5 + 어깨 구조물(3kg box) 양쪽 추가

**변경사항:**
- base와 SO-ARM base_link 사이에 구조물 box 추가 (좌/우 각 1개)
- 구조물 사양: 0.08 × 0.05 × 0.15m, 3kg, 회색
- 위치: `(0, ±0.095, 0.71)` — base 외벽(y=0.07)과 SO-ARM(y=0.12) 중간
- fixed joint로 base에 고정

**구성:**
- BHL 다리: 12 DOF
- SO-ARM 팔: 12 DOF
- 어깨 구조물: 좌우 3kg × 2 = 6kg
- IMU
- 총 DOF: 24 (능동 관절)
- 총 무게: 13.89 + 6.0 = **~19.89 kg**

---

## 다음 단계

1. URDF v6 시각화 검증
2. 구조물 크기/무게 조정
3. 머리/목 파트 설계 및 추가
4. 간섭 체크