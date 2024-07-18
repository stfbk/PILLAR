import json
from openai import OpenAI
from llms.prompts import (
    THREAT_MODEL_USER_PROMPT,
    DFD_SYSTEM_PROMPT,
)

def get_dfd(api_key, model, temperature, inputs):
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": DFD_SYSTEM_PROMPT,
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(
                    inputs
                )
            },
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)
    
