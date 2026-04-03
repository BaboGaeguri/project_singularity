#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import json

from hylion_perception import perceive_environment


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')

        # Publisher
        self.perception_pub = self.create_publisher(String, '/hylion/perception', 10)

        # Subscriber (Image와 String 모두 지원)
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.test_sub = self.create_subscription(String, '/hylion/test_camera', self.test_callback, 10)

        # CV Bridge
        self.bridge = CvBridge()

        # State
        self.latest_image = None

        self.get_logger().info('Perception Node initialized')

    def test_callback(self, msg):
        """Handle test String messages for simulation"""
        self.get_logger().info(f'Received test image data: {msg.data[:50]}...')
        
        # Simulate detections for testing
        detections = [
            {"class": "starbucks_cup", "confidence": 0.85, "x_pixel": 300, "y_pixel": 200},
            {"class": "table", "confidence": 0.92, "x_pixel": 400, "y_pixel": 300}
        ]
        
        # Publish detections
        json_str = json.dumps(detections)
        self.perception_pub.publish(String(data=json_str))
        self.get_logger().info(f'Published {len(detections)} test detections')

    def image_callback(self, msg):
        try:
            # Convert ROS Image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.latest_image = cv_image

            # Run perception
            detections, _ = perceive_environment(use_camera=False)  # Use stored image instead

            # If no detections from camera, try with current frame
            if not detections and self.latest_image is not None:
                # Simulate YOLO on current frame
                detections, _ = perceive_environment(use_camera=True)

            # Publish detections as JSON
            json_str = json.dumps(detections)
            self.perception_pub.publish(String(data=json_str))

            self.get_logger().info(f'Published {len(detections)} detections')

        except Exception as e:
            self.get_logger().error(f'Image processing error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
