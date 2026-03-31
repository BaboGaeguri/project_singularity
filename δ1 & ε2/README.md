# δ1 & ε2 — Hylion 로봇 설계 및 어셈블리

> BHL(하체) + SO-ARM(팔) + 커스텀 파트(토르소/골반/머리)를 조합한 Hylion 로봇의 CAD 설계 작업 영역

---

## 문서 구조

| # | 파일 | 설명 | 대상 |
|---|------|------|------|
| 01 | `01_onshape_setup_guide.md` | Onshape API 환경 세팅 (문서 확보, API key, Python venv) | 새 팀원 |
| 02 | `02_onshape_api_guide.md` | Onshape API 레퍼런스 (엔드포인트, 인증, 트러블슈팅) | 개발 중 참조 |
| 03 | `03_hylion_assembly_worklog.md` | 어셈블리 작업 진행 기록 (현재 상태, TODO) | 팀 내 공유 |
| 04 | `04_hyrion_dimensions.md` | 파트별 치수 정리 | 설계 참조 |
| 05 | `05_hyrion_parts_weight.md` | 파트별 무게 정리 | 설계 참조 |
| 06 | `06_hyrion_internal_parts_final.md` | 내부 부품 종합 정리 | 설계 참조 |
| 07 | `07_references.md` | 외부 링크 모음 (Onshape, API, 부품, 도구, 관련 인물) | 전체 참조 |
| 99 | `99_onshape_import_guide.md` | STEP → Onshape 업로드 가이드 (레거시) | 참고용 |

**처음 참여한다면:** `01` → `02` → `03` 순서로 읽으세요.

---

## 스크립트

| 파일 | 용도 |
|------|------|
| `assembly_hylion.py` | Onshape 어셈블리에 BHL/SO-ARM 삽입 + Transform 배치 |
| `inspect_assembly.py` | 어셈블리 상태 조회 → `onshape/{대상}_dump.json` 저장 (`--mates` 옵션으로 mate 포함) |
| `visualize_urdf.py` | URDF 3D 시각화 (yourdfpy) |
| `hylion_cad.py` | CadQuery 기반 커스텀 파트 생성 |
| `test_onshape.py` | Onshape API 연결 테스트 |
| `components/convert_step_to_stl.py` | STEP → STL 변환 |

---

## 폴더 구조

```
δ1 & ε2/
├── components/                     # 모든 부품 (mesh, URDF, CAD)
│   ├── berkeley_humanoid_lite/     #   BHL URDF + mesh
│   │   ├── mesh/                   #     STL 파일
│   │   └── urdf/                   #     URDF + config
│   └── so-arm/                     #   SO-ARM URDF + mesh
│       ├── assets/                 #     onshape-to-robot 추출 mesh (URDF용)
│       └── mesh/
│           ├── Individual/         #     개별 3D 프린팅 파트 STL
│           ├── Follower/           #     Follower 일체형 STL
│           ├── Leader/             #     Leader 일체형 STL
│           └── COTS/               #     구매 부품 (모터 등)
├── design/                         # 설계 요구사항, 제약조건, 방법론
├── urdf/                           # 합친 Hylion URDF + versions.md
├── step_files/                     # 커스텀 파트 STEP 파일
└── onshape/                        # Onshape API 조회 결과 (JSON)
```