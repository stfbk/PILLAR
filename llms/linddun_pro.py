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
import streamlit as st
import json
import requests
from openai import OpenAI
from llms.config import OLLAMA_CONFIG, LMSTUDIO_CONFIG
from misc.utils import (
    match_category_number,
    match_number_color,
)
from llms.prompts import (
    LINDDUN_PRO_SYSTEM_PROMPT,
    LINDDUN_PRO_USER_PROMPT,
)
from pydantic import BaseModel
from mistralai import Mistral, UserMessage
import google.generativeai as genai
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
    def safe_get_string(threat_dict, key, default=''):
        """Helper function to safely get string values from threat dictionary"""
        value = threat_dict.get(key, default)
        
        # If it's a list, join the elements or take the first element
        if isinstance(value, list):
            if value:  # If list is not empty
                if all(isinstance(item, str) for item in value):
                    return ' '.join(value)  # Join if all items are strings
                else:
                    return str(value[0])  # Convert first element to string
            else:
                return default  # Return default if list is empty
        
        # If it's not a string, convert it
        if not isinstance(value, str):
            return str(value) if value is not None else default
            
        return value
    
    markdown_output = "| Category| Threat at source | Threat at data flow | Threat at destination |\n"
    markdown_output += "|------|-------------|--------------------|------------------|\n"

    for threat in threats:
        # Use safe_get_string to handle potential lists or non-string values
        source_id = safe_get_string(threat, 'source_id').strip()
        source = safe_get_string(threat, 'source')
        data_flow_id = safe_get_string(threat, 'data_flow_id').strip()
        data_flow = safe_get_string(threat, 'data_flow')
        destination_id = safe_get_string(threat, 'destination_id').strip()
        destination = safe_get_string(threat, 'destination')
        category = safe_get_string(threat, 'category')
        
        # Check if any field has meaningful content
        if not any([source_id, source, data_flow_id, data_flow, destination_id, destination]):
            continue  # skip empty threats
            
        color = match_number_color(match_category_number(category))
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += (
            f"| {color_html}{category}</p> | "
            f"{source_id} <br> {source} | "
            f"{data_flow_id} <br> {data_flow} | "
            f"{destination_id} <br> {destination} |\n"
        )
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


def get_linddun_pro(api_key, model, dfd, edge, category, boundaries, temperature, model_provider="OpenAI"):
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
            - boundary: string. The trust boundary id of the data flow
            - description: string. The description of the data flow
        - edge (dict): The specific edge of the DFD to find threats for. The dictionary has the same keys as the DFD.
        - category (str): The LINDDUN category to look for in the threat model, in the format "Linking", "Identifying", etc.
        - boundaries (dict): The trust boundaries of the application. The dictionary has the following keys:
            - id: string. The ID of the trust boundary.
            - title: string. The title of the trust boundary.
            - description: string. The description of the trust boundary.
            - color: string. The color of the trust boundary.
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
    if model_provider == "Ollama":
        client = OpenAI(
            base_url=OLLAMA_CONFIG["base_url"],
            api_key=OLLAMA_CONFIG["api_key"]
        )
    elif model_provider == "Local LM Studio":
        client = OpenAI(
            base_url=LMSTUDIO_CONFIG["base_url"],
            api_key=LMSTUDIO_CONFIG["api_key"],
        )
    else:  # Default: OpenAI
        client = OpenAI(api_key=api_key)

    source, data_flow, destination = mapping_table(edge, category)
    tree = threat_tree(category)
    messages = [
        {
            "role": "system",
            "content": LINDDUN_PRO_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": LINDDUN_PRO_USER_PROMPT(dfd, edge, category, source, data_flow, destination, boundaries, tree),
        },
    ]

    # Use structured parsing ONLY for OpenAI gpt-4o models
    if model_provider == "OpenAI" and model in ["gpt-4o", "gpt-4o-mini"]:
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
        threat = response.choices[0].message.parsed.dict()
    elif model_provider == "Ollama":
        # For Ollama, use JSON object response format
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
            messages=messages,
        )
        raw_content = response.choices[0].message.content
        print(f"Raw {model_provider} response:", raw_content)

        try:
            threat = json.loads(raw_content)
        except Exception as e:
            print("JSON decode error:", e)
            threat = {
                "source_id": "",
                "source_title": "",
                "source": "",
                "data_flow_id": "",
                "data_flow_title": "",
                "data_flow": "",
                "destination_id": "",
                "destination_title": "",
                "destination": ""
            }
    else:
        # For LM Studio and other non-OpenAI models, don't use response_format
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            temperature=temperature,
            messages=messages,
        )
        raw_content = response.choices[0].message.content
        print(f"Raw {model_provider} response:", raw_content)

        try:
            # Try to extract JSON from the response
            start_idx = raw_content.find('{')
            end_idx = raw_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = raw_content[start_idx:end_idx]
                threat = json.loads(json_text)
            else:
                threat = json.loads(raw_content)
        except Exception as e:
            print("JSON decode error:", e)
            threat = {
                "source_id": "",
                "source_title": "",
                "source": "",
                "data_flow_id": "",
                "data_flow_title": "",
                "data_flow": "",
                "destination_id": "",
                "destination_title": "",
                "destination": ""
            }

    # Add category to the threat
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

