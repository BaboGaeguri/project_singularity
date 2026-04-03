import os
import json
import uuid
from datetime import datetime
from groq import Groq

# Initialize Groq client (Uses GROQ_API_KEY from ~/.bashrc)
client = Groq()

# HYlion JSON Action Schema v1.0
system_prompt = """You are the AI brain of the 'HYlion' physical robot.
You must output your response ONLY as a valid JSON object matching the following schema.
Do not include any conversational text outside the JSON.
Please use English for 'tts_text' to prevent terminal font rendering issues.

Schema:
{
  "action_id": "string (unique id)",
  "timestamp": "string (ISO format)",
  "state": "IDLE | TALKING | MANIPULATING | WALKING | LOW_BATTERY | EMERGENCY",
  "intent": "pick_place | greet | walk | chat | stop | look_at",
  "target_object": "string (e.g., starbucks_cup, tumbler, doll, None)",
  "emotion": "string (e.g., happy, neutral, sad)",
  "tts_text": "string (The actual words the robot will say)",
  "gait_cmd": "string (e.g., forward, backward, turn_left, None)",
  "confidence": float (0.0 to 1.0),
  "fallback": "string (fallback plan)"
}
"""

def chat_with_hylion():
    print("=" * 50)
    print("🤖 HYlion Brain is ONLINE.")
    print("Type your message (or type 'quit' / 'exit' to stop)")
    print("=" * 50)

    chat_history = [{"role": "system", "content": system_prompt}]

    while True:
        # 1. Keyboard Mic (User Input)
        user_input = input("\n[Keyboard Mic (You)]: ")
        
        if user_input.lower() in ['quit', 'exit']:
            print("\nShutting down HYlion brain... Goodbye!")
            break

        chat_history.append({"role": "user", "content": user_input})

        try:
            # 2. LLM Processing (Groq LLaMA3)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=chat_history,
                temperature=0.2, # Low temperature for strict JSON formatting
                response_format={"type": "json_object"}
            )

            llm_output = response.choices[0].message.content
            
            # Parse JSON
            parsed_json = json.loads(llm_output)
            
            # Overwrite auto-generated fields for robustness
            parsed_json["action_id"] = str(uuid.uuid4())
            parsed_json["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # 3. Terminal Speaker (Output)
            print("-" * 50)
            print(f"🔊 [Terminal Speaker]: {parsed_json.get('tts_text', '')}")
            print("-" * 50)
            
            print("⚙️  [Action Schema Output]:")
            print(json.dumps(parsed_json, indent=2))

            # Add to memory
            chat_history.append({"role": "assistant", "content": llm_output})

        except Exception as e:
            print(f"\n[ERROR]: {e}")

if __name__ == "__main__":
    chat_with_hylion()