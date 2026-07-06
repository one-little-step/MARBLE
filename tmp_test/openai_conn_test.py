from openai import OpenAI

def hello_world(
    api_key: str,
    base_url: str,
    model: str = "gpt-4o-mini"
) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url.rstrip("/")
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "Hello World"}
        ]
    )

    return response.choices[0].message.content


# Example
if __name__ == "__main__":
    print(
        hello_world(
            api_key="09d751acf574fe362cc1f3c2b5f8ad28",
            base_url="https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/llama-3-3-70b-instruct/v1",
            model="meta-llama/llama-3-3-70b-instruct"
        )
    )