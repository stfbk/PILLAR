import json
import google.generativeai as genai
import random
from openai import OpenAI
from misc.utils import (
    match_number_color,
    match_letter,
)
from llms.prompts import (
    LINDDUN_GO_SYSTEM_PROMPT,
    LINDDUN_GO_SPECIFIC_PROMPTS,
    LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT,
    LINDDUN_GO_JUDGE_PROMPT,
)

# Function to convert JSON to Markdown for display.
def linddun_go_gen_markdown(present_threats):
    markdown_output = "## Threats identified with LINDDUN Go\n\n"

    # Start the markdown table with headers
    markdown_output += "| Threat Name | Threat description | Detection reason |\n"
    markdown_output += "|-------------|--------------------|------------------|\n"

    # Fill the table rows with the threat model data
    for threat in present_threats:
        color = match_number_color(threat["threat_type"])
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{match_letter(threat['threat_type'])} - {threat['threat_title']}</p> | {threat['threat_description']} | {threat['reason']} |\n"


    return markdown_output

def get_deck(file="misc/deck.json"):
    with open(file, 'r') as deck_file:
        deck = json.load(deck_file)
    return deck["cards"]


def get_linddun_go(api_key, model_name, inputs):
    client = OpenAI(api_key=api_key)
    deck = get_deck()
    

    present_threats = []

    for elem in deck:
        question = "\n".join(elem["questions"])
        title = elem["title"]
        description = elem["description"]
        type = elem["type"]
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            temperature=0.01,
            messages=[
                {
                    "role": "system",
                    "content": LINDDUN_GO_SPECIFIC_PROMPTS[0]+LINDDUN_GO_SYSTEM_PROMPT,
                }, {"role": "user", "content": 
                 f"""
'''
APPLICATION TYPE: {inputs["app_type"]}
AUTHENTICATION METHODS: {inputs["authentication"]}
APPLICATION DESCRIPTION: {inputs["app_description"]}
DATABASE_SCHEMA: {inputs["database"]}
DATA POLICY: {inputs["data_policy"]}
QUESTIONS: {question}
THREAT_TITLE: {title}
THREAT_DESCRIPTION: {description}
'''
                """
                },
            ],
            max_tokens=4096,
        )
        # Convert the JSON string in the 'content' field to a Python dictionary
        response_content = json.loads(response.choices[0].message.content)
        response_content["question"] = question
        response_content["threat_title"] = title
        response_content["threat_description"] = description
        response_content["threat_type"] = type
        #print(response_content)
        if response_content["reply"]:
            present_threats.append(response_content)

    return present_threats


def get_multiagent_linddun_go(api_key, model_name, inputs, rounds, threats_to_analyze):

    client = OpenAI(api_key=api_key)
    present_threats = []
    deck = get_deck()
    random.shuffle(deck)


    for elem in deck[0:threats_to_analyze]:
        question = "\n".join(elem["questions"])
        title = elem["title"]
        description = elem["description"]
        type = elem["type"]
        previous_analysis = [{} for _ in range(6)]
        for round in range(rounds):
            for i in elem["competent_agents"]:
                response = client.chat.completions.create(
                    model=model_name,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": LINDDUN_GO_SPECIFIC_PROMPTS[i]+LINDDUN_GO_SYSTEM_PROMPT+(LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis) if previous_analysis[i] else ""),
                        },
                        {"role": "user", "content": 
                        f"""
        '''
        APPLICATION TYPE: {inputs["app_type"]}
        AUTHENTICATION METHODS: {inputs["authentication"]}
        APPLICATION DESCRIPTION: {inputs["app_description"]}
        DATABASE_SCHEMA: {inputs["database"]}
        DATA POLICY: {inputs["data_policy"]}
        QUESTIONS: {question}
        THREAT_TITLE: {title}
        THREAT_DESCRIPTION: {description}
        '''
                        """
                        },
                    ],
                    max_tokens=4096,
                )
                response_content = json.loads(response.choices[0].message.content)
                
                previous_analysis[i] = response_content
                #print(response_content)
        #print(previous_analysis)
        final_verdict = judge(api_key, model_name, previous_analysis)
        final_verdict["question"] = question
        final_verdict["threat_title"] = title
        final_verdict["threat_description"] = description
        final_verdict["threat_type"] = type
        #print(final_verdict)
        present_threats.append(final_verdict)
    #print(f"Present threats:\n{present_threats}")

    return present_threats


def judge(api_key, model_name, previous_analysis):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        response_format={"type": "json_object"},
        temperature=0.01,
        messages=[
            {
                "role": "system",
                "content": LINDDUN_GO_JUDGE_PROMPT,
            },
            {
                "role": "user", 
                "content": LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis)
            },
        ],
        max_tokens=4096,
    )
    response_content=json.loads(response.choices[0].message.content)
    return response_content