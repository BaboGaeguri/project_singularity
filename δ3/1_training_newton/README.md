# 트랙 1: Newton 물리 엔진을 이용한 강화학습

이 디렉토리는 Isaac Sim 6.0.0 (pip 설치) 환경에서 Newton 물리 엔진을 사용하여 `hylion_v6` 모델의 보행 정책을 학습하는 작업을 관리합니다.

## 주요 파일 및 디렉토리

- **학습 실행 스크립트**: `../../scripts/train_hylion.py`
- **학습 모니터링 스크립트**: `../../scripts/monitor_hylion_retrain.sh`
- **학습 대상 URDF**: `../../robot/hylion_v6.urdf`
- **Newton용 USD 에셋**: `../../usd/hylion_v6/`
- **실시간 로그 파일**: `../../hylion_v6_newton.log`
- **학습 결과 저장 위치**: `../../logs/hylion_v6_newton/`
  - 이 디렉토리 안에 학습된 정책(`.pth` 파일)이 저장됩니다.

## 현재 상태

- `train_hylion.py` 스크립트가 백그라운드에서 실행 중입니다.
- `ps -ef | grep train_hylion.py` 명령어로 프로세스를 확인할 수 있습니다.
- `tail -f ../../hylion_v6_newton.log` 또는 `../../scripts/monitor_hylion_retrain.sh`로 학습 현황을 실시간으로 볼 수 있습니다.

## 다음 단계

1.  `logs/hylion_v6_newton/` 디렉토리에 충분히 학습된 `.pth` 파일이 저장될 때까지 기다립니다.
2.  가장 성능이 좋은 `.pth` 파일을 선택하여 시각화 트랙으로 전달합니다.
