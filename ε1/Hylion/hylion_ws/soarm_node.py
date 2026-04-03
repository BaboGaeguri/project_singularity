#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

from hylion_soarm import call_lerobot_act_model, apply_inverse_kinematics


class SoArmNode(Node):
    def __init__(self):
        super().__init__('soarm_node')

        # Publisher
        self.soarm_cmd_pub = self.create_publisher(String, '/hylion/soarm_command', 10)

        # Subscriber
        self.action_json_sub = self.create_subscription(String, '/hylion/action_json', self.action_json_callback, 10)

        self.get_logger().info('SO-ARM Node initialized')

    def action_json_callback(self, msg):
        try:
            action_json = json.loads(msg.data)
            self.get_logger().info(f'Received action_json: intent={action_json.get("intent")}, target={action_json.get("target_object")}')

            intent = action_json.get("intent")
            if intent != "pick_place":
                self.get_logger().info('Ignoring non-pick_place intent')
                return  # Only handle pick_place

            motion_cmd = action_json.get("motion_cmd", {})
            so_arm_control = motion_cmd.get("so_arm_control", {})

            # Generate SO-ARM command
            command = self.generate_soarm_command(so_arm_control, action_json)

            if command:
                json_str = json.dumps(command)
                self.soarm_cmd_pub.publish(String(data=json_str))
                self.get_logger().info(f'Published SO-ARM command: {so_arm_control.get("method")}')

        except json.JSONDecodeError:
            self.get_logger().error('Failed to parse action JSON')

    def generate_soarm_command(self, so_arm_control, action_json):
        method = so_arm_control.get("method")

        if method == "act_sequence":
            act_output = so_arm_control.get("act_output")
            if act_output:
                return {
                    "type": "act_sequence",
                    "action_sequence": act_output["predicted_action_sequence"],
                    "num_steps": act_output["num_steps"],
                    "step_duration_ms": act_output["step_duration_ms"]
                }

        elif method == "inverse_kinematics":
            ik_target = so_arm_control.get("ik_target")
            if ik_target:
                target_xyz = ik_target.get("position_xyz", [0.3, 0, 0.2])
                target_rpy = ik_target.get("orientation_rpy", [0, 90, 0])
                joint_angles = apply_inverse_kinematics(target_xyz, target_rpy)
                return {
                    "type": "joint_target",
                    "joint_positions_deg": joint_angles,
                    "gripper_effort": so_arm_control.get("fallback_gripper_effort", 60)
                }

        elif method == "precoded":
            return {
                "type": "joint_target",
                "joint_positions_deg": so_arm_control.get("fallback_joint_target", [0, 90, -90, 0, 0, 0]),
                "gripper_effort": so_arm_control.get("fallback_gripper_effort", 60)
            }

        return None


def main(args=None):
    rclpy.init(args=args)
    node = SoArmNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
