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
from pydantic import BaseModel
from llms.prompts import CHOOSE_CONTROL_MEASURES_PROMPT, EXPLAIN_CONTROL_MEASURES_PROMPT, IMPACT_ASSESSMENT_PROMPT, THREAT_MODEL_USER_PROMPT
from misc.utils import (
    match_number_color,
    match_category_number,
)
from openai import OpenAI
import google.generativeai as genai
from mistralai import Mistral, UserMessage
import requests
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
    markdown_output += f"| {color_html}{threat['category']}</p> | {threat['description']} |\n"
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
    if measures is None or not isinstance(measures, (list, tuple)):
        measures = []

    markdown_output = "| Title | Explanation | Implementation |\n|--------|-------|-----|\n"
    for measure in measures:
        if measure is None or not isinstance(measure, dict):
            continue
        title = measure.get("title", "No Title")
        filename = measure.get("filename", "")
        explanation = measure.get("explanation", "")
        implementation = measure.get("implementation", "")
        markdown_output += f"| [{title}](https://privacypatterns.org/patterns/{filename}) | {explanation} | {implementation} |\n"
    return markdown_output

    

def get_assessment(api_key, model, threat, inputs, temperature, provider):
    """
    This function generates an assessment for a threat.
    
    Args:
        api_key (str): The API key for the selected provider.
        model (str): The model to use.
        threat (dict): The threat to assess. Any dictionary is accepted, since it will be converted to a string and passed to the model.
        inputs (dict): The dictionary of inputs to the application, with the same keys as the "input" session state in the Application Info tab.
        temperature (float): The temperature to use for the model.
        provider (str): The provider to use. One of "OpenAI API", "Google AI API", "Mistral API", "Ollama", or "Local LM Studio".

    Returns:
        dict: The assessment data. The dictionary has the following keys:
            - impact: string. The impact of the threat.
    """
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
    
    if provider == "OpenAI API":
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
        return json.loads(response.choices[0].message.content)
    
    elif provider == "Google AI API":
     
        
        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        
        response = model_obj.generate_content(
            [
                {"role": "system", "parts": [messages[0]["content"]]},
                {"role": "user", "parts": [messages[1]["content"]]},
            ],
            generation_config={"temperature": temperature}
        )
        
        content = response.text
        
        # Clean up the content if it contains markdown JSON formatting
        if "```json" in content:
            content = content.split("```json")[1]
            if "```" in content:
                content = content.split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        content = content.strip()
        
        try:
            result = json.loads(content)
            if "impact" in result:
                return {"impact": result["impact"]}
            else:
                return {"impact": content}
        except Exception as e:
            if "impact" in content.lower() and ":" in content:
                try:
                    impact_text = content.lower().split("impact")[1].split("\n")[0]
                    impact_text = impact_text.replace(":", "").replace('"', "").replace(",", "").strip()
                    return {"impact": f"Extracted from response: {impact_text}"}
                except:
                    pass
            
            return {"impact": response.text}
    
    elif provider == "Mistral API": 
        client = Mistral(api_key=api_key)
        
        combined_prompt = f"{messages[0]['content']}\n\nUser request: {messages[1]['content']}"
        
        response = client.chat.complete(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                UserMessage(content=combined_prompt)
            ],
            max_tokens=4096,
            temperature=temperature,
        )
        
        content = response.choices[0].message.content
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = content[start_idx:end_idx]
                result = json.loads(json_text)
            else:
                result = json.loads(content)
            
            if "impact" in result:
                return {"impact": result["impact"]}
            else:
                return {"impact": content}
        except json.JSONDecodeError as e:
            if "impact" in content.lower() and ":" in content:
                try:
                    impact_text = content.lower().split("impact")[1].split("\n")[0]
                    impact_text = impact_text.replace(":", "").replace('"', "").replace(",", "").strip()
                    return {"impact": f"Extracted from response: {impact_text}"}
                except:
                    pass
            
            return {"impact": content}
    
    elif provider == "Ollama":   
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": messages[0]["content"]},
                    {"role": "user", "content": messages[1]["content"]},
                ],
                "stream": False,
                "options": {"temperature": temperature}
            }
        )
        
        if response.status_code == 200:
            content = response.json()["message"]["content"]
            
            if "```json" in content:
                content = content.split("```json")[1]
                if "```" in content:
                    content = content.split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            content = content.strip()
            
            try:
                result = json.loads(content)
                if "impact" in result:
                    return {"impact": result["impact"]}
                else:
                    return {"impact": content}
            except Exception as e:
                if "impact" in content.lower() and ":" in content:
                    try:
                        impact_text = content.lower().split("impact")[1].split("\n")[0]
                        impact_text = impact_text.replace(":", "").replace('"', "").replace(",", "").strip()
                        return {"impact": f"Extracted from response: {impact_text}"}
                    except:
                        pass
                
                return {"impact": response.json()["message"]["content"]}
        else:
            raise Exception(f"Error from Ollama: {response.text}")
    
    elif provider == "Local LM Studio":
        
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096,
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            
            if "```json" in content:
                content = content.split("```json")[1]
                if "```" in content:
                    content = content.split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            content = content.strip()
            
            try:
                result = json.loads(content)
                if "impact" in result:
                    return {"impact": result["impact"]}
                else:
                    return {"impact": content}
            except Exception as e:
                if "impact" in content.lower() and ":" in content:
                    try:
                        impact_text = content.lower().split("impact")[1].split("\n")[0]
                        impact_text = impact_text.replace(":", "").replace('"', "").replace(",", "").strip()
                        return {"impact": f"Extracted from response: {impact_text}"}
                    except:
                        pass
                
                return {"impact": response.json()["choices"][0]["message"]["content"]}
        else:
            raise Exception(f"Error from LM Studio: {response.text}")
    
    else:
        raise ValueError(f"Unknown provider: {provider}")


