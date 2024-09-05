# Copyright 2024 [name of copyright owner]
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
import google.generativeai as genai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
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
		color = match_color(threat["threat_type"])
		color_html = f"<p style='background-color:{color};color:#ffffff;'>"
		markdown_output += f"| {color_html}{threat['threat_type']}</p> | {threat['Scenario']} | {threat['Reason']} |\n"

	return markdown_output

def get_threat_model_openai(api_key, model_name, prompt, temperature):
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

def get_threat_model_google(google_api_key, google_model, prompt, temperature):
	"""
	This function generates a threat model from the prompt using the Google AI model.

	Args:
		google_api_key (str): The Google API key.
		google_model (str): The Google model to use.
		prompt (str): The prompt to use for generating the threat model.
		temperature (float): The temperature to use for the model.
	
	Returns:
		threat_model: The list of threats in the threat model. Each threat is a dictionary with the following keys
			- title: string. The title of the threat.
			- threat_type: string. The type of the threat, in the format "L - Linking".
			- Scenario: string. The scenario where the threat occurs.
			- Reason: string. The reason for the threat.
	"""

	genai.configure(api_key=google_api_key)
	model = genai.GenerativeModel(
			google_model, generation_config={"response_mime_type": "application/json"}
	)
	response = model.generate_content(
		prompt, 
		generation_config=genai.types.GenerationConfig(
			temperature=temperature,
			response_mime_type="application/json",
			max_output_tokens=4096,
		)
	)
	try:
			# Access the JSON content from the 'parts' attribute of the 'content' object
			response_content = json.loads(response.candidates[0].content.parts[0].text)
	except json.JSONDecodeError as e:
			print(f"Error decoding JSON: {str(e)}")
			print("Raw JSON string:")
			print(response.candidates[0].content.parts[0].text)
			return None

	return response_content


def get_threat_model_mistral(mistral_api_key, mistral_model, prompt, temperature):
	"""
	This function generates a threat model from the prompt using the Mistral AI model.

	Args:
		mistral_api_key (str): The Mistral API key.
		mistral_model (str): The Mistral model to use.
		prompt (str): The prompt to use for generating the threat model.
		temperature (float): The temperature to use for the model.
	
	Returns:
		threat_model: The list of threats in the threat model. Each threat is a dictionary with the following keys
			- title: string. The title of the threat.
			- threat_type: string. The type of the threat, in the format "L - Linking".
			- Scenario: string. The scenario where the threat occurs.
			- Reason: string. The reason for the threat.
	"""
	client = MistralClient(api_key=mistral_api_key)

	response = client.chat(
		model=mistral_model,
		response_format={"type": "json_object"},
		messages=[
			ChatMessage(role="system", content=THREAT_MODEL_SYSTEM_PROMPT),
			ChatMessage(role="user", content=prompt),
		],
		max_tokens=4096,
		temperature=temperature,
	)

	# Convert the JSON string in the 'content' field to a Python dictionary
	response_content = json.loads(response.choices[0].message.content)

	return response_content
