import json
from openai import OpenAI
from misc.utils import (
    match_category_number,
    match_number_color,
)

def linddun_pro_gen_markdown(threats):
    # Start the markdown table with headers
    markdown_output = "| Category| Threat at source | Threat at data flow | Threat at destination |\n"
    markdown_output += "|------|-------------|--------------------|------------------|\n"

    # Fill the table rows with the threat model data
    for threat in threats:
        color = match_number_color(match_category_number(threat["category"]))
        color_html = f"<p style='background-color:{color};color:#ffffff;'>"
        markdown_output += f"| {color_html}{threat['category']}</p> | {threat['source']} | {threat['data_flow']} | {threat['destination']} |\n"
    return markdown_output

def mapping_table(edge, category):
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
    return (True, True, True)


def get_linddun_pro(api_key, model, edge, category, description):
    client = OpenAI(api_key=api_key)
    
    source, data_flow, destination = mapping_table(edge, category)
    
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
You are a privacy analyst with more than 20 years of experience working with the LINDDUN Pro privacy threat modeling technique.
You are analyzing one edge of the Data Flow Diagram for a software application to identify potential privacy threats concerning that specific edge.

The input is structured as follows, enclosed in triple quotes:
'''
EDGE: {"from": "source_node", "typefrom": "source_type", "to": "destination_node", "typeto": "destination_type"}
CATEGORY: The specific LINDDUN threat category you should analyze for the edge.
DESCRIPTION: A detailed description of the data flow for the edge.
SOURCE: A boolean, indicating whether you should analyze the source node for the edge.
DATA FLOW: A boolean, indicating whether you should analyze the data flow for the edge.
DESTINATION: A boolean, indicating whether you should analyze the destination node for the edge.
'''

The output should be a detailed analysis of the possible threats of the specified category for the edge. You should consider the source, data flow, and destination nodes based on the provided information,
finding potential privacy threats and explaining why they are relevant to the source, destination or data flow. If no threats are relevant to one of these, you should explain why. If 
it is specified that you don't need to analyze the source, data flow or destination, just say "Not applicable" for that part.
The output MUST be a JSON response with the following structure:

{
    "source": "A detailed explanation of which threat of the specified category is possible at the source node.",
    "data_flow": "A detailed explanation of which threat of the specified category is possible in the data flow.",
    "destination": "A detailed explanation of which threat of the specified category is possible at the destination node.",
}
                """,
            },
            {
                "role": "user", 
                "content": f"""
'''
EDGE: {{ "from": {edge["from"]}, "typefrom": {edge["typefrom"]}, "to": {edge["to"]}, "typeto": {edge["typeto"]} }}
CATEGORY: {category}
DESCRIPTION: {description}
SOURCE: {source}
DATA FLOW: {data_flow}
DESTINATION: {destination}
'''
"""
            },
        ],
        max_tokens=4096,
    )
    threat = json.loads(response.choices[0].message.content)
    threat["category"] = category
    return threat