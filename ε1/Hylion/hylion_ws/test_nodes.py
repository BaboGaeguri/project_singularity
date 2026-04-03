#!/usr/bin/env python3
"""
ROS2 노드 통합 테스트 스크립트
- brain_node, perception_node, soarm_node 간 토픽 통신 테스트
- 실제 카메라 없이 시뮬레이션 데이터로 테스트
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import time

class TestNode(Node):
    def __init__(self):
        super().__init__('test_node')

        # 퍼블리셔들
        self.user_input_pub = self.create_publisher(String, '/hylion/user_input', 10)
        self.camera_pub = self.create_publisher(String, '/hylion/test_camera', 10)

        # 서브스크라이버들
        self.perception_sub = self.create_subscription(
            String, '/hylion/perception', self.perception_callback, 10)
        self.action_sub = self.create_subscription(
            String, '/hylion/action_json', self.action_callback, 10)
        self.soarm_sub = self.create_subscription(
            String, '/hylion/soarm_command', self.soarm_callback, 10)
        self.tts_sub = self.create_subscription(
            String, '/hylion/tts', self.tts_callback, 10)

        # 테스트 데이터
        self.test_count = 0
        self.received_perception = False
        self.received_action = False
        self.received_soarm = False
        self.received_tts = False

        # 타이머로 테스트 실행
        self.timer = self.create_timer(2.0, self.run_test)

    def run_test(self):
        if self.test_count == 0:
            self.get_logger().info("=== 테스트 시작: 사용자 입력 퍼블리시 ===")
            msg = String()
            msg.data = "Pick up the cup"
            self.user_input_pub.publish(msg)
            self.get_logger().info(f"Published: {msg.data}")

        elif self.test_count == 1:
            self.get_logger().info("=== 테스트 2: 카메라 이미지 시뮬레이션 ===")
            # 실제로는 이미지 메시지지만, 여기서는 String으로 시뮬레이션
            msg = String()
            msg.data = "simulated_image_data"
            self.camera_pub.publish(msg)
            self.get_logger().info("Published simulated camera image")

        self.test_count += 1

        # 10초 후 테스트 종료
        if self.test_count > 5:
            self.get_logger().info("=== 테스트 결과 ===")
            self.get_logger().info(f"Perception received: {self.received_perception}")
            self.get_logger().info(f"Action received: {self.received_action}")
            self.get_logger().info(f"SO-ARM received: {self.received_soarm}")
            self.get_logger().info(f"TTS received: {self.received_tts}")
            rclpy.shutdown()

    def perception_callback(self, msg):
        self.get_logger().info(f"Received perception: {msg.data[:100]}...")
        self.received_perception = True

    def action_callback(self, msg):
        self.get_logger().info(f"Received action: {msg.data[:100]}...")
        self.received_action = True

    def soarm_callback(self, msg):
        self.get_logger().info(f"Received SO-ARM: {msg.data[:100]}...")
        self.received_soarm = True

    def tts_callback(self, msg):
        self.get_logger().info(f"Received TTS: {msg.data}")
        self.received_tts = True

def main():
    rclpy.init()
    node = TestNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()