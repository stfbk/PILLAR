import json
from openai import OpenAI
from misc.utils import (
    match_category_number,
    match_number_color,
)
from llms.prompts import (
    LINDDUN_PRO_SYSTEM_PROMPT,
    LINDDUN_PRO_USER_PROMPT,
)

def linddun_pro_gen_markdown(threats):
    # Start the markdown table with headers
    markdown_output = "| Category| Threat at source | Threat at data flow | Threat at destination |\n"
    markdown_output += "|------|-------------|--------------------|------------------|\n"

    # Fill the table rows with the threat model data
    for threat in threats:
        color = match_number_color(match_category_number(threat["category"]))
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{threat['category']}</p> | {threat['source']} | {threat['data_flow']} | {threat['destination']} |\n"
    return markdown_output

def mapping_table(edge, category):
    table = [
        {"from": "Process", "to": "Process", "Linking": (True, True, True), "Identifying": (True, True, True), "Non-repudiation": (True, True, True), "Detecting": (True, True, False), "Data disclosure": (True, True, True), "Unawareness and unintervenability": (True, False, True), "Non-compliance": (True, False, True)},
        {"from": "Process", "to": "Data store", "Linking": (True, True, True), "Identifying": (True, True, True), "Non-repudiation": (True, True, True), "Detecting": (True, True, False), "Data disclosure": (True, True, True), "Unawareness and unintervenability": (True, False, True), "Non-compliance": (True, False, True)},
        {"from": "Process", "to": "Entity", "Linking": (True, True, True), "Identifying": (True, True, True), "Non-repudiation": (True, True, True), "Detecting": (True, True, False), "Data disclosure": (True, True, True), "Unawareness and unintervenability": (True, False, True), "Non-compliance": (True, False, True)},
        {"from": "Data store", "to": "Process", "Linking": (True, True, True), "Identifying": (True, True, True), "Non-repudiation": (True, True, True), "Detecting": (True, True, False), "Data disclosure": (True, True, True), "Unawareness and unintervenability": (True, False, True), "Non-compliance": (True, False, True)},
        {"from": "Entity", "to": "Process", "Linking": (True, True, True), "Identifying": (True, True, True), "Non-repudiation": (True, True, True), "Detecting": (True, True, False), "Data disclosure": (True, True, True), "Unawareness and unintervenability": (True, False, True), "Non-compliance": (False, False, True)},
    ]
    
    for row in table:
        if row["from"] == edge["typefrom"] and row["to"] == edge["typeto"]:
            return row[category]
    return (True, True, True)


def get_linddun_pro(api_key, model, dfd, edge, category, description):
    client = OpenAI(api_key=api_key)
    
    source, data_flow, destination = mapping_table(edge, category)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": LINDDUN_PRO_SYSTEM_PROMPT,
            },
            {
                "role": "user", 
                "content": LINDDUN_PRO_USER_PROMPT(dfd, edge, category, description, source, data_flow, destination),
            },
        ],
        max_tokens=4096,
    )
    threat = json.loads(response.choices[0].message.content)
    threat["category"] = category
    return threat