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
                
THREAT: {threat['Scenario']}
REASON: {threat['Reason']}
PERCEIVED_IMPACT: {threat['perceived_impact'] if 'perceived_impact' in threat else ''}
PERCEIVED_LIKELIHOOD: {threat['perceived_likelihood'] if 'perceived_likelihood' in threat else ''}
IMPLEMENTED_MEASURES: {threat['measures'] if 'measures' in threat else ''}
""",
            },
        ],
        max_tokens=4096,
    )
    print(THREAT_MODEL_USER_PROMPT(inputs) + f"""
                
THREAT: {threat['Scenario']}
REASON: {threat['Reason']}
PERCEIVED_IMPACT: {threat['perceived_impact'] if 'perceived_impact' in threat else ''}
PERCEIVED_LIKELIHOOD: {threat['perceived_likelihood'] if 'perceived_likelihood' in threat else ''}
IMPLEMENTED_MEASURES: {threat['measures'] if 'measures' in threat else ''}
""")
    return json.loads(response.choices[0].message.content)

