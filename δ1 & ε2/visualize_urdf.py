"""URDF 시각화 스크립트"""
import sys
import yourdfpy

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "δ1 & ε2/urdf/hylion.urdf"
    print(f"URDF 로드 중: {path}")
    robot = yourdfpy.URDF.load(path)
    print(f"로봇 이름: {robot.robot.name}")
    print(f"Links: {len(robot.robot.links)}개")
    print(f"Joints: {len(robot.robot.joints)}개")
    robot.show()