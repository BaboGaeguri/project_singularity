# STL 좌표계 변환 규칙

> Onshape 직접 Export STL과 BHL 원본 리포 STL 사이의 좌표 변환 규칙
> 검증 방법: `base_visual.stl`(원본 리포) vs `base_tocompare.stl`(Onshape Export)의 bounds 비교

---

## 배경

BHL 원본 리포(`berkeley-humanoid-lite-assets`)에서 제공하는 STL과, Onshape에서 직접 Export한 STL은 **좌표계가 다르다**.

| 출처 | 좌표계 | 예시 파일 |
|------|--------|-----------|
| BHL 원본 리포 (URDF용) | 로봇 좌표계 (x=전후, y=좌우, z=상하) | `base_visual.stl` |
| Onshape 직접 Export | Onshape 내부 좌표계 (축이 뒤바뀜) | `base_tocompare.stl`, `base_no_actuator_BG.stl` |

---

## 변환 규칙

### Onshape Export → URDF 좌표계

```
URDF_x = -Onshape_y + (-0.000904)
URDF_y =  Onshape_x + (-0.000265)
URDF_z =  Onshape_z + (-0.075029)
```

축 매핑:
- **Onshape y축 → URDF x축** (부호 반전)
- **Onshape x축 → URDF y축** (부호 유지)
- **Onshape z축 → URDF z축** (부호 유지)

오프셋: `(-0.000904, -0.000265, -0.075029)` — Onshape 내부 원점과 URDF 원점의 차이

---

## 검증 결과

`base_visual.stl`(원본)과 `base_tocompare.stl`(Onshape Export)에 변환 적용 후 비교:

| 항목 | 변환 후 | 원본 | 오차 |
|------|---------|------|------|
| Bounds min x | -0.070904 | -0.070904 | 0.000000 |
| Bounds min y | -0.133265 | -0.133265 | 0.000000 |
| Bounds min z | -0.161389 | -0.161360 | 0.000029 |
| Bounds max x | 0.073096 | 0.073096 | 0.000000 |
| Bounds max y | 0.132735 | 0.132735 | 0.000000 |
| Bounds max z | 0.154999 | 0.154969 | 0.000030 |

z축 오차 ~0.03mm — 삼각형 해상도 차이(원본 41,942개 vs Onshape 1,770,414개)에 의한 것으로, 무시 가능.

---

## 적용 예시 (Python / trimesh)

```python
import trimesh
import numpy as np

mesh = trimesh.load('onshape_exported.stl')
v = mesh.vertices.copy()

# 좌표 변환
new_vertices = np.column_stack([
    -v[:, 1] - 0.000904,   # URDF_x = -Onshape_y + offset
     v[:, 0] - 0.000265,   # URDF_y =  Onshape_x + offset
     v[:, 2] - 0.075029,   # URDF_z =  Onshape_z + offset
])

transformed = trimesh.Trimesh(vertices=new_vertices, faces=mesh.faces, process=True)
transformed.export('urdf_compatible.stl')
```

---

## 주의사항

- 이 변환 규칙은 **BHL base 파트**에서 도출됨. 다른 Onshape 문서에서는 오프셋이 다를 수 있음.
- 축 매핑(x↔y, 부호 반전)은 Onshape 전반에 적용될 가능성이 높지만, 오프셋은 문서별 원점 설정에 따라 달라짐.
- Export 설정: Format=STL, Binary, Units=Meter, Resolution=Medium

---

## URDF revolute joint의 origin rpy 수정 규칙

> revolute joint의 초기 포즈(관절 각도)를 바꿀 때의 규칙.
> v5 작업 중 시행착오를 거쳐 도출 (2026-04-02)

### 핵심 원리

- revolute joint의 `<origin rpy>`는 **parent와 child 사이의 좌표계 정의**
- `<axis xyz="0 0 1">`이면 **로컬 Z축이 모터 회전축**
- rpy에서 **axis에 해당하는 성분(yaw)만 변경**하면 모터 회전 방향으로 초기 포즈 변경 가능
- **axis에 해당하지 않는 성분(roll, pitch)을 변경하면 모터 축 자체가 틀어져서 파트가 분리될 수 있음**

### axis와 rpy 대응

| axis | 모터 회전 방향에 해당하는 rpy 성분 |
|------|----------------------------------|
| `(1, 0, 0)` | **roll** (첫 번째 값) |
| `(0, 1, 0)` | **pitch** (두 번째 값) |
| `(0, 0, 1)` | **yaw** (세 번째 값) |

### 주의: roll/pitch가 이미 들어있는 경우

`rpy=(-1.5708, -1.5708, 0)`처럼 roll/pitch에 값이 있으면 이건 **좌표계 정의(모터 축 방향 설정)**이므로 건드리면 안 됨.
단, 이 값이 **초기 포즈에 영향**을 주고 있는 경우도 있음.

### 실제 사례: SO-ARM shoulder_lift

```xml
<!-- 원본 (ㄱ자로 꺾인 상태) -->
<origin xyz="-0.0303992 -0.0182778 -0.0542" rpy="-1.5708 -1.5708 0"/>
<axis xyz="0 0 1"/>

<!-- 차렷 자세 (팔을 아래로 펼침) -->
<origin xyz="-0.0303992 -0.0182778 -0.0542" rpy="-1.5708 0 0"/>
```

- `pitch`를 `-1.5708` → `0`으로 변경하여 ㄱ자 꺾임을 펼침
- `roll=-1.5708`은 좌표계 정의이므로 유지
- `yaw=0`은 모터 초기 각도(axis Z 방향)이므로 이걸 바꾸면 모터 회전 방향으로 초기 포즈 변경

### yaw 값에 따른 초기 포즈 (shoulder_lift 기준)

| yaw 값 | 각도 | 포즈 |
|--------|------|------|
| 0 | 0도 | 차렷 자세 (팔 아래로) |
| 1.5708 | +90도 | 팔 옆으로 뻗음 |
| -1.5708 | -90도 | 팔 반대쪽으로 |
| 3.14159 | 180도 | 만세 |

### fixed joint는 자유롭게 수정 가능

`type="fixed"` joint의 `origin rpy`는 제약 없이 변경 가능:
- SO-ARM 전체 방향 → `soarm_left_base_joint`의 rpy 수정
- child 이하가 통째로 회전, 내부 관절에 영향 없음

### Onshape 좌표계와의 차이

- URDF에서 SO-ARM base_joint의 rpy를 Onshape에 그대로 적용하면 방향이 다름
- Onshape Front 뷰 기준: Z=위, X=오른쪽
- URDF 기준: Z=위, Y=왼쪽, X=앞
- `roll=pi`로 뒤집힌 상태에서는 yaw가 수평 방향처럼 동작함 (로컬 Z축이 아래를 향하기 때문)