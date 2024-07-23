import json
from openai import OpenAI


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

The output should be a detailed analysis of the possible threats of the specified category for the edge. You should consider the source, data flow, and destination nodes based on the provided information.
The output MUST be a JSON response with the following structure:

{
    "threat": "A brief description of the identified threat.",
    "reason": "A detailed explanation of why the threat is relevant to the specified edge.",
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
    return json.loads(response.choices[0].message.content)