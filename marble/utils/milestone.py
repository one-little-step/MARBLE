import os
import time

import yaml

from marble.llms.client_factory import get_model_name, get_openai_client


def generate_task_milestones(task_description, client=None):
    """
    Generate milestones for a given task by calling the LLM.

    Args:
        task_description (str): The description of the main task to break down.
        client: Optional OpenAI client instance. If not provided, one is created
                from the active ``LLM_SOURCE`` environment configuration.

    Returns:
        list or None: Returns a list of milestones if successful, otherwise None.
    """

    # Load the prompt data from YAML file
    try:
        with open("marble/utils/milestone_prompt.yaml", "r") as file:
            prompt_data = yaml.safe_load(file)
    except FileNotFoundError:
        print("Error: milestone_prompt.yaml file not found.")
        return None

    # Extract system and user prompts and tool configuration
    system_prompt = prompt_data["prompts"]["task_breakdown"]["sys_prompt"]
    user_template = prompt_data["prompts"]["task_breakdown"]["user"]
    tool = prompt_data["tools"][0]

    # Format the user prompt with the task description
    user_prompt = user_template.replace("<<task_description>>", task_description)

    # Prepare the messages for the GPT tool call
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if client is None:
        client = get_openai_client()

    # Define the tool call function with retry mechanism
    rounds = 0
    while rounds < 3:
        rounds += 1
        try:
            response = client.chat.completions.create(
                model=get_model_name(),
                messages=messages,
                tools=[tool],
                tool_choice="auto",
                temperature=0.0,
                n=1,
            )
            return response.choices[0].message.tool_calls
        except Exception as e:
            print(f"Attempt {rounds}: Error in generating milestones - {e}")
            time.sleep(5)

    print("Error: Chat Completion failed too many times.")
    return None
