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
from llms.config import OLLAMA_CONFIG, LMSTUDIO_CONFIG
import google.generativeai as genai
from mistralai import Mistral, UserMessage
from openai import OpenAI
from misc.utils import (
		match_color,
)
from llms.prompts import (
	THREAT_MODEL_SYSTEM_PROMPT,
)
	
from pydantic import BaseModel

def threat_model_gen_markdown(threat_model):
	"""
	This function generates a markdown table from the threat model data.

	Args:
		threat_model (list): The list of threats in the threat model. Each threat is a dictionary with the following
			keys:
			- threat_type: string. The type of the threat, in the format "L - Linking".
			- Scenario: string. The scenario where the threat occurs.
			- Reason: string. The reason for the threat.
	
	Returns:
		str: The markdown table with the threat model data.
	"""
	markdown_output = "| Threat Type | Scenario | Reason |\n"
	markdown_output += "|-------------|----------|--------|\n"

	# Fill the table rows with the threat model data
	for threat in threat_model:
		# Ensure we only use the expected fields and clean any extra content
		threat_type = str(threat.get("threat_type", "Unknown")).strip()
		scenario = str(threat.get("Scenario", "No scenario")).strip()
		reason = str(threat.get("Reason", "No reason provided")).strip()
		
		# Remove any potential markdown or extra formatting from the text fields
		threat_type = threat_type.replace('\n', ' ').replace('|', '').strip()
		scenario = scenario.replace('\n', ' ').replace('|', '').strip()
		reason = reason.replace('\n', ' ').replace('|', '').strip()
		
		color = match_color(threat_type)
		color_html = f"<p style='background-color:{color};color:#ffffff;'>"
		markdown_output += f"| {color_html}{threat_type}</p> | {scenario} | {reason} |\n"

	return markdown_output

def get_threat_model_openai(api_key, model_name, prompt, temperature, lmstudio=False, ollama=False):
	"""
	This function generates a simple LINDDUN threat model from the prompt.
	
	Args:
		api_key (str): The OpenAI API key.
		model_name (str): The OpenAI model to use.
		prompt (str): The prompt to use for generating the threat model.
		temperature (float): The temperature to use for the model.
	
	Returns:
		threat_model: The list of threats in the threat model. Each threat is a dictionary with the following keys:
			- title: string. The title of the threat.
			- threat_type: string. The type of the threat, in the format "L - Linking".
			- Scenario: string. The scenario where the threat occurs.
			- Reason: string. The reason for the threat.
	"""

	if lmstudio:
		client = OpenAI(
            base_url=LMSTUDIO_CONFIG["base_url"],
            api_key=LMSTUDIO_CONFIG["api_key"],
        )
	elif ollama:
		client = OpenAI(
            base_url=OLLAMA_CONFIG["base_url"],
            api_key=OLLAMA_CONFIG["api_key"]
        )
	else:
		client = OpenAI(api_key=api_key)
	messages=[
			{
			"role": "system",
			"content": THREAT_MODEL_SYSTEM_PROMPT,
			},
			{"role": "user", "content": prompt},
	]

	if model_name in ["gpt-4o", "gpt-4o-mini"]:
		class Threat(BaseModel):
			title: str
			threat_type: str
			Scenario: str
			Reason: str
		class ThreatModel(BaseModel):
			threat_model: list[Threat]

		response = client.beta.chat.completions.parse(
			messages=messages,
			model=model_name,
			response_format=ThreatModel,
			temperature=temperature,
			max_tokens=4096,
		)
	else:
		response = client.chat.completions.create(
			model=model_name,
			messages=messages,
			max_tokens=4096,
			temperature=temperature,
			response_format={"type": "json_object"},
		)
		
	response_content = json.loads(response.choices[0].message.content)

	return response_content

def get_threat_model_mistral(mistral_api_key, mistral_model, prompt, temperature):
    """
    Get a threat model using Mistral AI
    """
    client = Mistral(api_key=mistral_api_key)
    
    # Combine system and user prompts into a single prompt for Mistral
    combined_prompt = f"{THREAT_MODEL_SYSTEM_PROMPT}\n\nUser request: {prompt}"

    response = client.chat.complete(
        model=mistral_model,
        response_format={"type": "json_object"},
        messages=[
            UserMessage(content=combined_prompt)
        ],
        temperature=temperature
    )

    # Convert the JSON string in the 'content' field to a Python dictionary
    response_text = response.choices[0].message.content
    
    # Extract only the JSON part from the response
    try:
        # Try to find JSON object boundaries
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
            response_content = json.loads(json_text)
        else:
            # If no JSON boundaries found, try parsing the whole response
            response_content = json.loads(response_text)
    except json.JSONDecodeError:
        # If JSON parsing fails, return a default empty threat model
        response_content = {"threat_model": []}

    return response_content


def get_threat_model_google(google_api_key: str, model: str, app_input: str, temp: float = 0.7):
    """
    This function generates a threat model from the prompt using the Google AI model.
    """
    try:
        genai.configure(api_key=google_api_key)
        google_model = genai.GenerativeModel(
            model, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Combine system and user prompts into a single prompt for Google AI
        combined_prompt = f"{THREAT_MODEL_SYSTEM_PROMPT}\n\nUser request: {app_input}"
        
        response = google_model.generate_content(
            combined_prompt,  
            generation_config=genai.types.GenerationConfig(
                temperature=temp,
                response_mime_type="application/json",
                max_output_tokens=4096,
            )
        )

        # Handle the response
        if response.candidates and len(response.candidates) > 0:
            try:
                json_text = response.candidates[0].content.parts[0].text
                response_content = json.loads(json_text)
                
                # Ensure we have the expected structure
                if isinstance(response_content, dict) and "threat_model" in response_content:
                    return response_content
                elif isinstance(response_content, list):
                    # If we got a list directly, wrap it in the expected structure
                    return {"threat_model": response_content}
                else:
                    # If response doesn't have the threat_model key, wrap it
                    return {"threat_model": [response_content]}
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Google AI response: {str(e)}")
                print("Raw response:", json_text)
                raise Exception("Invalid JSON response from Google AI")
        else:
            raise Exception("No response generated from Google AI")
            
    except Exception as e:
        print(f"Error in Google AI threat model generation: {str(e)}")
        raise e


