# 트랙 2: PhysX 물리 엔진을 이용한 시각화

이 디렉토리는 Isaac Sim 5.1.0 (애플리케이션) 환경에서 PhysX 물리 엔진을 사용하여 학습된 `hylion_v6` 모델의 보행 정책을 시각화하고 영상을 녹화하는 작업을 관리합니다.

## 주요 파일 및 디렉토리

- **시각화 대상 URDF**: `../../robot/hylion_v6.urdf`
- **PhysX용 USD 에셋**: `usd/` (이 디렉토리 안에 생성될 예정)
- **시각화/녹화 스크립트**: `scripts/` (이 디렉토리 안에 생성될 예정)
- **학습된 정책 파일**: `checkpoints/` (이 디렉토리 안에 학습 트랙에서 생성된 `.pth` 파일을 복사해 올 예정)

## 작업 흐름

1.  **PhysX용 USD 변환**: `hylion_v6.urdf`를 PhysX와 호환되는 USD 에셋으로 변환하여 `usd/` 폴더에 저장합니다.
2.  **체크포인트 복사**: 학습 트랙(`1_training_newton`)의 `logs/` 디렉토리에서 가장 성능이 좋은 정책 파일(`.pth`)을 `checkpoints/` 폴더로 복사합니다.
3.  **시각화 스크립트 실행**: `scripts/` 폴더의 재생 스크립트를 실행하여, 복사된 정책과 PhysX용 USD를 이용해 로봇의 움직임을 시각화하고 필요시 영상을 녹화합니다.

## 다음 단계

1.  PhysX용 USD 변환 스크립트(`scripts/convert_urdf_physx.py`)를 작성하고 실행합니다.
2.  재생 및 녹화 스크립트(`scripts/playback_physx.sh`)를 작성합니다.