def choose_control_measures(api_key, model, threat, inputs, temperature, provider="OpenAI API"):
    """
    This function generates a list of control measures which could be useful for a threat, out of the full list of [privacy patterns](https://privacypatterns.org/).
    
    Note: This function only supports OpenAI API provider for reliable JSON parsing and response formatting.

    Args:
        api_key (str): The API key for OpenAI.
        model (str): The OpenAI model to use.
        threat (dict): The threat to assess.
        inputs (dict): The dictionary of inputs to the application.
        temperature (float): The temperature to use for the model.
        provider (str): The provider to use. Only "OpenAI API" is supported.

    Returns:
        list: The list of control measures.
    """
    if provider != "OpenAI API":
        raise ValueError("Control measures selection is only supported with OpenAI API provider.")
        
    with open("misc/privacypatterns.json", "r") as f:
        patterns = json.load(f)
        patterns = [{"title": p["title"], "excerpt": p["excerpt"], "related_patterns": p["sections"]["Related Patterns"] if "Related Patterns" in p["sections"] else None} for p in patterns["patterns"]]

    messages = [
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

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)["measures"]

def get_control_measures(api_key, model, threat, inputs, temperature, provider="OpenAI API"):
    """
    This function generates a list of control measures which could be useful for a threat and explains why they are useful and how to implement them.
    
    Note: This function only supports OpenAI API provider for reliable JSON parsing and response formatting.

    Args:
        api_key (str): The API key for OpenAI.
        model (str): The OpenAI model to use.
        threat (dict): The threat to assess.
        inputs (dict): The dictionary of inputs to the application.
        temperature (float): The temperature to use for the model.
        provider (str): The provider to use. Only "OpenAI API" is supported.

    Returns:
        list: The list of control measures.
    """
    if provider != "OpenAI API":
        raise ValueError("Control measures generation is only supported with OpenAI API provider.")
    
    measures = choose_control_measures(api_key, model, threat, inputs, temperature, provider)
    
    if not isinstance(measures, list):
        measures = [measures] if measures is not None else []
    
    chosen = []
    with open("misc/privacypatterns.json", "r") as f:
        patterns = json.load(f)["patterns"]

    for pattern in patterns:
        if pattern["title"] in measures:
            chosen.append(pattern)

    messages = [
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
PATTERNS: {json.dumps(chosen)}
'''
""",
        },
    ]

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)["measures"]
