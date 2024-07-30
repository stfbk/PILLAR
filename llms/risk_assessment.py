import json
from openai import OpenAI
from llms.prompts import THREAT_MODEL_USER_PROMPT

def assessment_gen_markdown(assessment):
    markdown_output = "| Impact | Likelihood |\n"
    markdown_output += "|--------|------------|\n"
    markdown_output += f"| {assessment['impact']} | {assessment['likelihood']} | "
    markdown_output += "|-----------------|\n"
    markdown_output += "| Control Measures |\n"
    markdown_output += "|-----------------|\n | "

    for measure in assessment['control']:
        markdown_output += f"{measure} <br> "
    markdown_output += "|\n"
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
application, you have to provide your opinion on the impact, likelihood, and
possible control measures for the threat, in a JSON response.
Impact and likelihood should be in a scale from 1 to 10, with 1 being the
lowest and 10 being the highest. 

Be specific and tailored to the application and threat provided. The response
should be detailed and actionable, providing a clear understanding of the
threat and the possible mitigation strategies.

The user might provide a perceived impact and likelihood of the threat, which
you have to take into account when providing your assessment. The user might
also provide the measures already implemented to mitigate the threat, which you
should consider when providing your assessment. If the implemented measures are
satisfying and useful, you should decrease the impact and likelyhood. In any
case, you have to provide your expert opinion, which usually is similar to the user's.

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
REASON: the reason for the threat detection
PERCEIVED_IMPACT: (optional) the perceived impact of the threat from the user, in a scale from 1 to 10
PERCEIVED_LIKELIHOOD: (optional) the perceived likelihood of the threat from the user, in a scale from 1 to 10
IMPLEMENTED_MEASURES: (optional) the measures already implemented to mitigate the threat. if they are useful, you should consider them when providing your assessment and lowering the impact and likelihood
'''

The JSON output MUST be structured as follows:
{
    "impact": "5 - the threat's potential impact is moderate because......",
    "likelihood": "7 - the threat is likely to happen because ......",
    "control": ["Detailed control measure to mitigate the threat.", "Another control measure.", // as many as needed ]
}

""",
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(inputs) + f"""
                
THREAT: {threat['Scenario'] if 'Scenario' in threat else threat['threat_title'] + ' - ' + threat['threat_description']}
REASON: {threat['Reason'] if 'Reason' in threat else threat['reason']}
PERCEIVED_IMPACT: {threat['perceived_impact'] if 'perceived_impact' in threat else ''}
PERCEIVED_LIKELIHOOD: {threat['perceived_likelihood'] if 'perceived_likelihood' in threat else ''}
IMPLEMENTED_MEASURES: {threat['measures'] if 'measures' in threat else ''}
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
REASON: the reason for the threat detection
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
THREAT: {threat['Scenario'] if 'Scenario' in threat else threat['threat_title'] + ' - ' + threat['threat_description']}
REASON: {threat['Reason'] if 'Reason' in threat else threat['reason']}
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
REASON: the reason for the threat detection
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
THREAT: {threat['Scenario'] if 'Scenario' in threat else threat['threat_title'] + ' - ' + threat['threat_description']}
REASON: {threat['Reason'] if 'Reason' in threat else threat['reason']}
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

