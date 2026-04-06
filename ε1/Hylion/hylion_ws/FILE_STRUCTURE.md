# hylion_ws 파일 구조

```
hylion_ws/
│
├── FILE_STRUCTURE.md                        ← 이 문서
│
├── 📄 문서
│   ├── 하이리온 Physical AI 로봇 기획서.md  ← 전체 프로젝트 기획서 (v12)
│   ├── LEROBOT_ACT_JSON_MAPPING.md          ← LeRobot ACT ↔ HYlion JSON 매핑 가이드
│   ├── hylion_action_schema_v1.0.md         ← (비어 있음 — 작성 예정)
│   ├── HYlio_JSON_Action_Schema (v1.0).json ← JSON 액션 스키마 정의 (v1.0)
│   └── HYlion_JSON_액션_스키마_v1.0.docx   ← JSON 액션 스키마 정의 Word 버전
│
├── 🤖 ROS2 노드 (실행 파일)
│   ├── brain_node.py       ← LLM 오케스트레이션 노드 (Groq API, JSON 생성)
│   ├── perception_node.py  ← 카메라 + YOLO 감지 노드
│   ├── soarm_node.py       ← SO-ARM 101 제어 노드 (ACT / IK / fallback)
│   └── test_nodes.py       ← 노드 간 통신 통합 테스트 (카메라 없이 시뮬)
│
├── 🔧 모듈 (라이브러리)
│   ├── hylion_brain_v2.py  ← Brain 로직 standalone 버전 (ROS2 없이 CLI 테스트용, Schema v3.0)
│   ├── hylion_brain_test.py← Brain 로직 초기 버전 (Schema v1.0, 레거시)
│   ├── hylion_perception.py← YOLO 감지 + 카메라→로봇 좌표 변환 유틸리티
│   └── hylion_soarm.py     ← SO-ARM 제어 유틸리티 (ACT 추론 stub, IK stub)
│
└── 📦 ROS2 패키지
    └── src/
        └── hylion_brain/   ← ROS2 ament 패키지 (미완성, entry_points 비어 있음)
            ├── hylion_brain/
            │   └── __init__.py
            ├── resource/
            │   └── hylion_brain
            ├── test/
            │   ├── test_copyright.py
            │   ├── test_flake8.py
            │   └── test_pep257.py
            ├── package.xml
            ├── setup.cfg
            └── setup.py
```

---

## 파일별 역할 요약

### ROS2 노드 (실행 파일)

| 파일 | 노드명 | Subscribe | Publish |
|------|--------|-----------|---------|
| `brain_node.py` | `brain_node` | `/hylion/user_input`, `/hylion/perception` | `/hylion/action_json`, `/hylion/tts` |
| `perception_node.py` | `perception_node` | `/camera/image_raw`, `/hylion/test_camera` | `/hylion/perception` |
| `soarm_node.py` | `soarm_node` | `/hylion/action_json` | `/hylion/soarm_command` |
| `test_nodes.py` | `test_node` | `/hylion/perception`, `/hylion/action_json`, `/hylion/soarm_command`, `/hylion/tts` | `/hylion/user_input`, `/hylion/test_camera` |

### 모듈 (라이브러리)

| 파일 | 주요 함수/클래스 | 상태 |
|------|----------------|------|
| `hylion_perception.py` | `perceive_environment()`, `pixel_to_robot_coords()` | YOLO 선택적 import (ultralytics 없으면 mock 반환) |
| `hylion_soarm.py` | `call_lerobot_act_model()`, `apply_inverse_kinematics()` | 두 함수 모두 stub (Week 2~3 구현 예정) |
| `hylion_brain_v2.py` | Groq LLM 호출, JSON 생성 (Schema v3.0) | CLI 대화형 테스트용 |
| `hylion_brain_test.py` | Groq LLM 호출 (Schema v1.0) | 레거시, v2로 대체됨 |

### 문서

| 파일 | 내용 |
|------|------|
| `하이리온 Physical AI 로봇 기획서.md` | 시연 시나리오, 상태 머신, 시스템 아키텍처, HW 구성, 팀 역할, 13주 일정 |
| `LEROBOT_ACT_JSON_MAPPING.md` | LeRobot ACT 데이터셋 구조, SO-ARM 관절 순서, ACT→JSON 매핑, 구현 타임라인 |
| `HYlio_JSON_Action_Schema (v1.0).json` | JSON 액션 스키마 공식 정의 |

---

## 실행 방법

```bash
# ROS2 노드 실행 (터미널 3개)
ros2 run hylion brain_node
ros2 run hylion perception_node
ros2 run hylion soarm_node

# 사용자 입력 테스트
ros2 topic pub /hylion/user_input std_msgs/String "data: 'Pick up the cup'"

# 통합 테스트 (카메라 없이)
python3 test_nodes.py

# standalone CLI 테스트 (ROS2 없이)
python3 hylion_brain_v2.py
```
