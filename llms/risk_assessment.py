import json
from openai import OpenAI
from llms.prompts import THREAT_MODEL_USER_PROMPT
from misc.utils import (
    match_number_color,
    match_category_number,
)

def assessment_gen_markdown(assessment):
    markdown_output = "| Impact |\n"
    markdown_output += "|--------|\n"
    markdown_output += f"| {assessment['impact']} |\n"

    return markdown_output

def linddun_pro_gen_individual_markdown(threat):
    markdown_output = "| Category| Description |\n"
    markdown_output += "|------|-------------|\n"

    # Fill the table rows with the threat model data
    color = match_number_color(match_category_number(threat["category"]))
    color_html = f"<p style='background-color:{color};color:#ffffff;'>"
    markdown_output += f"| {color_html}{threat['category']}</p> | {threat["description"]} |\n"
    return markdown_output

def measures_gen_markdown(measures):
    markdown_output = "| Title | Explanation | Implementation |\n"
    markdown_output += "|--------|-------|-----|\n"

    for measure in measures:
        markdown_output += f"| [{measure['title']}](https://privacypatterns.org/patterns/{measure["filename"]}) | {measure['explanation']} | {measure['implementation']} |\n"
    return markdown_output
    
def get_assessment(api_key, model, threat, inputs):
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a risk assessment expert with 20 years of experience in the field.
Given an application description and a potential threat detected in the
application, you have to provide your opinion on the impact the threat might have, in a JSON response.

Be specific and tailored to the application and threat provided. The response
should be detailed and actionable, providing a clear understanding of the
threat.

The input is structured as follows, enclosed in triple quotes:
'''
APPLICATION TYPE: Web | Mobile | Desktop | Cloud | IoT | Other application
AUTHENTICATION METHODS: SSO | MFA | OAUTH2 | Basic | None
APPLICATION DESCRIPTION: the general application description, sometimes with a Data Flow Diagram
DATABASE SCHEMA: the database schema used by the application to contain the
data, or none if no database is used, in this JSON format:
{[
{
	'data_type': 'Name',
	'encryption': True,
	'sensitive': True,
	'notes': 'Collected only once'
},
{
	'data_type': 'Email',
	'encryption': True,
	'sensitive': False,
	'notes': ''
},
]}
DATA POLICY: the data policy of the application
'''

The threat is structured as follows, enclosed in triple quotes:

'''
THREAT: the threat detected in the application
'''

The JSON output MUST be structured as follows:
{
    "impact": "5 - the threat's potential impact is moderate because......",
}

""",
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(inputs) + f"""
                
