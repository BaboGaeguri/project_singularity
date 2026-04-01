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

## 소재 조사 (2026-04-01)

`inspect_parts.py --mass`로 Onshape API에서 파트별 소재/질량/밀도 조회.

### BHL — 소재 확인됨

| 소재 | 밀도 (kg/m³) | 용도 |
|------|-------------|------|
| **PLA** | 1,250 | 3D프린팅 구조 부품 (Housing, Mount, Foot 등 대부분) |
| **Aluminum** | 2,700 | 2020 알루미늄 프로파일 (골격) |
| **ABS** | 1,052 | IMU link, 일부 소형 부품 |

> 주의: `Geometry Stud Base`는 밀도 설정 오류 (999,999,999 kg/m³ → mass 785kg). Onshape 설정 실수로 보임.

### SO-ARM (SO-101) — 소재 전부 미지정

모든 파트: `material: "미지정"`, `mass: 0`, `density: 0`
→ SO-101 URDF의 질량은 `onshape-to-robot` config에서 수동 지정된 것으로 추정

---

## SO-ARM Onshape 권한 조사 (2026-04-01)

### SO-ARM100 GitHub Issue #147 확인

- 다른 사용자가 동일한 Copy 권한 요청을 한 상태
- **TheRobotStudio(Pepijn) 답변** (2026-02-06):
  - Copy 권한은 열지 않음
  - 대신 SO-100 파일을 별도 공유: `did: 8c3443ad2476530f652d160f`
  - **SO-101은 HuggingFace가 SO-100을 수정한 버전**임을 밝힘 (케이블 배치 변경 + 하단 pitch 제거)

### SO-100 Copy 후 조사

- SO-100 문서를 Copy하여 `inspect_assembly.py --mates` + `inspect_parts.py --mass` 실행
- **결과**: 소재 전부 미지정, Mate 없음 — 원본에 처음부터 없었음

### SO-100 vs SO-101 체적 비교

| 파트 | 차이 |
|------|------|
| 모터 (STS3215) | 동일 |
| 어깨 회전, 마운팅 플레이트 | ~0.5% 이내 (동일) |
| 상완, 하완, 손목, 그리퍼 | **5~7% 차이** (형상 다름) |
| 베이스 | **파트 분할 방식 자체가 다름** (5배 차이) |

**결론: SO-100을 SO-101 대용으로 사용할 수 없음**

### 방향 재정립

SO-ARM 내부 Mate/소재 정보는 **Onshape 어셈블리에 불필요**함을 확인:
- SO-ARM은 **완제품**으로 구매 → 내부 관절의 Mate 재현 불필요
- 실제 제작에 필요한 것은 **SO-ARM base 외형(STL)** + **BHL 체결 포인트** + **브래킷 설계**
- SO-ARM 외형 STL은 이미 확보됨 (`components/so-arm/assets/`)
- **SO-101 Onshape Copy 권한 요청은 불필요**

---

## Hylion v4 스펙 (2026-04-01)

상세 내용 → `09_hylion_v4_specs.md`

| 항목 | 값 |
|------|-----|
| 총 무게 | 13.89 kg (BHL 공식 16kg보다 2.1kg 가벼움 — 팔 교체 때문) |
| 총 DOF | 24 (다리 12 + 팔 12) |
| 전체 높이 | ~0.82m (발바닥~어깨) |
| 최대 폭 | ~0.24m (어깨 기준) |
| 팔 길이 | ~0.52m (쭉 폈을 때) |

---

## Onshape 어셈블리 배치 시도 (2026-04-01)

### `assembly_hylion.py` — API로 자동 배치

**방법**: Onshape API로 BHL + SO-ARM을 Hylion Assembly에 삽입 + transform 적용

**스크립트 구조**:
1. 기존 instance 전부 삭제
2. BHL 삽입 (원점, 팔 suppress된 복사본 사용)
3. SO-ARM 좌/우 삽입 + 위치/회전 적용

**BHL 팔 suppress**:
- BHL 원본 복사본에서는 suppress 불가 (외부 참조 제한)
- **새 복사본 생성** → Arm L(6), Arm R(6) suppress → 버전 `v2_no_arms` 생성
- BHL 복사본 (팔 suppress): `did: bf0b8ec39be1c3ca659f6306`

