import os
from openai import OpenAI

RITS_API_KEY = os.getenv("RITS_API_KEY", "09d751acf574fe362cc1f3c2b5f8ad28")

client = OpenAI(
    api_key="dummy",
    base_url="https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/moonshotai-kimi-k2-7/v1",
    default_headers={
        "RITS_API_KEY": RITS_API_KEY,
        "accept": "application/json",
    },
)

full_task_description = """Software Development Task:

Please write a Python program called 'SimpleCalculator' that supports addition, subtraction, multiplication, and division of two numbers. The program should handle invalid inputs gracefully (e.g., division by zero, non-numeric input) and include a simple command-line interface.

1. Implementation requirements:
   - Implement functions for add, subtract, multiply, and divide.
   - Handle division by zero with an appropriate error message.
   - Provide a simple CLI that prompts the user for two numbers and an operation.
   - Include basic input validation.

2. Project structure:
   - solution.py (main implementation)

3. Development process:
   - Developer: Create the code.
   - Developer: Revise the code.

Please work together to complete this task following software engineering best practices."""

requirements = """   - Implement functions for add, subtract, multiply, and divide.
   - Handle division by zero with an appropriate error message.
   - Provide a simple CLI that prompts the user for two numbers and an operation.
   - Include basic input validation."""

system_prompt = (
    "You are a Python developer. Create a solution based on the following task description.\n"
    "Your code should be clean, well-documented, and follow Python best practices.\n"
    "Include explanations of the code and its functionality as inline comments within the code.\n"
    "Your final output must be enclosed in a markdown code block with the language specified as python.\n"
    "Ensure that nothing besides the code is inside the markdown code block.\n"
    f"Task Description:\n{full_task_description}\n\n"
    f"Implementation Requirements:\n{requirements}\n"
)


def test_param(token_param: str, token_value: int):
    print(f"\n=== Testing {token_param}={token_value} ===")
    kwargs = {
        "model": "moonshotai/Kimi-K2.7-Code",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please write the complete Python code for this task."},
        ],
        "temperature": 0.0,
    }
    kwargs[token_param] = token_value
    response = client.chat.completions.create(**kwargs)
    msg = response.choices[0].message
    print(f"content length: {len(msg.content or '')}")
    print(f"content preview: {repr((msg.content or '')[:200])}")
    print(f"usage: {response.usage}")
    return msg.content


for param in ["max_tokens", "max_completion_tokens"]:
    for value in [4096, 8192]:
        try:
            test_param(param, value)
        except Exception as e:
            print(f"ERROR: {e}")
