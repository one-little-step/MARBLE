import os
from openai import OpenAI


def hello_world_rits(
    rits_api_key: str,
    model: str = "moonshotai/Kimi-K2.7-Code",
) -> str:
    client = OpenAI(
        api_key="dummy",  # required by SDK, but RITS uses RITS_API_KEY header
        base_url="https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/moonshotai-kimi-k2-7/v1",
        default_headers={
            "RITS_API_KEY": rits_api_key,
            "accept": "application/json",
        },
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Hello world",
            }
        ],
        temperature=0,
        max_tokens=128,
    )

    return response.choices[0].message.content or ""


if __name__ == "__main__":
    # RITS_API_KEY = os.getenv("RITS_API_KEY")
    RITS_API_KEY = "09d751acf574fe362cc1f3c2b5f8ad28"  # Replace with your actual RITS API key

    if not RITS_API_KEY:
        raise RuntimeError("Please set RITS_API_KEY environment variable")

    print(hello_world_rits(RITS_API_KEY))