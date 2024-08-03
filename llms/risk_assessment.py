import json
from openai import OpenAI
from llms.prompts import CHOOSE_CONTROL_MEASURES_PROMPT, EXPLAIN_CONTROL_MEASURES_PROMPT, IMPACT_ASSESSMENT_PROMPT, THREAT_MODEL_USER_PROMPT
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
    
def get_assessment(api_key, model, threat, inputs, temperature):
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
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
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)


def choose_control_measures(api_key, model, threat, inputs, temperature):
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
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)["measures"]


def get_control_measures(api_key, model, threat, inputs, temperature):
    measures = choose_control_measures(api_key, model, threat, inputs, temperature)
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
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)["measures"]

