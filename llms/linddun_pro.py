import json
import requests
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
        markdown_output += f"| {color_html}{threat['category']}</p> | {threat["source_id"].strip()} <br> {threat['source']} | {threat["data_flow_id"].strip()} <br> {threat['data_flow']} | {threat["destination_id"].strip()} <br> {threat['destination']} |\n"
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


def get_linddun_pro(api_key, model, dfd, edge, category, description, temperature):
    client = OpenAI(api_key=api_key)
    
    source, data_flow, destination = mapping_table(edge, category)
    
    tree = threat_tree(category)
    
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
                "content": LINDDUN_PRO_USER_PROMPT(dfd, edge, category, description, source, data_flow, destination, tree),
            },
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    threat = json.loads(response.choices[0].message.content)
    threat["category"] = category
    return threat


def threat_tree(category):
    response = requests.get("https://downloads.linddun.org/linddun-trees/structured/json/v240118/trees.json").json()

    full_tree = None
    for item in response:
        if item["name"].lower() == category.lower():
            full_tree = item
    if not full_tree:
        print("Wrong category!")
        return None

    tree = {}
    tree = build_tree(tree, full_tree)

    return tree

def build_tree(tree, full_tree):
    tree["name"] = full_tree["name"]
    tree["id"] = full_tree["id"]
    if full_tree["fullDescription"]:
        tree["description"] = full_tree["fullDescription"]
    else:
        tree["description"] = full_tree["description"]
    tree["children"] = []
    for child in full_tree["children"]:
        tree["children"].append(build_tree({}, child))
    
    return tree
