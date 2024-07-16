import json
import requests
import google.generativeai as genai
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from openai import OpenAI
from openai import AzureOpenAI
from misc.utils import (
		match_color,
)
from llms.prompts import (
	THREAT_MODEL_SYSTEM_PROMPT,
)

# Function to convert JSON to Markdown for display.
def threat_model_gen_markdown(threat_model):
		markdown_output = "## Privacy Threat Model\n\n"

		# Start the markdown table with headers
		markdown_output += "| Threat Type | Scenario | Potential Impact |\n"
		markdown_output += "|-------------|----------|------------------|\n"

		# Fill the table rows with the threat model data
		for threat in threat_model:
				color = match_color(threat["threat_type"])
				color_html = f"<p style='background-color:{color};color:#ffffff;'>"
				markdown_output += f"| {color_html}{threat['threat_type']}</p> | {threat['Scenario']} | {threat['Potential Impact']} |\n"

		return markdown_output


# Function to create a prompt for generating a threat model
def create_threat_model_prompt(
		inputs
):
		prompt = f"""
'''
APPLICATION TYPE: {inputs["app_type"]}
AUTHENTICATION METHODS: {inputs["authentication"]}
APPLICATION DESCRIPTION: {inputs["app_description"]}
DATABASE SCHEMA: {inputs["database"]}
DATA POLICY: {inputs["data_policy"]}
'''
"""
		return prompt


def create_image_analysis_prompt():
		prompt = """
		You are a Senior Solution Architect tasked with explaining the following architecture diagram to 
		a Security Architect to support the threat modelling of the system.

		In order to complete this task you must:

			1. Analyse the diagram
			2. Explain the system architecture to the Security Architect. Your explanation should cover the key 
				 components, their interactions, and any technologies used.
		
		Provide a direct explanation of the diagram in a clear, structured format, suitable for a professional 
		discussion.
		
		IMPORTANT INSTRUCTIONS:
		 - Do not include any words before or after the explanation itself. For example, do not start your
		explanation with "The image shows..." or "The diagram shows..." just start explaining the key components
		and other relevant details.
		 - Do not infer or speculate about information that is not visible in the diagram. Only provide information that can be
		directly determined from the diagram itself.
		"""
		return prompt


# Function to get analyse uploaded architecture diagrams.
def get_image_analysis(api_key, model_name, prompt, base64_image):
		headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

		messages = [
				{
						"role": "user",
						"content": [
								{"type": "text", "text": prompt},
								{
										"type": "image_url",
										"image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
								},
						],
				}
		]

		payload = {"model": model_name, "messages": messages, "max_tokens": 4000}

		response = requests.post(
				"https://api.openai.com/v1/chat/completions", headers=headers, json=payload
		)

		# Log the response for debugging
		try:
				response.raise_for_status()  # Raise an HTTPError for bad responses
				response_content = response.json()
				return response_content
		except requests.exceptions.HTTPError as http_err:
				print(f"HTTP error occurred: {http_err}")  # HTTP error
		except Exception as err:
				print(f"Other error occurred: {err}")  # Other errors

		print(
				f"Response content: {response.content}"
		)  # Log the response content for further inspection
		return None


# Function to get threat model from the GPT response.
def get_threat_model_openai(api_key, model_name, prompt, temperature):
		client = OpenAI(api_key=api_key)

		response = client.chat.completions.create(
				model=model_name,
				response_format={"type": "json_object"},
				temperature=temperature,
				messages=[
						{
								"role": "system",
								"content": THREAT_MODEL_SYSTEM_PROMPT,
						},
						{"role": "user", "content": prompt},
				],
				max_tokens=4096,
		)

		# Convert the JSON string in the 'content' field to a Python dictionary
		response_content = json.loads(response.choices[0].message.content)

		return response_content


# Function to get threat model from the Azure OpenAI response.
def get_threat_model_azure(
		azure_api_endpoint, azure_api_key, azure_api_version, azure_deployment_name, prompt
):
		client = AzureOpenAI(
				azure_endpoint=azure_api_endpoint,
				api_key=azure_api_key,
				api_version=azure_api_version,
		)

		response = client.chat.completions.create(
				model=azure_deployment_name,
				response_format={"type": "json_object"},
				messages=[
						{
								"role": "system",
								"content": "You are a helpful assistant designed to output JSON.",
						},
						{"role": "user", "content": prompt},
				],
		)

		# Convert the JSON string in the 'content' field to a Python dictionary
		response_content = json.loads(response.choices[0].message.content)

		return response_content


# Function to get threat model from the Google response.
def get_threat_model_google(google_api_key, google_model, prompt, temperature):
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


# Function to get threat model from the Mistral response.
def get_threat_model_mistral(mistral_api_key, mistral_model, prompt, temperature):
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