**버전 관리 이슈**:
- `get_or_create_version`이 오래된 버전(suppress 전)을 반환하는 문제 발생
- Onshape는 버전을 **오래된순**으로 반환함 (최신이 마지막)
- `get_latest_version`으로 수정 — `metadataWorkspaceId`가 유효한 마지막 버전 사용

**좌표계 차이 문제 (미해결)**:
- URDF 좌표 `(0, ±0.12, 0.82)` + `rpy=(pi, 0, ±pi/2)`를 그대로 Onshape에 적용하면 배치가 어긋남
- **원인**: URDF 좌표계 ≠ Onshape 좌표계 (축 매핑이 다름)
- Onshape Front 뷰 기준: Z=위, X=오른쪽
- 위치를 `tx=±0.12` (X축=좌우)로 수정 → 좌우 배치는 맞음
- **회전이 아직 안 맞음** — SO-ARM이 위로 솟아있고 아래로 안 내려옴
- `roll=PI`, `pitch=PI`, `roll=PI+pitch=PI` 등 시도했으나 미해결
- **다음 단계**: SO-ARM 원본의 Onshape 내부 방향을 정확히 파악한 후 회전 행렬 보정

---

## Document ID

| 문서 | did | wid | eid |
|------|-----|-----|-----|
| **Hylion Assembly** (작업 문서) | `a741aa6d15d9e384d9ffa4d9` | `2105b756950a92f6be143e8a` | `0f1a46cb91bfc8ad1a11b7ea` |
| **BHL 복사본 (원본)** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `8a738ee5d00bb7ca5f8b3bc0` |
| **BHL 복사본 (팔 suppress)** | `bf0b8ec39be1c3ca659f6306` | `560942befdcb6930ea4b7a28` | `f015812d38473d4933b28001` |
| **SO-ARM 복사본** (SO-101, STEP import) | `32d468d3a6994ea4b9d0cfa1` | `4702c8115f56790e62e507c5` | `61ca4b83d9996a40877b20fc` |
| **BHL base (모터 제거)** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `719459ab4fd197d947f11217` |
| **SO-100 원본** (TheRobotStudio 공유) | `8c3443ad2476530f652d160f` | `cbfc0795034ec0eb76266c9e` | `8b1be6bb4110bea74c27dbdc` |
| **SO-100 Copy** (우리 복사본) | `777450bd9cf2ea12995524af` | `21332a10decdb024c210faae` | `4a47bf70b89df2ec8aa69f12` |

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
- [x] Onshape 파트별 소재/질량 조사 (BHL: PLA+AL, SO-ARM: 미지정) ✅ 2026-04-01
- [x] SO-ARM Onshape 권한 조사 → SO-100 Copy + 비교 → **내부 Mate 불필요 확인** ✅ 2026-04-01
- [x] Hylion v4 스펙 정리 → `09_hylion_v4_specs.md` ✅ 2026-04-01
- [x] BHL 팔 suppress + 새 복사본 생성 ✅ 2026-04-01
- [x] `assembly_hylion.py` v4 기준 업데이트 (회전 행렬 추가) ✅ 2026-04-01
- [ ] **Onshape SO-ARM 회전 보정** — URDF↔Onshape 좌표계 차이 해결
- [ ] **URDF v4 시각화 검증 — 충돌 여부 확인**
- [ ] **연결 브래킷 설계** — SO-ARM base 외형 + BHL 체결 포인트 기반
- [ ] 머리/목 파트 설계 및 추가
- [ ] 간섭 체크 (시뮬레이터에서)
- [ ] 배치 확정 후 Export

조회/배치 스크립트:
- `inspect_assembly.py` → `onshape/{target}_dump.json`
- `inspect_parts.py` → `onshape/{target}_parts.json`, `{target}_mass.json`
- `check_versions.py` → 문서별 버전 목록 확인
- `assembly_hylion.py` → Hylion Assembly에 BHL + SO-ARM 자동 배치

---

## 해볼 것
- onshape에 so-arm이 제대로 그려지지 않는 원인이 뭘까
- SO-ARM의 Onshape 내부 좌표축 방향을 inspect로 확인 필요