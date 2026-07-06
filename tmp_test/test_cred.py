import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
import yaml

# Load the actual config
config_path = "marble/configs/test_config/werewolf_config/werewolf_config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Test all credential sources
print("=== Config Credential Verification ===")
print(f"Top-level openai_api_key: {config.get('openai_api_key', 'MISSING')[:20]}...")
print(f"villager_config api_key:  {config['villager_config']['api_key'][:20]}...")
print(f"villager_config base_url: {config['villager_config']['base_url']}")
print(f"villager_config model:    {config['villager_config']['model_name']}")
print(f"werewolf_config api_key:  {config['werewolf_config']['api_key'][:20]}...")
print(f"werewolf_config base_url: {config['werewolf_config']['base_url']}")
print(f"werewolf_config model:    {config['werewolf_config']['model_name']}")
print(f"eval_config api_key:      {config['eval_config']['api_key'][:20]}...")
print(f"eval_config base_url:     {config['eval_config']['base_url']}")
print(f"eval_config model:        {config['eval_config']['model_name']}")

# Test each credential source works
for label, creds in [
    ("villager_config", config["villager_config"]),
    ("werewolf_config", config["werewolf_config"]),
    ("eval_config", config["eval_config"]),
]:
    print(f"\n=== Testing {label} ===")
    client = OpenAI(base_url=creds["base_url"], api_key=creds["api_key"])
    try:
        resp = client.chat.completions.create(
            model=creds["model_name"],
            messages=[{"role": "user", "content": "Say exactly: OK"}],
            max_tokens=50,
        )
        msg = resp.choices[0].message.content
        print(f"  Text: '{msg}' ✓")
    except Exception as e:
        print(f"  Text FAILED: {e}")

    try:
        resp = client.chat.completions.create(
            model=creds["model_name"],
            messages=[{"role": "user", "content": "Use the test tool."}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"input": {"type": "string"}},
                        "required": ["input"]
                    }
                }
            }],
            tool_choice="auto",
            max_tokens=200,
        )
        tc = resp.choices[0].message.tool_calls
        status = f"Tool call: {tc[0].function.name}" if tc else "No tool call"
        print(f"  Tools: {status} ✓")
    except Exception as e:
        print(f"  Tools FAILED: {e}")
