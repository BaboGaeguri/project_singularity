#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import json
import uuid
from datetime import datetime
from groq import Groq

from hylion_perception import perceive_environment, pixel_to_robot_coords
from hylion_soarm import call_lerobot_act_model, apply_inverse_kinematics

class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # System prompt for LLM
        self.system_prompt = """
You are HYlion, an intelligent robot assistant. Your task is to understand user requests and generate appropriate actions in JSON format.

Available actions:
- navigation: Move to a location
- pick_place: Pick up or place objects (triggers SO-ARM control)
- speak: Generate TTS response
- observe: Look around and detect objects

For pick_place actions, include so_arm_control with act_output, ik_target, and fallback options.

Response format: Valid JSON only, no additional text.
"""

        # Publishers
        self.action_json_pub = self.create_publisher(String, '/hylion/action_json', 10)
        self.tts_pub = self.create_publisher(String, '/hylion/tts', 10)

        # Subscribers
        self.user_input_sub = self.create_subscription(String, '/hylion/user_input', self.user_input_callback, 10)
        self.perception_sub = self.create_subscription(String, '/hylion/perception', self.perception_callback, 10)

        # State
        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        self.latest_detections = []
        self.pending_action = None

        # Groq client
        self.client = Groq()

        self.get_logger().info('Brain Node initialized')

    def user_input_callback(self, msg):
        user_input = msg.data.strip()
        if not user_input or user_input.lower() in ['quit', 'exit']:
            return

        self.get_logger().info(f'Received user input: {user_input}')

        # LLM reasoning
        action_json = self.reason_with_llm(user_input, self.latest_detections, self.chat_history)
        if not action_json:
            self.get_logger().error('LLM failed to generate JSON')
            return

        # Normalize to internal schema
        action_json = self.normalize_action_json(action_json)

        # Populate perception data
        self.populate_perception_data(action_json, self.latest_detections)

        # Validate and generate SO-ARM commands if needed
        issues = self.validate_action_json(action_json)
        for issue in issues:
            if issue.startswith('⚠️'):
                self.get_logger().warn(issue)
            else:
                self.get_logger().info(issue)

        # Add metadata
        action_json["action_id"] = str(uuid.uuid4())
        action_json["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Publish action JSON
        json_str = json.dumps(action_json)
        self.action_json_pub.publish(String(data=json_str))
        self.get_logger().info(f'Published action_json: {json_str[:160]}')

        # Publish TTS
        tts_text = action_json.get('tts_text', '')
        if tts_text:
            self.tts_pub.publish(String(data=tts_text))
            self.get_logger().info(f'Published tts: {tts_text}')

        # Update history
        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": json_str})

    def perception_callback(self, msg):
        try:
            self.latest_detections = json.loads(msg.data)
            self.get_logger().info(f'Updated detections: {len(self.latest_detections)} objects')
        except json.JSONDecodeError:
            self.get_logger().error('Failed to parse perception data')

    def reason_with_llm(self, user_input, detections, chat_history):
        perception_context = f"Current camera detections: {json.dumps(detections, indent=2)}\nUser command: \"{user_input}\""
        full_prompt = self.system_prompt + "\n" + perception_context

        messages = chat_history.copy()
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": full_prompt})
        else:
            messages[-1] = {"role": "user", "content": full_prompt}

        # Try external LLM (Groq); fallback to deterministic local handler
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            llm_output = response.choices[0].message.content
            parsed = json.loads(llm_output)
            self.get_logger().info('LLM response received')
            return parsed
        except Exception as e:
            self.get_logger().warn(f'LLM Error, using local fallback: {e}')

        # Local deterministic parser for quick testing
        return self.local_reasoning(user_input, detections)

    def local_reasoning(self, user_input, detections):
        user_input_lower = user_input.lower()
        action_json = {
            "intent": "observe",
            "state": "IDLE",
            "tts_text": "I did not understand. Please repeat.",
            "motion_cmd": {}
        }

        if "pick up" in user_input_lower or "grab" in user_input_lower or "lift" in user_input_lower:
            # pick_place intent
            target_engineered = "unknown"
            target_detection = detections[0] if detections else None
            if target_detection:
                target_engineered = target_detection.get("class", "unknown")

            action_json = {
                "intent": "pick_place",
                "state": "MANIPULATING",
                "target_object": target_engineered,
                "confidence": 0.7,
                "tts_text": f"Okay, I will pick up the {target_engineered}.",
                "motion_cmd": {
                    "so_arm_control": {
                        "method": "inverse_kinematics",
                        "ik_target": {
                            "position_xyz": [
                                target_detection.get("robot_x_cm", 25.0) / 100.0 if target_detection else 0.30,
                                target_detection.get("robot_y_cm", 0.0) / 100.0 if target_detection else 0.0,
                                target_detection.get("robot_z_cm", 30.0) / 100.0 if target_detection else 0.20
                            ],
                            "orientation_rpy": [0, 90, 0]
                        },
                        "fallback_gripper_effort": 60
                    }
                }
            }

        elif "go to" in user_input_lower or "move" in user_input_lower:
            action_json = {
                "intent": "navigation",
                "state": "MOVING",
                "target_object": "location",
                "confidence": 0.8,
                "tts_text": "Moving to the requested location.",
                "motion_cmd": {}
            }

        else:
            action_json = {
                "intent": "observe",
                "state": "IDLE",
                "tts_text": "I am observing the environment.",
                "motion_cmd": {}
            }

        return action_json

    def populate_perception_data(self, action_json, detections):
        if "perception" not in action_json:
            action_json["perception"] = {"detected_objects": [], "target_position": {"x_cm": 0, "y_cm": 0, "z_cm": 0}, "approach_angle_deg": 0}

        if not detections:
            action_json["perception"]["detected_objects"] = []
            return

        for det in detections:
            x_robot, y_robot, z_robot = pixel_to_robot_coords(det["x_pixel"], det["y_pixel"], det.get("depth_cm", 50))
            det["robot_x_cm"] = round(x_robot, 1)
            det["robot_y_cm"] = round(y_robot, 1)
            det["robot_z_cm"] = round(z_robot, 1)

        action_json["perception"]["detected_objects"] = detections

        if action_json.get("intent") == "pick_place" and detections:
            t = detections[0]
            action_json["perception"]["target_position"] = {"x_cm": t["robot_x_cm"], "y_cm": t["robot_y_cm"], "z_cm": t["robot_z_cm"]}

    def validate_action_json(self, action_json):
        issues = []

        intent = action_json.get("intent")

        if intent == "pick_place":
            if not action_json.get("target_object") or action_json.get("target_object") == "None":
                action_json["target_object"] = "unknown"
                action_json["confidence"] = 0.3
                issues.append("⚠️ target_object was None, set to 'unknown' with low confidence")

        if action_json.get("state") == "MANIPULATING" and action_json.get("gait_cmd") != "stop":
            action_json["gait_cmd"] = "stop"
            issues.append("⚠️ State=MANIPULATING forces gait_cmd=stop")

        motion_cmd = action_json.get("motion_cmd", {})

        if intent != "pick_place":
            motion_cmd.pop("so_arm_control", None)
            action_json["motion_cmd"] = motion_cmd
            return issues

        so_arm = motion_cmd.get("so_arm_control", {})
        detected_objects = action_json.get("perception", {}).get("detected_objects", [])
        if not detected_objects:
            detected_obj = None
        else:
            detected_obj = detected_objects[0]

        act_result = call_lerobot_act_model(
            camera_frame=None,
            language_instruction=motion_cmd.get("language_instruction", ""),
            target_object_detection=detected_obj
        )

        if act_result:
            so_arm["act_output"] = act_result
            so_arm["method"] = "act_sequence"
            issues.append("✅ ACT model generated action sequence")
        else:
            if so_arm.get("method") == "act_sequence":
                so_arm["method"] = "precoded"
                issues.append("⚠️ ACT unavailable, switched to precoded_pick fallback")

            if so_arm.get("ik_target"):
                try:
                    target_xyz = so_arm["ik_target"].get("position_xyz", [0.3, 0, 0.2])
                    target_rpy = so_arm["ik_target"].get("orientation_rpy", [0, 90, 0])
                    so_arm["fallback_joint_target"] = apply_inverse_kinematics(target_xyz, target_rpy)
                except Exception as e:
                    issues.append(f"⚠️ IK failed: {e}")

        motion_cmd["so_arm_control"] = so_arm
        action_json["motion_cmd"] = motion_cmd

        return issues

    def normalize_action_json(self, action_json):
        # Convert legacy keys to unified schema
        if not isinstance(action_json, dict):
            return {
                "intent": "observe",
                "state": "IDLE",
                "tts_text": "Could not parse action JSON.",
                "motion_cmd": {}
            }

        # Legacy field mapping
        if "intent" not in action_json:
            action = action_json.get("action") or action_json.get("behavior")
            if isinstance(action, str):
                action_low = action.lower()
                if "pick" in action_low:
                    action_json["intent"] = "pick_place"
                elif "place" in action_low:
                    action_json["intent"] = "pick_place"
                elif "move" in action_low or "go" in action_low:
                    action_json["intent"] = "navigation"
                elif "speak" in action_low or "talk" in action_low:
                    action_json["intent"] = "speak"
                else:
                    action_json["intent"] = "observe"
            else:
                action_json["intent"] = "observe"

        if "target_object" not in action_json:
            if "object" in action_json:
                action_json["target_object"] = action_json.get("object")

        if "tts_text" not in action_json and "utterance" in action_json:
            action_json["tts_text"] = action_json.get("utterance")

        if "motion_cmd" not in action_json:
            action_json["motion_cmd"] = {}

        # Move top-level so_arm_control under motion_cmd if present
        if "so_arm_control" in action_json:
            action_json.setdefault("motion_cmd", {})["so_arm_control"] = action_json.pop("so_arm_control")

        # Ensure so_arm_control structure exists for pick_place
        if action_json.get("intent") == "pick_place":
            action_json.setdefault("motion_cmd", {}).setdefault("so_arm_control", {})

        return action_json


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
