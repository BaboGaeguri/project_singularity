import json
import uuid
from datetime import datetime
from groq import Groq

from hylion_perception import perceive_environment, pixel_to_robot_coords
from hylion_soarm import call_lerobot_act_model, apply_inverse_kinematics

# Initialize Groq client (Uses GROQ_API_KEY from ~/.bashrc)
client = Groq()

# HYlion JSON Action Schema v3.0 (LeRobot ACT + SO-ARM 101 Pro 통합)
system_prompt = """You are the AI brain of the 'HYlion' physical robot with SO-ARM 101 Pro manipulator.
You must output your response ONLY as a valid JSON object matching the following schema.
Do not include any conversational text outside the JSON.
Please use English for 'tts_text' to prevent terminal font rendering issues.

Schema v3.0 — SO-ARM 101 Pro Compatible:
{
  "action_id": "string (unique uuid)",
  "timestamp": "string (ISO8601_with_Z)",
  "state": "IDLE | TALKING | MANIPULATING | WALKING | LOW_BATTERY | EMERGENCY",
  "intent": "pick_place | greet | walk | chat | stop | look_at",
  "target_object": "string (starbucks_cup | tumbler | doll | human | None)",
  "emotion": "string (happy | neutral | sad | focused)",
  "tts_text": "string (English)",
  
  "perception": {
    "detected_objects": [],
    "target_position": {"x_cm": 0, "y_cm": 0, "z_cm": 0},
    "approach_angle_deg": 0
  },
  
  "motion_cmd": {
    "pipeline": "act_imitation | precoded_pick | rule_based",
    "task_description": "string",
    "language_instruction": "string",
    "so_arm_control": {
      "method": "act_sequence | inverse_kinematics | precoded",
      "act_output": null,
      "ik_target": null,
      "fallback_joint_target": null,
      "fallback_gripper_effort": null
    }
  },
  
  "safety": {
    "collision_check": true,
    "force_limit_newtons": 30,
    "gripper_max_effort": 100,
    "emergency_stop": false
  },
  
  "gait_cmd": "forward | backward | turn_left | turn_right | stop | None",
  "confidence": 0.0,
  "fallback": "string"
}

CRITICAL RULES FOR LLM:
1. If intent == 'pick_place' → target_object MUST NOT be None (confidence >= 0.5)
2. If intent == 'pick_place' → motion_cmd.pipeline SHOULD be 'act_imitation' (primary) or 'precoded_pick' (fallback)
3. If state == 'MANIPULATING' AND gait_cmd != 'stop' → FORCE gait_cmd = 'stop'
4. Only include so_arm_control when intent == 'pick_place'; otherwise omit it.
5. For WALKING → gait_cmd != None, gripper_effort should be 0 (open, safe for walking)
6. Confidence should reflect both object detection and motion feasibility
"""


def reason_with_llm(user_input, detections, chat_history):
    perception_context = f"""
Current camera detections:
{json.dumps(detections, indent=2)}

User command: \"{user_input}\"
"""

    full_prompt = system_prompt + "\n" + perception_context

    messages = chat_history.copy()
    if not messages or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": full_prompt})
    else:
        messages[-1] = {"role": "user", "content": full_prompt}

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        llm_output = response.choices[0].message.content
        return json.loads(llm_output)

    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None


def populate_perception_data(action_json, detections):
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


def validate_action_json(action_json):
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
    act_result = call_lerobot_act_model(
        camera_frame=None,
        language_instruction=motion_cmd.get("language_instruction", ""),
        target_object_detection=action_json.get("perception", {}).get("detected_objects", [None])[0]
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


def chat_with_hylion():
    print("="*60)
    print("🤖 HYlion Brain v2.0 is ONLINE (LLM orchestration only)")
    print("="*60)
    print("Type your message (or 'quit'/'exit' to stop)")
    print("="*60)

    chat_history = [{"role": "system", "content": system_prompt}]

    while True:
        print("\n📸 [Sensing environment...]")
        detections, frame = perceive_environment(use_camera=True)

        if detections:
            print(f"   ✅ Detected {len(detections)} object(s)")
        else:
            print("   ⚠️ No objects detected")

        user_input = input("\n[You]: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("\n🛑 Shutting down HYlion brain... Goodbye!")
            break
        if not user_input:
            continue

        print("\n🧠 [LLM reasoning...]")
        chat_history.append({"role": "user", "content": user_input})

        action_json = reason_with_llm(user_input, detections, chat_history)
        if not action_json:
            print("❌ LLM failed to generate valid JSON")
            continue

        populate_perception_data(action_json, detections)
        issues = validate_action_json(action_json)
        for issue in issues:
            print(issue)

        action_json["action_id"] = str(uuid.uuid4())
        action_json["timestamp"] = datetime.utcnow().isoformat() + "Z"

        print("\n" + "-"*60)
        print(f"🔊 [Robot says]: {action_json.get('tts_text', '(silent)')}")
        print("-"*60)
        print(json.dumps(action_json, indent=2))

        chat_history.append({"role": "assistant", "content": json.dumps(action_json)})


if __name__ == "__main__":
    chat_with_hylion()
