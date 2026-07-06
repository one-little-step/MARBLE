import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from marble.llms.model_prompting import model_prompting

CREATE_SOLUTION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_solution",
        "description": "Create the initial solution.py file for a coding task.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Description of the coding task",
                },
                "model_name": {"type": "string"},
            },
            "required": ["task_description", "model_name"],
        },
    },
}

messages = [
    {
        "role": "system",
        "content": "You are a Senior Software Developer specialized in Python development.",
    },
    {
        "role": "user",
        "content": "Please write a Python program called 'SimpleCalculator' that supports addition, subtraction, multiplication, and division of two numbers.",
    },
]

result = model_prompting(
    llm_model="moonshotai/Kimi-K2.7-Code",
    messages=messages,
    tools=[CREATE_SOLUTION_TOOL],
    tool_choice="auto",
    max_token_num=4096,
)

print("RESULT:")
for msg in result:
    print(f"  content: {msg.content!r}")
    print(f"  role: {msg.role}")
    print(f"  tool_calls: {msg.tool_calls}")
