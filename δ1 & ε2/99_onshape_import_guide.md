# STEP 파일 → OnShape 업로드 가이드

> 하이리온 로봇 CAD (`hylion_cad.py`) 실행 후 생성된 STEP 파일을 OnShape에 올리는 방법

---

## 0. 사전 준비 — STEP 파일 생성

### Python 환경 세팅 (최초 1회)

```
# Python 3.11 설치 필요 (3.14는 CadQuery 미지원)
# python.org → Python 3.11.9 Windows installer (64-bit) 다운로드
# 설치 시 "Add python.exe to PATH" 반드시 체크

python -m pip install cadquery
```

### STEP 파일 생성

VSCode 터미널(`Ctrl + ~`)에서:

```
python hylion_cad.py
```

**출력 파일 (step_files/ 폴더):**

| 파일 | 내용 |
|------|------|
| `hylion_head.step` | 머리 외피 + 내부 부품 블록 (OAK-D Lite, MG90S 등) |
| `hylion_torso.step` | 토르소 외피 + 내부 부품 블록 (배터리, NUC, Orin 등) |
| `hylion_pelvis.step` | 골반 외피 (BHL URDF 기반) |
| `hylion_leg.step` | 단측 다리 외피 (OnShape에서 미러링 → 양쪽) |

---

## 1. OnShape에 STEP 파일 올리기

### 1-1. OnShape 접속

- [onshape.com](https://onshape.com) 접속 → 로그인
- 기존 문서 열기 또는 새 문서 생성

### 1-2. Import

우측 상단 **`Import`** 버튼 클릭

> ⚠️ **주의:** OnShape UI 하단 탭의 `+` 버튼은 FeatureScript/Assembly 탭 추가용이므로 사용 안 함

파일 선택 창에서 `step_files/` 폴더 안의 파일 선택
- 4개 동시 선택 가능 (Shift 또는 Ctrl 클릭)

Import 완료 후 하단 탭에 각 파일이 별도 Part Studio로 생성됨:
```
hylion_head | hylion_torso | hylion_pelvis | hylion_leg | Assembly 1
```

### 1-3. 부품 확인

각 탭 클릭 → 3D 뷰어에서 확인

**색상 범례 (OnShape 파트 트리에서 부품명 확인):**

| 색상 | 부품명 | 설명 |
|------|--------|------|
| 회색 | `head_shell` / `torso_shell` | 외피 쉘 |
| 파랑 | `OAK-D_left` / `OAK-D_right` | OAK-D Lite 카메라 |
| 주황 | `MG90S_servo` | 입 서보 |
| 검정 | `speaker_20mm` | 스피커 |
| 초록 | `PAM8403_amp` / `NUC_BeeLink_N95` | 앰프 / NUC |
| 파랑 | `Jetson_Orin` | Orin Nano Super |
| 빨강 | `battery_A_6S` | 배터리 A (6S LiPo) |
| 주황 | `battery_B_12V` | 배터리 B (12V Li-ion) |
| 노랑 | `control_boards` | 제어 보드 레이어 통합 |
| 보라 | `XL430_neck_L` / `XL430_neck_R` | 목 서보 |
| 회색 | `cooling_fan_40mm` | 냉각 팬 |

---

## 2. 다리 미러링 (단측 → 양쪽)

`hylion_leg` 탭에서:

1. 상단 툴바에서 **`Mirror`** 피처 찾기
   - 툴바 오른쪽 끝 `...` 또는 `▼` 클릭 → 숨겨진 피처에서 `Mirror` 선택
2. **Entities** → 다리 파트 클릭
3. **Mirror plane** → `YZ Plane` 선택
4. `✓` 확인

→ 오른쪽·왼쪽 다리 완성

---

## 3. Assembly 조립

하단 `Assembly 1` 탭 클릭

각 파트 탭에서 파트를 Assembly로 불러와 세로로 배치:

```
(위)
  머리        hylion_head
  토르소      hylion_torso
  골반        hylion_pelvis
  왼쪽 다리   hylion_leg (원본)
  오른쪽 다리 hylion_leg (미러)
(아래)
```

**배치 기준 치수 (지면 Z=0 기준):**

| 파트 | 높이 | 지면 기준 Z |
|------|------|------------|
| 다리 (BHL URDF) | 360mm | 0 ~ 360mm |
| 골반 | 235mm | 360 ~ 595mm |
| 토르소 | 250mm | 595 ~ 845mm |
| 목 (XL430) | 40mm | 845 ~ 885mm |
| 머리 | 350mm | 885 ~ 1235mm |

> **참고:** BHL 전체 높이는 ~800mm이나, 위 수치는 외피 CAD 기준 추정값.
> 실제 조립 후 BHL URDF와 대조하여 보정 필요.

---

## 4. 트러블슈팅

### `pip`이 인식되지 않을 때

```
# pip 대신 아래 명령어 사용
python -m pip install cadquery
```

### `py` 명령어도 안 될 때

- Python이 PATH에 없는 것 → VSCode `Ctrl+Shift+P` → `Python: Select Interpreter`에서 경로 확인
- 전체 경로로 실행:
  ```
  C:\Users\...\Python311\python.exe -m pip install cadquery
  ```

### STEP 파일이 일부만 생성될 때

- 스크립트 실행 중 에러 발생 → 터미널 에러 메시지 확인
- 가장 흔한 에러: `gp_Vec::Normalized() - vector has zero norm`
  - `make_cyl`/`make_rect`의 `normal`과 `xDir`이 평행할 때 발생
  - `hylion_cad.py`의 `_xdir()` 함수가 자동으로 방지하도록 되어 있음

### OnShape에서 파트가 22개 조각으로 쪼개져 보일 때

- CadQuery union 과정에서 내부적으로 여러 body가 생성된 것
- Assembly 탭에서 사용 시 특별한 문제 없음
- 각 파트 탭에서 개별로 보는 것을 권장

---

## 5. 의류학과 협업 시 공유 방법

### OnShape 링크 공유

OnShape 문서 우측 상단 **`Share`** → **`Copy link`**
→ 링크를 의류학과 학생에게 전달 (무료 계정으로도 열람 가능)

### 학생이 확인해야 할 항목

| 확인 항목 | 관련 파트 |
|-----------|-----------|
| 카메라 창 위치·크기 (93×30mm) | `hylion_head` |
| 입 개구부 위치·크기 (60×22mm) | `hylion_head` |
| 스피커 그릴 위치 | `hylion_head` |
| 마이크 홀 위치 (측면 Ø8mm) | `hylion_head` |
| 어깨 플랜지 돌출 위치 | `hylion_torso` |
| 배기팬 홀 위치 (상단 Ø42mm) | `hylion_torso` |
| 흡기 슬롯 위치 (하단 ×4) | `hylion_torso` |
| NUC 포트 개구부 (배면) | `hylion_torso` |
| 관절 개구부 위치 (무릎·발목·힙) | `hylion_leg` |