def get_linddun_pro_mistral(api_key, model, dfd, edge, category, boundaries, temperature):
    """
    This function generates a LINDDUN Pro threat model using Mistral AI.
    
    Args:
        - api_key (str): The Mistral API key.
        - model (str): The Mistral model to use.
        - dfd (list): The Data Flow Diagram of the application.
        - edge (dict): The specific edge of the DFD to find threats for.
        - category (str): The LINDDUN category to look for in the threat model.
        - boundaries (dict): The trust boundaries of the application.
        - temperature (float): The temperature to use for the model.
    
    Returns:
        - dict: The threat model for the specific edge and category.
    """

    client = Mistral(api_key=api_key)
    source, data_flow, destination = mapping_table(edge, category)
    tree = threat_tree(category)
    
    # Combine system and user prompts for Mistral
    combined_prompt = f"{LINDDUN_PRO_SYSTEM_PROMPT}\n\n{LINDDUN_PRO_USER_PROMPT(dfd, edge, category, source, data_flow, destination, boundaries, tree)}"
    
    response = client.chat.complete(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            UserMessage(content=combined_prompt)
        ],
        temperature=temperature
    )
    
    # Extract JSON from response with robust parsing
    response_text = response.choices[0].message.content
    
    try:
        # Try to find JSON object boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
            threat = json.loads(json_text)
        else:
            threat = json.loads(response_text)
            
    except json.JSONDecodeError:
        # If JSON parsing fails, return empty threat
        print(f"JSON decode error for Mistral response: {response_text}")
        threat = {
            "source_id": "",
            "source_title": "",
            "source": "",
            "data_flow_id": "",
            "data_flow_title": "",
            "data_flow": "",
            "destination_id": "",
            "destination_title": "",
            "destination": ""
        }
    
    # Add category to the threat
    threat["category"] = category
    
    return threat

def get_linddun_pro_google(api_key, model, dfd, edge, category, boundaries, temperature):
    """
    This function generates a LINDDUN Pro threat model using Google AI.
    
    Args:
        - api_key (str): The Google AI API key.
        - model (str): The Google AI model to use.
        - dfd (list): The Data Flow Diagram of the application.
        - edge (dict): The specific edge of the DFD to find threats for.
        - category (str): The LINDDUN category to look for in the threat model.
        - boundaries (dict): The trust boundaries of the application.
        - temperature (float): The temperature to use for the model.
    
    Returns:
        - dict: The threat model for the specific edge and category.
    """
    try:
        genai.configure(api_key=api_key)
        google_model = genai.GenerativeModel(
            model, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        source, data_flow, destination = mapping_table(edge, category)
        tree = threat_tree(category)
        
        # Combine system and user prompts for Google AI
        combined_prompt = f"{LINDDUN_PRO_SYSTEM_PROMPT}\n\n{LINDDUN_PRO_USER_PROMPT(dfd, edge, category, source, data_flow, destination, boundaries, tree)}"
        
        response = google_model.generate_content(
            combined_prompt,  
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                response_mime_type="application/json",
                max_output_tokens=4096,
            )
        )

        # Handle the response
        if response.candidates and len(response.candidates) > 0:
            json_text = response.candidates[0].content.parts[0].text
            
            # Extract JSON from response with robust parsing
            try:
                # Try to find JSON object boundaries
                start_idx = json_text.find('{')
                end_idx = json_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_content = json_text[start_idx:end_idx]
                    threat = json.loads(json_content)
                else:
                    threat = json.loads(json_text)
                    
            except json.JSONDecodeError:
                # If JSON parsing fails, return empty threat
                print(f"JSON decode error for Google AI response: {json_text}")
                threat = {
                    "source_id": "",
                    "source_title": "",
                    "source": "",
                    "data_flow_id": "",
                    "data_flow_title": "",
                    "data_flow": "",
                    "destination_id": "",
                    "destination_title": "",
                    "destination": ""
                }
        else:
            raise Exception("No response generated from Google AI")
            
    except Exception as e:
        print(f"Error in Google AI LINDDUN PRO generation: {str(e)}")
        # Return empty threat on error
        threat = {
            "source_id": "",
            "source_title": "",
            "source": "",
            "data_flow_id": "",
            "data_flow_title": "",
            "data_flow": "",
            "destination_id": "",
            "destination_title": "",
            "destination": ""
        }
    
    # Add category to the threat
    threat["category"] = category
    
    return threat