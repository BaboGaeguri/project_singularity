# Hylion 어셈블리 작업 기록

> BHL(하체) + SO-ARM(팔)을 조합하여 Hylion 로봇을 구성하는 작업 기록
> 환경 세팅 → `01_onshape_setup_guide.md` | API 레퍼런스 → `02_onshape_api_guide.md`

---

## 전체 플로우

```
[1] 환경 세팅 (문서 확보, API key, venv)                 ✅ 완료 → 01_onshape_setup_guide.md
[2] Onshape 어셈블리 배치 스크립트                       ✅ 완료 (중복 삽입 해결됨)
[3] Assembly 상태 조회 + 정리                            ✅ 완료 (2026-03-31)
[4] URDF vs Onshape 일치 검증                            ✅ 완료 — 둘 다 일치 확인
[5] URDF 기반 Hylion 합치기                              ✅ v1~v4 진행 (v4가 현재 가장 나은 상태)
[6] Mesh 파일 확보                                       ✅ 완료
[7] BHL base mesh에서 어깨 모터 제거                     ❌ 포기 — 원본 mesh 그대로 사용으로 전환
[8] URDF 시각화 검증                                     ⚠️ 반복 수정 중
[9] 간섭 체크 + 배치 확정                                🔲 미수행
[10] Export (STEP / URDF)                                🔲 미수행
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

## Mesh 파일 확보 (2026-03-31)

### 확보 방법
- **BHL mesh**: 프로젝트에 원래 포함 (`components/berkeley_humanoid_lite/mesh/`)
- **SO-ARM mesh**: `onshape-to-robot`으로 SO-ARM 복사본에서 추출 (`components/so-arm/assets/`)
- **모터 (STS3215)**: `onshape-to-robot`이 자동 추출 + GrabCAD에서 STEP 다운로드 → STL 변환
- **3D 프린팅용 STL**: LeRobot 문서 링크에서 다운로드 (`components/so-arm/mesh/Individual/`)

### 주의
- **3D 프린팅용 STL과 URDF용 mesh는 원점이 다름** — URDF에는 `assets/` 폴더 파일 사용
- **Onshape 직접 export한 STL과 `onshape-to-robot` STL도 좌표계가 다름** (축이 뒤바뀜)
- URDF용 mesh는 반드시 `onshape-to-robot`으로 추출한 것을 사용해야 함

---

## BHL base 내부 구조 (Onshape API 조회, 2026-03-31)

### Mate 정보 (`bhl_dump.json`, includeMateFeatures=true)
- 루트 어셈블리: FASTENED 4개 + REVOLUTE 22개
- base 서브어셈블리 내부: FASTENED 10개 이상 (프로파일, NUC, 배터리 등)
- **체결 구조가 완전히 구현되어 있음**

### BHL 어깨 모터 위치 (Actuator-6512, Mate Arm L/R)
- 좌: `(x=-0.028, y=0.08, z=0.544)` — base 서브어셈블리 하단 근처
- 우: `(x=-0.028, y=-0.08, z=0.544)`
- 이 모터는 **Chest 서브어셈블리** 안에 포함

### BHL collision box
- 크기: 150×140×230mm
- 중심: z=0.71
- 범위: x=±0.075, y=±0.07, z=0.595~0.825

---

## URDF 버전 이력

상세 내용 → `urdf/versions.md`

### v1 — 최초 합치기
- BHL 기존 팔 제거 + SO-ARM 연결
- 위치: `(0, ±0.133, 0.764)` — BHL 원본 팔 어깨 위치
- **문제**: SO-ARM이 BHL 토르소와 겹침

### v2 — 위치를 Onshape API 데이터 기반으로 수정
- 위치: `(-0.028, ±0.08, 0.544)` — Actuator-6512 월드 좌표
- **문제**: SO-ARM이 BHL 토르소를 관통

### v3 — SO-ARM 방향 회전 (현재 가장 나은 상태)
- 방향: `rpy=(pi, 0, 0)` — SO-ARM을 뒤집어서 팔이 아래로 늘어뜨려짐
- 위치: `(0, ±0.10, 0.544)` — 토르소 외벽 바깥
- **문제**: BHL 어깨 모터(Chest)와 SO-ARM base가 여전히 겹침

### v4 — 원본 base mesh + SO-ARM 충돌 회피 배치 (2026-04-01)
- **방향 전환**: Chest 제거를 포기하고, 원본 `base_visual.stl` 그대로 사용
- **SO-ARM 배치**: 토르소 상단 양 옆, collision box 밖에 배치
  - 좌: `(0, +0.12, 0.82)`, `rpy=(pi, 0, pi/2)` — 뒤집어서 팔이 아래로, 옆으로 뻗음
  - 우: `(0, -0.12, 0.82)`, `rpy=(pi, 0, -pi/2)` — 좌우 대칭
- **총 DOF**: 24 (다리 12 + 팔 12)
- **상태**: 시각화 검증 필요

### 핵심 미해결 문제
1. **URDF 시각화 검증** — v4가 실제로 겹침 없이 올바르게 보이는지 확인
2. **SO-ARM 마운트 위치 미세 조정** — 시각화 결과에 따라 xy/z 조정
3. **연결 브래킷 설계** — 실제 체결을 위한 추가 구조물

---

## Document ID

| 문서 | did | wid | eid |
|------|-----|-----|-----|
| **Hylion Assembly** (작업 문서) | `a741aa6d15d9e384d9ffa4d9` | `2105b756950a92f6be143e8a` | `bff9221de0592d13a616f0f2` |
| **BHL 복사본** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `8a738ee5d00bb7ca5f8b3bc0` |
| **SO-ARM 복사본** | `32d468d3a6994ea4b9d0cfa1` | `4702c8115f56790e62e507c5` | `61ca4b83d9996a40877b20fc` |
| **BHL base (모터 제거)** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `719459ab4fd197d947f11217` |

---

## TODO

- [x] 중복 BHL instance 삭제 ✅ 2026-03-31
- [x] URDF vs Onshape 일치 검증 ✅ 2026-03-31
- [x] BHL URDF에서 기존 팔 제거 ✅ 2026-03-31
- [x] SO-ARM URDF 체인을 BHL base에 연결 (v1) ✅ 2026-03-31
- [x] SO-ARM mesh 파일 확보 (onshape-to-robot) ✅ 2026-03-31
- [x] 모터 STL 확보 (GrabCAD + STEP→STL 변환) ✅ 2026-03-31
- [x] BHL Onshape mate 데이터 조회 ✅ 2026-03-31
- [x] ~~BHL base mesh 어깨 모터 제거~~ → 포기, 원본 mesh 사용으로 전환 ✅ 2026-04-01
- [x] SO-ARM 마운트 위치/방향 설정 (v4: 토르소 상단 외벽 배치) ✅ 2026-04-01
- [ ] **URDF v4 시각화 검증 — 충돌 여부 확인**
- [ ] 연결 브래킷 설계
- [ ] URDF 시각화 검증 통과
- [ ] SO-ARM 원본 Onshape 권한 요청 (병렬)
- [ ] 간섭 체크
- [ ] 배치 확정 후 Export

조회 스크립트: `inspect_assembly.py` → 결과 JSON: `onshape/hylion_dump.json`, `soarm_dump.json`, `bhl_dump.json`

---