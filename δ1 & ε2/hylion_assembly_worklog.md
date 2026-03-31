# Hylion 어셈블리 작업 기록

> BHL + SO-ARM 원본 Onshape 문서를 API로 조합하여 Hylion 로봇 어셈블리를 구성하는 작업 기록
> 환경 세팅 → `onshape_setup_guide.md` | API 레퍼런스 → `onshape_api_guide.md`

---

## 전체 플로우

```
[1] 환경 세팅 (문서 확보, API key, venv)                 ✅ 완료 → onshape_setup_guide.md
[2] 어셈블리 배치 스크립트 실행                          ✅ 완료 (중복 삽입 해결됨)
[3] Assembly 상태 조회 + 정리                            ✅ 완료 (2026-03-31)
[4] BHL 토르소 내부 치수 자동 조회                       🔲 미수행
[5] 간섭 체크 (Interference Detection)                   🔲 미수행
[6] 배치 확정 후 검토 + Export                           🔲 미수행
```

---

## Document ID

| 문서 | did | wid | eid |
|------|-----|-----|-----|
| **Hylion Assembly** (작업 문서) | `a741aa6d15d9e384d9ffa4d9` | `2105b756950a92f6be143e8a` | `bff9221de0592d13a616f0f2` |
| **BHL 복사본** | `f0fecca5eed67c8c3b107deb` | `5986bd9b41326a2034f55e3a` | `8a738ee5d00bb7ca5f8b3bc0` |
| **SO-ARM 복사본** | `32d468d3a6994ea4b9d0cfa1` | `4702c8115f56790e62e507c5` | `61ca4b83d9996a40877b20fc` |

---

## 어셈블리 배치

스크립트: `assembly_hylion.py` (실행 시 기존 instance 전부 삭제 후 새로 삽입)

### 현재 상태 (2026-03-31)

| # | 이름 | 소스 | Transform (tx, ty, tz) |
|---|------|------|----------------------|
| 0 | Assembly \<1\> | BHL | (0, 0, 0) — 원점 |
| 1 | Assembly 1 new calib \<1\> | SO-ARM 좌 | (0.15, 0.2, 0.75) — 보정 필요 |
| 2 | Assembly 1 new calib \<2\> | SO-ARM 우 | (0.15, -0.2, 0.75) — 보정 필요 |

> 중복 삽입 문제 해결됨 — 스크립트에 `clear_all_instances()` 추가 (2026-03-31)

### 배치 기준 치수 (지면 Z=0 기준)

| 파트 | 지면 기준 Z | 근거 |
|------|------------|------|
| 다리 (BHL) | 0 ~ 360mm | URDF joint offset 합산 |
| 골반 | 360 ~ 595mm | hyrion_dimensions.md |
| 토르소 1층 (Jetson + NUC) | 595 ~ 634mm | 39mm |
| 토르소 2층 (제어 보드류) | 636 ~ 671mm | 35mm |
| 토르소 3층 (배터리 A+B) | 673 ~ 730mm | 57mm |
| 목 (XL430) | 845 ~ 885mm | 서보 크기 기준 |
| 머리 | 885 ~ 1235mm | 설계 결정값 |
| SO-ARM 좌 | tx=0.15, ty=+0.2, tz=0.75 | 초기값, 보정 필요 |
| SO-ARM 우 | tx=0.15, ty=-0.2, tz=0.75 | 초기값, 보정 필요 |

---

## TODO

- [x] 중복 BHL instance 삭제 (1개만 남기기) ✅ 2026-03-31
- [ ] SO-ARM transform 값 보정
- [ ] BHL 토르소 bounding box API 조회 (내부 가용 공간 확인)
- [ ] 간섭 체크 실행
- [ ] 배치 확정 후 STEP export + URDF 변환

조회 스크립트: `inspect_assembly.py` → 결과 JSON: `onshape/assembly_dump.json`