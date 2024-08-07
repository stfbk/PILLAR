import json
import requests
from openai import OpenAI
from llms.prompts import (
    THREAT_MODEL_USER_PROMPT,
    DFD_SYSTEM_PROMPT,
    DFD_IMAGE_SYSTEM_PROMPT,
)

def get_dfd(api_key, model, temperature, inputs):
    """
    This function generates a DFD from the application inputs.

    Args:
        api_key (str): The OpenAI API key.
        model (str): The OpenAI model to use.
        temperature (float): The temperature to use for the model.
        inputs (dict): The dictionary of inputs to the application, with the same keys as the "input" session state in the Application Info tab.
    
    Returns:
        list: The list of edges in the DFD. Each edge is a dictionary with the following keys:
            - from: string. The entity where the data flow starts
            - typefrom: string. The type of the entity where the data flow starts
            - to: string. The entity where the data flow ends
            - typeto: string. The type of the entity where the data flow ends
            - trusted: bool. Whether the data flow is trusted
    """
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": DFD_SYSTEM_PROMPT,
            },
            {
                "role": "user", 
                "content": THREAT_MODEL_USER_PROMPT(
                    inputs
                )
            },
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)
    

def get_image_analysis(api_key, model_name, base64_image):
	"""
	This function generates a DFD from the image provided.
    
	Args:
        api_key (str): The OpenAI API key.
        model_name (str): The OpenAI model to use.
        base64_image (str): The base64 encoded image to analyze.
    
    Returns:
        list: The list of edges in the DFD. Each edge is a dictionary with the following keys:
            - from: string. The entity where the data flow starts
            - typefrom: string. The type of the entity where the data flow starts
            - to: string. The entity where the data flow ends
            - typeto: string. The type of the entity where the data flow ends
            - trusted: bool. Whether the data flow is trusted
	"""
	headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

	messages = [
		{
			"role": "user",
			"content": [
				{"type": "text", "text": DFD_IMAGE_SYSTEM_PROMPT},
				{
					"type": "image_url",
					"image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
				},
			],
		}
	]

	payload = {"model": model_name, "messages": messages, "response_format": {"type": "json_object" }, "max_tokens": 4096}

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