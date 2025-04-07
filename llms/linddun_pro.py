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
from pydantic import BaseModel

def linddun_pro_gen_markdown(threats):
    """
    This function generates a markdown table from the threat model data.

    Args:
        threats (list): The list of threats in the threat model. Each threat is a dictionary with the following
            keys:
            - category: string. The category of the threat.
            - source: string. The source of the threat.
            - data_flow: string. The data flow of the threat.
            - destination: string. The destination of the threat.
            - source_id: string. The source of the threat.
            - data_flow_id: string. The data flow of the threat.
            - destination_id: string. The destination of the threat.
    """
    markdown_output = "| Category| Threat at source | Threat at data flow | Threat at destination |\n"
    markdown_output += "|------|-------------|--------------------|------------------|\n"

    for threat in threats:
        color = match_number_color(match_category_number(threat["category"]))
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{threat['category']}</p> | {threat['source_id'].strip()} <br> {threat['source']} | {threat['data_flow_id'].strip()} <br> {threat['data_flow']} | {threat['destination_id'].strip()} <br> {threat['destination']} |\n"
    return markdown_output

def mapping_table(edge, category):
    """
    This function implements the mapping table found at https://linddun.org/instructions-for-pro/#mappingtable.
    
    Args:
        edge (dict): The edge of the DFD to find threats for. The dictionary has the following keys:
            - from: string. The entity where the data flow starts
            - typefrom: string. The type of the entity where the data flow starts
            - to: string. The entity where the data flow ends
            - typeto: string. The type of the entity where the data flow ends
            - trusted: bool. Whether the data flow is trusted
        category (str): The LINDDUN category to look for in the threat model, in the format "Linking", "Identifying", etc.
    
    Returns:
        tuple: A tuple with three booleans representing whether the source, data flow, and destination of the threat have to be considered or not.
    """
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
    # If the edge is not found in the table, there is an error with the category. Return True for all three booleans as a fallback.
    return (True, True, True)


def get_linddun_pro(api_key, model, dfd, edge, category, description, temperature):
    """
    This function generates a LINDDUN Pro threat model from the information provided.
    
    Args:
        - api_key (str): The OpenAI API key.
        - model (str): The OpenAI model to use.
        - dfd (list): The Data Flow Diagram of the application. Each element is a dictionary with the following keys:
            - from: string. The entity where the data flow starts
            - typefrom: string. The type of the entity where the data flow starts
            - to: string. The entity where the data flow ends
            - typeto: string. The type of the entity where the data flow ends
            - trusted: bool. Whether the data flow is trusted
        - edge (dict): The specific edge of the DFD to find threats for. The dictionary has the same keys as the DFD.
        - category (str): The LINDDUN category to look for in the threat model, in the format "Linking", "Identifying", etc.
        - description (str): A brief description of the data flow.
        - temperature (float): The temperature to use for the model.
    
    Returns:
        - dict: The threat model for the specific edge and category. The dictionary has the following
            keys:
            - source_id: string. The ID of the source of the threat.
            - source_title: string. The title of the threat at the source.
            - source: string. The description of the threat at the source.
            - data_flow_id: string. The ID of the data flow of the threat.
            - data_flow_title: string. The title of the threat at the data flow.
            - data_flow: string. The description of the threat at the data flow.
            - destination_id: string. The ID of the destination of the threat.
            - destination_title: string. The title of the threat at the destination.
            - destination: string. The description of the threat at the destination.
            - category: string. The category of the threat, in the format "Linking", "Identifying", etc.
    """
    client = OpenAI(api_key=api_key)

    source, data_flow, destination = mapping_table(edge, category)
    
    tree = threat_tree(category)
    
    messages=[
        {
            "role": "system",
            "content": LINDDUN_PRO_SYSTEM_PROMPT,
        },
        {
            "role": "user", 
            "content": LINDDUN_PRO_USER_PROMPT(dfd, edge, category, description, source, data_flow, destination, tree),
        },
    ]
    
    if model in ["gpt-4o", "gpt-4o-mini"]:
        class Threat(BaseModel):
            source_id: str
            source_title: str
            source: str
            data_flow_id: str
            data_flow_title: str
            data_flow: str
            destination_id: str
            destination_title: str
            destination: str
        response = client.beta.chat.completions.parse(
            model=model,
            response_format=Threat,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    else:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
            messages=messages,
        )
    threat = json.loads(response.choices[0].message.content)
    threat["category"] = category
    return threat


def threat_tree(category):
    """
    This function returns the LINDDUN threat tree for the given category, to be used in the LINDDUN Pro threat model.
    
    Args:
        category (str): The category of the threat, such as "Linking".
    
    Returns:
        dict: The LINDDUN threat tree for the given category. The dictionary has the following keys:
            - name: string. The name of the threat category.
            - id: string. The ID of the threat category.
            - description: string. The description of the threat category.
            - children: list. The list of children of the threat category. Each child is a dictionary with the same keys as the parent.
    """
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
    """
    This function recursively builds the LINDDUN threat tree, given the full
    tree. It is needed because not all the information is needed in the final
    tree.
    
    Args:
        tree (dict): The tree to build.
        full_tree (dict): The full tree to build the tree from.
    
    Returns:
        dict: The built tree.
    """
    tree["name"] = full_tree["name"]
    tree["id"] = full_tree["id"]
    # If the full description is empty, use the description instead
    if full_tree["fullDescription"]:
        tree["description"] = full_tree["fullDescription"]
    else:
        tree["description"] = full_tree["description"]
    tree["children"] = []
    for child in full_tree["children"]:
        tree["children"].append(build_tree({}, child))
    
    return tree
