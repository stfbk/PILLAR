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
import random
import streamlit as st
from openai import OpenAI
import google.generativeai as genai
# from mistralai import Mistral
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

def get_deck(shuffled=False, file="misc/deck.json"):
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
    
    result = deck["cards"]
    if shuffled:
        random.shuffle(result)
    return result


def get_linddun_go_google(client, model_name, inputs, threats_to_analyze, temperature):
    """
    This function generates a single-agent LINDDUN threat model from the prompt using Google Gemini.

    Args:
        client (GenerativeModel): The Google Gemini client.
        model_name (str): The Google model to use.
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
    print(f"Starting Google Gemini analysis with model: {model_name}")
    deck = get_deck(shuffled=True)
    threats = []

    # For each card, ask the associated questions to the LLM
    for card in deck[0:threats_to_analyze]:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]
        
        print(f"Processing card: {title}")

        system_prompt = LINDDUN_GO_SPECIFIC_PROMPTS[0] + LINDDUN_GO_SYSTEM_PROMPT
        user_prompt = LINDDUN_GO_USER_PROMPT(inputs, question, title, description)
        
        messages = [
            {
                'role': 'user',
                'parts': [{'text': system_prompt}],
            },
            {
                'role': 'user',
                'parts': [{'text': user_prompt}],
            }
        ]
        
        try:
            print(f"Sending request to Google Gemini API")
            response = client.generate_content(
                messages,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    max_output_tokens=4096,
                    temperature=temperature,
                ),
            )
            
            print(f"Received response from Google Gemini API")
            if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
                print(f"Response text: {response_text[:100]}...")  # Print first 100 chars
                response_content = json.loads(response_text)
            else:
                print("Empty or invalid response from Google Gemini API")
                response_content = {"reply": False, "reason": "Google API response was empty or invalid."}
        except Exception as e:
            print(f"Error with Google Gemini API: {str(e)}")
            response_content = {"reply": False, "reason": f"Error processing with Google API: {str(e)}"}
        
        response_content["question"] = question
        response_content["threat_title"] = title
        response_content["threat_description"] = description
        response_content["threat_type"] = type

        threats.append(response_content)
        print(f"Completed card: {title}")

    print(f"Completed Google Gemini analysis, processed {len(threats)} threats")
    return threats


def get_linddun_go(api_key, model_name, inputs, threats_to_analyze, temperature, provider=None):
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
    if provider == "Ollama":
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    elif provider == "Local LM Studio":
        client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lmstudio"
        )
    elif provider == "Google AI API":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            google_client = genai.GenerativeModel(
                model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            return get_linddun_go_google(google_client, model_name, inputs, threats_to_analyze, temperature)
        except Exception as e:
            print(f"Error initializing Google AI client: {str(e)}")
            raise Exception(f"Error initializing Google AI client: {str(e)}")
    elif provider == "Mistral API":
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI(api_key=api_key)
    deck = get_deck(shuffled=True)

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
                reason: str
                reply: bool
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



def get_multiagent_linddun_go(keys, models, inputs, temperature, rounds, threats_to_analyze, llms_to_use, lmstudio=False, ollama=False):
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

    # Initialize clients based on selected providers
    clients = {}
    if "OpenAI API" in llms_to_use:
        clients["OpenAI API"] = OpenAI(api_key=keys["openai_api_key"])
    if "Local LM Studio" in llms_to_use:
        clients["Local LM Studio"] = OpenAI(base_url="http://127.0.0.1:7860/v1", api_key="lm-studio")
    if "Ollama" in llms_to_use:
        clients["Ollama"] = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    if "Mistral API" in llms_to_use:
        clients["Mistral API"] = OpenAI(api_key=keys["mistral_api_key"])
    if "Google AI API" in llms_to_use:
        genai.configure(api_key=keys["google_api_key"])
        clients["Google AI API"] = genai.GenerativeModel(
            models["google_model"],
            generation_config={"response_mime_type": "application/json"}
        )

    threats = []
    deck = get_deck(shuffled=True)

    # Separate judge provider/model from agent pool
    if ollama:
        judge_model = models.get("ollama_models")[0]  # First model is judge
        agent_models = models.get("ollama_models")[1:] if len(models.get("ollama_models", [])) > 1 else [judge_model]
    elif lmstudio:
        judge_model = models.get("lmstudio_models")[0]
        agent_models = models.get("lmstudio_models")[1:] if len(models.get("lmstudio_models", [])) > 1 else [judge_model]
    else:
        # For cloud providers
        judge_provider = llms_to_use[0]  # First provider is judge
        agent_providers = llms_to_use[1:] if len(llms_to_use) > 1 else [judge_provider]
        
        # Map providers to their models
        judge_model = {
            "OpenAI API": models.get("openai_model"),
            "Mistral API": models.get("mistral_model"),
            "Google AI API": models.get("google_model")
        }.get(judge_provider)
        
        agent_models = []
        for provider in agent_providers:
            if provider == "OpenAI API":
                agent_models.append(models.get("openai_model"))
            elif provider == "Mistral API":
                agent_models.append(models.get("mistral_model"))
            elif provider == "Google AI API":
                agent_models.append(models.get("google_model"))

    for card in deck[0:threats_to_analyze]:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]
        previous_analysis = [{} for _ in range(6)]
        
        for round in range(rounds):
            # First round: all agents participate
            # Subsequent rounds: only competent agents
            agents_this_round = range(6) if round == 0 else card["competent_agents"]
            
            for i in agents_this_round:
                if round > 0 and i not in card["competent_agents"]:
                    continue

                # Select model for current agent from pool (excluding judge model)
                model_index = (i % len(agent_models))
                current_model = agent_models[model_index]
                
                system_prompt = LINDDUN_GO_SPECIFIC_PROMPTS[i] + LINDDUN_GO_SYSTEM_PROMPT
                user_prompt = LINDDUN_GO_USER_PROMPT(inputs, question, title, description)

                if ollama:
                    response_content = get_response_openai(
                        clients["Ollama"],
                        current_model,
                        temperature,
                        system_prompt,
                        user_prompt,
                        ollama=True
                    )
                elif lmstudio:
                    response_content = get_response_openai(
                        clients["Local LM Studio"],
                        current_model,
                        temperature,
                        system_prompt,
                        user_prompt,
                        lmstudio=True
                    )
                else:
                    # Get current provider for the model
                    current_provider = llms_to_use[model_index % len(llms_to_use)]
                    if current_provider == "OpenAI API":
                        response_content = get_response_openai(
                            clients["OpenAI API"],
                            current_model,
                            temperature,
                            system_prompt,
                            user_prompt
                        )
                    elif current_provider == "Mistral API":
                        response_content = get_response_mistral(
                            clients["Mistral API"],
                            current_model,
                            temperature,
                            system_prompt,
                            user_prompt
                        )
                    elif current_provider == "Google AI API":
                        response_content = get_response_google(
                            clients["Google AI API"],
                            temperature,
                            system_prompt,
                            user_prompt
                        )

                previous_analysis[i] = response_content

        # Judge phase - use dedicated judge model
        if ollama:
            final_verdict = judge(
                keys,
                {"ollama_model": judge_model},
                previous_analysis,
                temperature,
                ollama=True
            )
        elif lmstudio:
            final_verdict = judge(
                keys,
                {"lmstudio_model": judge_model},
                previous_analysis,
                temperature,
                lmstudio=True
            )
        else:
            final_verdict = judge(keys, models, previous_analysis, temperature)

        final_verdict.update({
            "question": question,
            "threat_title": title,
            "threat_description": description,
            "threat_type": type
        })

        threats.append(final_verdict)

    return threats

def get_response_openai(client, model, temperature, system_prompt, user_prompt, lmstudio=False, ollama=False):
    """
    This function generates a response from the OpenAI API, LM Studio, or Ollama.

    Args:
        client (OpenAI): The OpenAI/LM Studio/Ollama client.
        model (str): The model to use.
        temperature (float): The temperature to use for the model.
        system_prompt (str): The system prompt to use.
        user_prompt (str): The user prompt to use.
        lmstudio (bool): Whether to use LM Studio format.
        ollama (bool): Whether to use Ollama format.
    
    Returns:
        dict: The response with the following keys:
            - reply: boolean. Whether the threat was deemed present or not.
            - reason: string. The reason for the detection or non-detection.
    """
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user", 
            "content": user_prompt,
        },
    ]

    if model in ["gpt-4o", "gpt-4o-mini"] or lmstudio:
        # Use parse format for GPT4-organic and LM Studio
        class Threat(BaseModel):
            reason: str
            reply: bool
        response = client.beta.chat.completions.parse(
            model=model,
            response_format=Threat,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
    elif ollama:
        # Use regular completion for Ollama
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=4096,
        )
    else:
        # Standard OpenAI format
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=4096,
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
            'parts': [{'text': system_prompt}],
        },
        {
            'role':'user',
            'parts': [{'text': user_prompt}],
        }
    ]
    try:
        response = client.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                max_output_tokens=4096,
                temperature=temperature,
            ),
        )
        
        # Check if response has content
        if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return json.loads(response.candidates[0].content.parts[0].text)
        else:
            # Return a default response if no valid content is found
            return {"reply": False, "reason": "Google API response was empty or invalid."} 
    except Exception as e:
        # Handle any exceptions that might occur
        print(f"Error with Google Gemini API: {str(e)}")
        return {"reply": False, "reason": f"Error processing with Google API: {str(e)}"}

def judge(keys, models, previous_analysis, temperature, judge_provider=None, lmstudio=False, ollama=False):
    """
    This function judges the final verdict based on the previous analysis.

    Args:
        keys (dict): The dictionary of API keys for the different LLM providers.
        models (dict): The dictionary of models for the different LLM providers.
        previous_analysis (list): The list of previous analysis for the different agents.
        temperature (float): The temperature to use for the model.
        judge_provider (str): The provider to use as judge (OpenAI API, Google AI API, Mistral API).
        lmstudio (bool): Whether to use LM Studio.
        ollama (bool): Whether to use Ollama.
    
    Returns:
        dict: The final verdict, with the following keys:
            - reply: boolean. Whether the threat was deemed present or not in the application by the LLM.
            - reason: string. The reason for the detection or non-detection of the threat.
    """
    if ollama:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        model_name = models.get("ollama_model")  # Get the Judge model
    elif lmstudio:
        client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
        model_name = models.get("lmstudio_model")  # Get the Judge model
    else:
        # Use specified judge provider
        if judge_provider == "Google AI API":
            genai.configure(api_key=keys["google_api_key"])
            client = genai.GenerativeModel(models["google_model"])
            model_name = models.get("google_model")
        elif judge_provider == "Mistral API":
            client = OpenAI(api_key=keys["mistral_api_key"])
            model_name = models.get("mistral_model")
        else:  # Default to OpenAI
            client = OpenAI(api_key=keys["openai_api_key"])
            model_name = models.get("openai_model")

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

    if model_name in ["gpt-4o", "gpt-4o-mini"] or lmstudio:
        class Threat(BaseModel):
            reason: str
            reply: bool
        response = client.beta.chat.completions.parse(
            model=model_name,
            response_format=Threat,
            temperature=temperature,
            messages=messages,
            max_tokens=4096,
        )
        response_content = json.loads(response.choices[0].message.content)
    elif judge_provider == "Google AI API":
        google_messages = [
            {
                'role':'user',
                'parts': [{'text': LINDDUN_GO_JUDGE_PROMPT}],
            },
            {
                'role':'user',
                'parts': [{'text': LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis)}],
            }
        ]
        try:
            response = client.generate_content(
                google_messages,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    max_output_tokens=4096,
                    temperature=temperature,
                ),
            )
            if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                response_content = json.loads(response.candidates[0].content.parts[0].text)
            else:
                response_content = {"reply": False, "reason": "Google API judge response was empty or invalid."}
        except Exception as e:
            print(f"Error with Google Gemini API in judge: {str(e)}")
            response_content = {"reply": False, "reason": f"Error processing with Google API judge: {str(e)}"}
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=4096,
        )
        response_content = json.loads(response.choices[0].message.content)
    return response_content