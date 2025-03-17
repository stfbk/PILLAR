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
import google.generativeai as genai
import random
from openai import OpenAI
from mistralai import Mistral
from misc.utils import (
    match_number_color,
    match_letter,
)
from llms.prompts import (
    LINDDUN_GO_SYSTEM_PROMPT,
    LINDDUN_GO_USER_PROMPT,
    LINDDUN_GO_SPECIFIC_PROMPTS,
    LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT,
    LINDDUN_GO_JUDGE_PROMPT,
)
    
from pydantic import BaseModel

def linddun_go_gen_markdown(threats):
    """
    This function generates a markdown table from the threat model data.

    Args:
        threats (list): The list of threats in the threat model. Each threat is a dictionary with the following
            keys:
            - threat_type: int. The type of the threat, as a number from 1 to 7.
            - threat_title: string. The title of the threat.
            - threat_description: string. The description of the threat.
            - reason: string. The reason for the threat.
        
    Returns:
        str: The markdown table with the threat model data.
    """
    # Start the markdown table with headers
    markdown_output = "| Threat Name | Threat description | Detection reason |\n"
    markdown_output += "|-------------|--------------------|------------------|\n"

    # Fill the table rows with the threat model data
    for threat in threats:
        color = match_number_color(threat["threat_type"])
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{match_letter(threat['threat_type'])} - {threat['threat_title']}</p> | {threat['threat_description']} | {threat['reason']} |\n"

    return markdown_output

def get_deck(file="misc/deck.json"):
    """
    This function reads the deck of cards from a JSON file.

    Args:
        file (str): The path to the JSON file containing the deck of cards.
    
    Returns:
        list: The list of cards in the deck. Each card is a dictionary with the following keys:
            - title: string. The title of the card.
            - description: string. The description of the card.
            - questions: list. The list of questions to ask about the card.
            - type: int. The type of the card, as a number from 1 to 7.
            - competent_agents: list. The list of competent agents for the card, as numbers from 0 to 5.
    """
    with open(file, 'r') as deck_file:
        deck = json.load(deck_file)
    return deck["cards"]


def get_linddun_go(api_key, model_name, inputs, threats_to_analyze, temperature):
    """
    This function generates a single-agent LINDDUN threat model from the prompt.

    Args:
        api_key (str): The OpenAI API key.
        model_name (str): The OpenAI model to use.
        inputs (dict): The inputs to the model, a dictionary with the same keys as the one in the Application Info tab.
        threats_to_analyze (int): The number of threats to analyze.
        temperature (float): The temperature to use for the model.
    
    Returns:
        list: The list of threats in the threat model. Each threat is a dictionary with the following keys:
            - question: string. The questions on the card, asked to the LLM to elicit the threat.
            - threat_title: string. The title of the threat.
            - threat_description: string. The description of the threat.
            - threat_type: int. The LINDDUN category of the threat, from 1 to 7.
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    client = OpenAI(api_key=api_key)
    deck = get_deck()
    
    # Shuffle the deck of cards, simulating the experience of drawing cards from the deck
    random.shuffle(deck)

    threats = []

    # For each card, ask the associated questions to the LLM
    for card in deck[0:threats_to_analyze]:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]

        messages=[
            {
                "role": "system",
                "content": LINDDUN_GO_SPECIFIC_PROMPTS[0]+LINDDUN_GO_SYSTEM_PROMPT, # We use the first specific prompt for the system prompt, as it is the single agent simulation
            }, 
            {
                "role": "user", 
                "content": LINDDUN_GO_USER_PROMPT(inputs, question, title, description)
            },
        ]
        
        if model_name in ["gpt-4o", "gpt-4o-mini"]:
            class Threat(BaseModel):
                reply: bool
                reason: str
            response = client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                response_format=Threat,
                temperature=temperature,
                max_tokens=4096,
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=4096,
            )
        response_content = json.loads(response.choices[0].message.content)
        response_content["question"] = question
        response_content["threat_title"] = title
        response_content["threat_description"] = description
        response_content["threat_type"] = type

        threats.append(response_content)

    return threats



def get_multiagent_linddun_go(keys, models, inputs, temperature, rounds, threats_to_analyze, llms_to_use):
    """
    This function generates a multi-agent LINDDUN threat model from the prompt.
    
    Args:
        keys (dict): The dictionary of API keys for the different LLM providers.
        models (dict): The dictionary of models for the different LLM providers.
        inputs (dict): The inputs to the model, the same as the one in the Application Info tab.
        temperature (float): The temperature to use for the model.
        rounds (int): The number of rounds to run the simulation for.
        threats_to_analyze (int): The number of threats to analyze.
        llms_to_use (list): The list of LLM providers to use.
    
    Returns:
        list: The list of threats in the threat model. Each threat is a dictionary with the following keys
            - question: string. The questions on the card, asked to the LLM to elicit the threat.
            - threat_title: string. The title of the threat.
            - threat_description: string. The description of the threat.
            - threat_type: int. The LINDDUN category of the threat, from 1 to 7.
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """

    # Initialize the LLM clients
    openai_client = OpenAI(api_key=keys["openai_api_key"]) if "OpenAI API" in llms_to_use else None
    mistral_client = Mistral(api_key=keys["mistral_api_key"]) if "Mistral API" in llms_to_use else None
    if "Google AI API" in llms_to_use:
        genai.configure(api_key=keys["google_api_key"])
        google_client = genai.GenerativeModel(
                models["google_model"], generation_config={"response_mime_type": "application/json"}
        )
    else:
        google_client = None

    threats = []
    deck = get_deck()
    
    # Shuffle the deck of cards, simulating the experience of drawing cards from the deck
    random.shuffle(deck)


    for card in deck[0:threats_to_analyze]:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]
        previous_analysis = [{} for _ in range(6)]
        
        # Run the simulation for the specified number of rounds
        # In the first round, we ask the questions to all agents.
        # In the following rounds, we only ask the questions to the competent agents, but we keep track of the previous analysis for all agents.
        for round in range(rounds):
            for i in range(6):
                if round == 2 and i not in card["competent_agents"]:
                    previous_analysis[i] = {} # At the third round, we only have to consider the analysis of the competent agents in the second round, not the others, so we reset the previous analysis for the non-competent agents
                if i not in card["competent_agents"] and round != 0:
                    continue
                llm = random.randrange(0, len(llms_to_use))
                system_prompt = LINDDUN_GO_SPECIFIC_PROMPTS[i]+LINDDUN_GO_SYSTEM_PROMPT+(LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis) if previous_analysis[i] else "")  
                user_prompt = LINDDUN_GO_USER_PROMPT(inputs, question, title, description)
                if llms_to_use[llm] == "OpenAI API":
                    response_content = get_response_openai(
                        openai_client, 
                        models["openai_model"], 
                        temperature,
                        system_prompt,
                        user_prompt
                    )
                elif llms_to_use[llm] == "Mistral API":
                    response_content = get_response_mistral(
                        mistral_client,
                        models["mistral_model"],
                        temperature,
                        system_prompt,
                        user_prompt
                    )
                elif llms_to_use[llm] == "Google AI API":
                    response_content = get_response_google(
                        google_client,
                        temperature,
                        system_prompt,
                        user_prompt
                    )
                else:
                    raise Exception("Invalid LLM provider")

                
                previous_analysis[i] = response_content

        # Judge the final verdict based on the previous analysis
        final_verdict = judge(keys, models, previous_analysis, temperature)
        final_verdict["question"] = question
        final_verdict["threat_title"] = title
        final_verdict["threat_description"] = description
        final_verdict["threat_type"] = type

        threats.append(final_verdict)

    return threats

def get_response_openai(client, model, temperature, system_prompt, user_prompt):
    """
    This function generates a response from the OpenAI API.

    Args:
        client (OpenAI): The OpenAI client.
        model (str): The OpenAI model to use.
        temperature (float): The temperature to use for the model.
        system_prompt (str): The system prompt to use.
        user_prompt (str): The user prompt to use.
    
    Returns:
        dict: The response from the OpenAI API, with the following keys:
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user", 
            "content": user_prompt,
        },
    ]
    if model in ["gpt-4o", "gpt-4o-mini"]:
        class Threat(BaseModel):
            reply: bool
            reason: str
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
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
    return json.loads(response.choices[0].message.content)

