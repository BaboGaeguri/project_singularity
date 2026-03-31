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

## hylion_v4.urdf ← 실패

**날짜:** 2026-03-31

**내용:** BHL base mesh에서 어깨 모터 제거 시도

**시도한 것:**
1. Onshape에서 `base_no_actuator_BG` 탭 생성 → Chest 삭제 → STL export
2. 원본 `base_visual.stl` 대신 이 STL 사용
3. **실패 원인:** `onshape-to-robot`이 생성한 STL과 Onshape 직접 export STL의 좌표계가 다름 (x/y축 뒤바뀜)

**추가 시도:**
1. `onshape-to-robot`으로 `base_no_actuator_BG` 탭 추출 → 개별 파트 STL 생성
2. 개별 STL을 trimesh로 merge → 좌표 불일치 지속

**교훈:**
- Onshape 직접 export STL ≠ `onshape-to-robot` STL (좌표계가 다름)
- base mesh 교체 시 동일한 도구(`onshape-to-robot`)로 추출해야 함
- 개별 파트 merge는 원점 문제 해결이 안 됨

---

## 다음 단계

v3 기반으로 이어서 작업. 핵심 과제:
1. BHL 어깨 모터(Chest) 제거된 mesh를 **원본과 동일한 좌표계**로 만드는 방법 확보
2. SO-ARM 위치를 겹침 없는 최종 위치로 확정
3. 연결 브래킷 설계