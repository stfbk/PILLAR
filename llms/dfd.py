import json
from openai import OpenAI
from llms.prompts import THREAT_MODEL_USER_PROMPT

def get_dfd(api_key, model, temperature, inputs):
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a senior system architect with more than 20 years of
experience in the field. You are tasked with creating a Data
Flow Diagram (DFD) for a new application, such that privacy
threat modelling can be executed upon it. 

The input is going to be structured as follows, enclosed in triple quotes:
'''
APPLICATION TYPE: the type of application (web, mobile, desktop, etc.)
AUTHENTICATION METHODS: the authentication methods supported (password, 2FA, etc.)
APPLICATION DESCRIPTION: the application description
DATABASE_SCHEMA: the database schema used by the application to contain the data, or none if no database is used
DATA POLICY: the data policy of the application
'''

You MUST reply with a json-formatted list of dictionaries under the "dfd"
attribute, where each dictionary represents an edge in the DFD. The response
MUST have the following structure:
{
    "dfd": [
        {
            "from": "source_node",
            "typefrom": "Entity/Process/Data store",
            "to": "destination_node",
            "typeto": "Entity/Process/Data store",
            "bidirectional": true/false
        },
        //// other edges description....
    ]
}
Provide a comprehensive list, including as many nodes of the application as possible.
                """,
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
    
