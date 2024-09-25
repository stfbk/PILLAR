# Copyright 2024 Fondazione Bruno Kessler
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
from openai import OpenAI
from llms.prompts import CHOOSE_CONTROL_MEASURES_PROMPT, EXPLAIN_CONTROL_MEASURES_PROMPT, IMPACT_ASSESSMENT_PROMPT, THREAT_MODEL_USER_PROMPT
from misc.utils import (
    match_number_color,
    match_category_number,
)
from pydantic import BaseModel

def assessment_gen_markdown(assessment):
    """
    This function generates a markdown table from the assessment data.

    Args:
        assessment (dict): The assessment data. The dictionary has the following
            keys:
            - impact: string. The impact of the threat.
    
    Returns:
        str: The markdown table with the assessment data.
    """
    markdown_output = "| Impact |\n"
    markdown_output += "|--------|\n"
    markdown_output += f"| {assessment['impact']} |\n"

    return markdown_output

def linddun_pro_gen_individual_markdown(threat):
    """
    This function generates a markdown table from a single threat in the LINDDUN Pro threat model.
    
    Args:
        threat (dict): The threat in the threat model. The dictionary has the following keys:
            - category: string. The category of the threat.
            - description: string. The description of the threat.
    """
    markdown_output = "| Category| Description |\n"
    markdown_output += "|------|-------------|\n"

    color = match_number_color(match_category_number(threat["category"]))
    color_html = f"<p style='background-color:{color};color:#ffffff;'>"
    markdown_output += f"| {color_html}{threat['category']}</p> | {threat["description"]} |\n"
    return markdown_output

def measures_gen_markdown(measures):
    """
    This function generates a markdown table from the control measures data.

    Args:
        measures (list): The list of control measures. Each measure is a dictionary with the following
            keys:
            - title: string. The title of the measure.
            - explanation: string. The explanation of the measure.
            - implementation: string. The implementation of the measure.
    
    Returns:
        str: The markdown table with the control measures data.
    """
    markdown_output = "| Title | Explanation | Implementation |\n"
    markdown_output += "|--------|-------|-----|\n"

    for measure in measures:
        markdown_output += f"| [{measure['title']}](https://privacypatterns.org/patterns/{measure["filename"]}) | {measure['explanation']} | {measure['implementation']} |\n"
    return markdown_output
    


def get_assessment(api_key, model, threat, inputs, temperature):
    """
    This function generates an assessment for a threat.
    
    Args:
        api_key (str): The OpenAI API key.
        model (str): The OpenAI model to use.
        threat (dict): The threat to assess. Any dictionary is accepted, since it will be converted to a string and passed to the model.
        inputs (dict): The dictionary of inputs to the application, with the same keys as the "input" session state in the Application Info tab.
        temperature (float): The temperature to use for the model.

    Returns:
        dict: The assessment data. The dictionary has the following keys:
            - impact: string. The impact of the threat.
    """
    client = OpenAI(api_key=api_key)
    
    messages=[
        {
            "role": "system",
            "content": IMPACT_ASSESSMENT_PROMPT,
        },
        {
            "role": "user", 
            "content": THREAT_MODEL_USER_PROMPT(inputs) + f"""
            
'''
THREAT: {threat}
'''
""",
        },
    ]
    
    if model in ["gpt-4o", "gpt-4o-mini"]:
        class Assessment(BaseModel):
            impact: str
        response = client.beta.chat.completions.parse(
            model=model,
            response_format=Assessment,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
    return json.loads(response.choices[0].message.content)


def choose_control_measures(api_key, model, threat, inputs, temperature):
    """
    This function generates a list of control measures which could be useful for a threat, out of the full list of [privacy patterns](https://privacypatterns.org/).
    
    Args:
        api_key (str): The OpenAI API key.
        model (str): The OpenAI model to use.
        threat (dict): The threat to assess. Any dictionary is accepted, since it will be converted to a string and passed to the model.
        inputs (dict): The dictionary of inputs to the application, with the same keys as the "input" session state in the Application Info tab.
        temperature (float): The temperature to use for the model.
    
    Returns:
        list: The list of control measures. Each measure is a string, the title of the chosen privacy pattern.
    """
    client = OpenAI(api_key=api_key)
    with open("misc/privacypatterns.json", "r") as f:
        patterns = json.load(f)
        # for each pattern inside the "patterns" list, keep only "title", "excerpt" and "Related Patterns"
        patterns = [{"title": p["title"], "excerpt": p["excerpt"], "related_patterns": p["sections"]["Related Patterns"] if "Related Patterns" in p["sections"] else None} for p in patterns["patterns"]]
    messages=[
        {
            "role": "system",
            "content": CHOOSE_CONTROL_MEASURES_PROMPT,
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
    ]
    
    if model in ["gpt-4o", "gpt-4o-mini"]:
        class Measures(BaseModel):
            measures: list[str]
        response = client.beta.chat.completions.parse(
            model=model,
            response_format=Measures,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
    return json.loads(response.choices[0].message.content)["measures"]


def get_control_measures(api_key, model, threat, inputs, temperature):
    """
    This function generates a list of control measures which could be useful for a threat and explains why they are useful and how to implement them.
    
    Args:
        api_key (str): The OpenAI API key.
        model (str): The OpenAI model to use.
        threat (dict): The threat to assess. Any dictionary is accepted, since it will be converted to a string and passed to the model.
        inputs (dict): The dictionary of inputs to the application, with the same keys as the "input" session state in the Application Info tab.
        temperature (float): The temperature to use for the model.
    
    Returns:
        list: The list of control measures. Each measure is a dictionary with the following keys:
            - filename: string. The filename of the measure.
            - title: string. The title of the measure.
            - explanation: string. The explanation of the measure.
            - implementation: string. The implementation of the measure.
    """
    measures = choose_control_measures(api_key, model, threat, inputs, temperature)
    chosen = []
    with open("misc/privacypatterns.json", "r") as f:
        patterns = json.load(f)["patterns"]

    for pattern in patterns:
        if pattern["title"] in measures:
            chosen.append(pattern)
    

    client = OpenAI(api_key=api_key)
    messages=[
        {
            "role": "system",
            "content": EXPLAIN_CONTROL_MEASURES_PROMPT,
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
    ]
    
    if model in ["gpt-4o", "gpt-4o-mini"]:
        class Measure(BaseModel):
            filename: str
            title: str
            explanation: str
            implementation: str
        class Measures(BaseModel):
            measures: list[Measure]

        response = client.beta.chat.completions.parse(
            model=model,
            response_format=Measures,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
    return json.loads(response.choices[0].message.content)["measures"]

