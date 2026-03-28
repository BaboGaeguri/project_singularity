# 하이리온 로봇 설계 진행 현황

## 현재 단계
**토르소 레이아웃 설계** 진행 중

---

## 진행 순서

- [x] Onshape 계정 세팅 완료 (Education/Student 플랜)
- [x] 설계 도구 결정: Onshape + CadQuery 병행
- [ ] **[진행 중] BHL 치수 파악** ← 지금 여기
- [ ] 토르소 레이아웃 스케치 (2D)
- [ ] 토르소 3D 모델 (CadQuery)
- [ ] 각 브래킷 설계
- [ ] IsaacLab URDF 반영

---

## 부품 치수 수집 현황

| 부품 | 치수 | 상태 |
|------|------|------|
| BHL 전체 높이 (로봇 전체) | ~80cm | ✅ 확인 |
| BHL 전체 무게 | 16kg | ✅ 확인 |
| BHL 최대 프린트 파트 크기 | 200×200×200mm | ✅ 확인 |
| BHL base(pelvis) 박스 크기 | 150×140×230mm | ✅ URDF 확인 |
| BHL hip joint 좌우 간격 | 160mm (각 ±80mm) | ✅ URDF 확인 |
| BHL hip joint 높이 (지면 기준) | ~543mm | ✅ URDF 확인 |
| BHL base(pelvis) 중심 높이 | ~710mm | ✅ URDF 확인 |
| BHL 토르소 마운팅 상단 높이 | ~825mm | ✅ URDF 계산값 |
| BHL base CoM | z=638mm | ✅ URDF 확인 |
| Orin Nano Super | ~100×79mm | ⚠️ 두께 미확인 |
| NUC BeeLink N95 | ~126×113×37mm | ⚠️ 요확인 |
| SO-ARM101 | - | ⏳ 실측 후 |
| 배터리 A/B | - | ⏳ 실물 확인 후 |

---

## 참고 링크

- BHL GitHub: `github.com/HybridRobotics/Berkeley-Humanoid-Lite`
- BHL Docs: `berkeley-humanoid-lite.gitbook.io/docs`
- SO-ARM101: `github.com/TheRobotStudio/SO-ARM100`