def get_response_mistral(client, model, temperature, system_prompt, user_prompt):
    """
    This function generates a response from the Mistral API.

    Args:
        client (MistralClient): The Mistral client.
        model (str): The Mistral model to use.
        temperature (float): The temperature to use for the model.
        system_prompt (str): The system prompt to use.
        user_prompt (str): The user prompt to use.
    
    Returns:
        dict: The response from the Mistral API, with the following keys:
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    response = client.chat(
			model=model,
			response_format={"type": "json_object"},
			messages=[
				{"role":"system", "content":system_prompt},
				{"role":"user", "content":user_prompt},
			],
			max_tokens=4096,
            temperature=temperature,
	)

    return json.loads(response.choices[0].message.content)

def get_response_google(client, temperature, system_prompt, user_prompt):
    """
    This function generates a response from the Google AI API.
    
    Args:
        client (GenerativeModel): The Google AI client.
        temperature (float): The temperature to use for the model.
        system_prompt (str): The system prompt to use.
        user_prompt (str): The user prompt to use.
    
    Returns:
        dict: The response from the Google AI API, with the following keys:
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    messages = [
        {
            'role':'user',
            'parts': system_prompt,
        },
        {
            'role':'user',
            'parts': user_prompt,
        }
    ]
    response = client.generate_content(
        messages,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=4096,
            temperature=temperature,
        ),
    )

    return json.loads(response.candidates[0].content.parts[0].text)

def judge(keys, models, previous_analysis, temperature):
    """
    This function judges the final verdict based on the previous analysis.

    Args:
        keys (dict): The dictionary of API keys for the different LLM providers.
        models (dict): The dictionary of models for the different LLM providers.
        previous_analysis (list): The list of previous analysis for the different agents.
        temperature (float): The temperature to use for the model.
    
    Returns:
        dict: The final verdict, with the following keys:
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    client = OpenAI(api_key=keys["openai_api_key"])
    messages=[
        {
            "role": "system",
            "content": LINDDUN_GO_JUDGE_PROMPT,
        },
        {
            "role": "user", 
            "content": LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis)
        },
    ]
    if models["openai_model"] in ["gpt-4o", "gpt-4o-mini"]:
        class Threat(BaseModel):
            reply: bool
            reason: str
        response = client.beta.chat.completions.parse(
            model=models["openai_model"],
            response_format=Threat,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    else:
        response = client.chat.completions.create(
            model=models["openai_model"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=4096,
        )
    response_content=json.loads(response.choices[0].message.content)
    return response_content