'''
THREAT: {threat}
'''
""",
            },
        ],
        max_tokens=4096,
    )
    return json.loads(response.choices[0].message.content)


def choose_control_measures(api_key, model, threat, inputs):
    client = OpenAI(api_key=api_key)
    with open("privacypatterns.json", "r") as f:
        patterns = json.load(f)
        # for each pattern inside the "patterns" list, keep only "title", "excerpt" and "Related Patterns"
        patterns = [{"title": p["title"], "excerpt": p["excerpt"], "related_patterns": p["sections"]["Related Patterns"] if "Related Patterns" in p["sections"] else None} for p in patterns["patterns"]]
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a privacy expert with 20 years of experience in the field.
Given an application description and a potential threat detected in the
application, you have to provide control measures to mitigate the threat, based
on the privacy patterns provided. The response should be detailed and actionable,
providing a clear understanding of the threat and the possible mitigation strategies.

The input is structured as follows, enclosed in triple quotes:
'''
APPLICATION TYPE: Web | Mobile | Desktop | Cloud | IoT | Other application
AUTHENTICATION METHODS: SSO | MFA | OAUTH2 | Basic | None
APPLICATION DESCRIPTION: the general application description, sometimes with a Data Flow Diagram
DATABASE SCHEMA: the database schema used by the application to contain the
data, or none if no database is used, in this JSON format:
{[
{
    'data_type': 'Name',
    'encryption': True,
    'sensitive': True,
    'notes': 'Collected only once'
},
{
    'data_type': 'Email',
    'encryption': True,
    'sensitive': False,
    'notes': ''
},
]}
DATA POLICY: the data policy of the application
'''

The threat is structured as follows, enclosed in triple quotes:
'''
THREAT: the threat detected in the application
'''

The privacy patterns are provided as follows, enclosed in triple quotes:
'''
PATTERNS: [
    {
        "title": "Pattern Title",
        "excerpt": "Pattern excerpt",
        "related_patterns": "some patterns related to this one, if applicable"
    },
    {
        "title": "Pattern Title",
        "excerpt": "Pattern excerpt",
        "related_patterns": "some patterns related to this one, if applicable"
    }
]

The "measures" array should contain ONLY and EXACTLY the names of the chosen privacy patterns to mitigate the threat. The names should be precise and match the ones in the "title" field of the privacy patterns provided.
The JSON output MUST be structured as follows:
{
    "measures": ["Title 1", "Title 2", // as many as needed ]
}
""",
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(inputs) + f"""
'''
THREAT: {threat}
'''

'''
PATTERNS: {json.dumps(patterns)}
'''
""",
            },
        ],
        max_tokens=4096,
    )
    return json.loads(response.choices[0].message.content)["measures"]


def get_control_measures(api_key, model, threat, inputs):
    measures = choose_control_measures(api_key, model, threat, inputs)
    chosen = []
    with open("privacypatterns.json", "r") as f:
        patterns = json.load(f)["patterns"]

    for pattern in patterns:
        if pattern["title"] in measures:
            chosen.append(pattern)
    

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a privacy expert with 20 years of experience in the field.
Given an application description and a potential threat detected in the
application, you have to provide a detailed explanation of the chosen privacy
patterns (control measures) to mitigate the threat. The response should be detailed and actionable,
providing a clear understanding of the threat and the possible mitigation strategies.
You should also suggest how to implement the chosen patterns in the application.

The input is structured as follows, enclosed in triple quotes:
'''
APPLICATION TYPE: Web | Mobile | Desktop | Cloud | IoT | Other application
AUTHENTICATION METHODS: SSO | MFA | OAUTH2 | Basic | None
APPLICATION DESCRIPTION: the general application description, sometimes with a Data Flow Diagram
DATABASE SCHEMA: the database schema used by the application to contain the
data, or none if no database is used, in this JSON format:
{[
{
    'data_type': 'Name',
    'encryption': True,
    'sensitive': True,
    'notes': 'Collected only once'
},
{
    'data_type': 'Email',
    'encryption': True,
    'sensitive': False,
    'notes': ''
},
]}
DATA POLICY: the data policy of the application
'''

The threat is structured as follows, enclosed in triple quotes:
'''
THREAT: the threat detected in the application
'''

The chosen privacy patterns are provided as follows, enclosed in triple quotes:
'''
PATTERNS: [
    {
        "title": "Pattern Title",
        "excerpt": "Pattern excerpt",
        "sections": {
            /// detailed sections of the pattern, including context, examples, implementation, context etc.
        }
    },
    /// other patterns used
]
'''

The JSON output MUST be structured as follows:
{
    "measures": [
        {
            "filename": "Pattern Filename",
            "title": "Pattern Title",
            "explanation": "A detailed explanation of the pattern and how it mitigates the threat.",
            "implementation": "Suggested implementation of the pattern in the application."
        },
        /// other patterns used
    ]
}
The "explanation" and "implementation" fields should be detailed and tailored to the application and threat provided, and should be about 100 words long each.
""",
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(inputs) + f"""
'''
THREAT: {threat}
'''

'''
PATTERNS: {
    json.dumps(chosen)
}
'''
""",
            },
        ],
        max_tokens=4096,
    )
    return json.loads(response.choices[0].message.content)["measures"]

