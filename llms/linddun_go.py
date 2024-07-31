import json
import google.generativeai as genai
import random
from openai import OpenAI
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
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

# Function to convert JSON to Markdown for display.
def linddun_go_gen_markdown(present_threats):
    # Start the markdown table with headers
    markdown_output = "| Threat Name | Threat description | Detection reason |\n"
    markdown_output += "|-------------|--------------------|------------------|\n"

    # Fill the table rows with the threat model data
    for threat in present_threats:
        color = match_number_color(threat["threat_type"])
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{match_letter(threat['threat_type'])} - {threat['threat_title']}</p> | {threat['threat_description']} | {threat['reason']} |\n"


    return markdown_output

def get_deck(file="misc/deck.json"):
    with open(file, 'r') as deck_file:
        deck = json.load(deck_file)
    return deck["cards"]


def get_linddun_go(api_key, model_name, inputs, temperature):
    client = OpenAI(api_key=api_key)
    deck = get_deck()
    

    threats = []

    for card in deck:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": LINDDUN_GO_SPECIFIC_PROMPTS[0]+LINDDUN_GO_SYSTEM_PROMPT,
                }, 
                {
                    "role": "user", 
                    "content": LINDDUN_GO_USER_PROMPT(inputs, question, title, description)
                },
            ],
            max_tokens=4096,
        )
        # Convert the JSON string in the 'content' field to a Python dictionary
        response_content = json.loads(response.choices[0].message.content)
        response_content["question"] = question
        response_content["threat_title"] = title
        response_content["threat_description"] = description
        response_content["threat_type"] = type
        #print(response_content)
        threats.append(response_content)

    return threats



def get_multiagent_linddun_go(keys, models, inputs, temperature, rounds, threats_to_analyze, llms_to_use):
    openai_client = OpenAI(api_key=keys["openai_api_key"]) if "OpenAI API" in llms_to_use else None
    mistral_client = MistralClient(api_key=keys["mistral_api_key"]) if "Mistral API" in llms_to_use else None
    if "Google AI API" in llms_to_use:
        genai.configure(api_key=keys["google_api_key"])
        google_client = genai.GenerativeModel(
                models["google_model"], generation_config={"response_mime_type": "application/json"}
        )
    else:
        google_client = None
    threats = []
    deck = get_deck()
    random.shuffle(deck)


    for card in deck[0:threats_to_analyze]:
        question = "\n".join(card["questions"])
        title = card["title"]
        description = card["description"]
        type = card["type"]
        previous_analysis = [{} for _ in range(6)]
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

                #print(llm)
                #print(response_content)
                
                previous_analysis[i] = response_content
                #print(response_content)
            #print(previous_analysis)
        final_verdict = judge(keys, models, previous_analysis, temperature)
        final_verdict["question"] = question
        final_verdict["threat_title"] = title
        final_verdict["threat_description"] = description
        final_verdict["threat_type"] = type
        #print(final_verdict)
        threats.append(final_verdict)
    #print(f"Present threats:\n{present_threats}")

    return threats

def get_response_openai(client, model, temperature, system_prompt, user_prompt):
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user", 
                "content": user_prompt,
            },
        ],
        max_tokens=4096,
        temperature=temperature,
    )
    return json.loads(response.choices[0].message.content)

def get_response_mistral(client, model, temperature, system_prompt, user_prompt):

	response = client.chat(
			model=model,
			response_format={"type": "json_object"},
			messages=[
				ChatMessage(role="system", content=system_prompt),
				ChatMessage(role="user", content=user_prompt),
			],
			max_tokens=4096,
            temperature=temperature,
	)

	return json.loads(response.choices[0].message.content)

def get_response_google(client, temperature, system_prompt, user_prompt):
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
    client = OpenAI(api_key=keys["openai_api_key"])
    response = client.chat.completions.create(
        model=models["openai_model"],
        response_format={"type": "json_object"},
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": LINDDUN_GO_JUDGE_PROMPT,
            },
            {
                "role": "user", 
                "content": LINDDUN_GO_PREVIOUS_ANALYSIS_PROMPT(previous_analysis)
            },
        ],
        max_tokens=4096,
    )
    response_content=json.loads(response.choices[0].message.content)
    return response_content