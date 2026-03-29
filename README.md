# project_singularity

# 1. 의존성 파일 구조

설계/로봇 작업의 의존성을 분리해서 관리:

```
requirements.txt          ← 공통 (python-dotenv)
requirements_design.txt   ← 설계용 (requests, cadquery)
requirements_robot.txt    ← 로봇 구동용 (lerobot, torch)
```