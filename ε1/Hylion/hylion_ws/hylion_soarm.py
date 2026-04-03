def call_lerobot_act_model(camera_frame, language_instruction, target_object_detection):
    """LeRobot ACT 모델 추론 (Week 3+ 구현)."""
    act_available = False

    if not act_available:
        return None

    # 실제 구현은 이 위치에 추가
    return None


def apply_inverse_kinematics(target_xyz, target_rpy, current_joint_state=None):
    """목표 좌표 → SO-ARM 6-DOF 관절각 변환 (Week 2 구현)."""
    # TODO: ikpy 또는 SO-ARM 라이브러리 활용
    return [0, 90, -90, 0, 0, 0]
