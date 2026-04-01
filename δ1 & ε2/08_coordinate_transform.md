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