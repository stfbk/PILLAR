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

import streamlit as st
import graphviz
import random
import json
from tabs.sidebar import sidebar
from tabs.application_info import application_info
from tabs.dfd import dfd
from tabs.threat_model import threat_model
from tabs.linddun_go import linddun_go
from tabs.linddun_pro import linddun_pro
from tabs.risk_assessment import risk_assessment
from tabs.report import report


def init_session_state():
    """
    This function initializes the session state for the application. It creates
    the necessary session state variables and sets their initial values. To
    understand the structure of the session state, please refer to the comments
    in the code below. If the code uses a session state variable that is not
    initialized here, it probably means that the variable is associated with a
    specific streamlit element, with the "key" parameter. In that case, the
    variable is initialized when the element is created and always has the
    value of the element. Look for the element in the corresponding tab file to
    understand how the variable acts.
    """


    # Initialize the session state for the sidebar
    if "keys" not in st.session_state:
        # keys is a dictionary that will store the API keys, indexed such as
        # "openai_api_key", "google_api_key", "mistral_api_key"
        st.session_state["keys"] = {}
    if "openai_model" not in st.session_state:
        # openai_model is a string that will store the OpenAI model to use
        st.session_state["openai_model"] = "gpt-4o-mini"
    if "google_model" not in st.session_state:
        # google_model is a string that will store the Google AI model to use
        st.session_state["google_model"] = "gemini-1.5-pro-latest"
    if "mistral_model" not in st.session_state:
        # mistral_model is a string that will store the Mistral model to use
        st.session_state["mistral_model"] = "mistral-large-latest"
    
    # Initialize the session state for the Application Info and DFD tabs
    if "input" not in st.session_state:
        # "input" is a dictionary that stores all the user input for the
        # application information
        st.session_state["input"] = {}
        # The dictionary has the following keys:
        #   - app_description: string.  A detailed description of the application
        #   - app_type: string. The type of the application
        #   - types_of_data: list. The types of data collected by the application
        #   - has_database: bool. Whether the application describes the data collected 
        #   - database: list of dict. The type of data stored in the database. Each
        #       dict has the following keys:
        #       - data_type: string. The type of data stored in the database
        #       - encryption: bool. Whether the data type is encrypted
        #       - sensitive: bool. Whether the data is considered sensitive
        #       - notes: string. Additional information about the data type
        #   - data_policy: string. The data retention and deletion policy of the 
        #       application
        #   - user_data_control: string. The actions the user can perform on their data
        #   - dfd: list of dict. The Data Flow Diagram of the application. Each dict
        #       has the following keys:
        #       - from: string. The entity where the data flow starts
        #       - typefrom: string. The type of the entity where the data flow starts
        #       - to: string. The entity where the data flow ends
        #       - typeto: string. The type of the entity where the data flow ends
        #       - trusted: bool. Whether the data flow is trusted
        #   - graph: graphviz.Digraph. The graph representation of the Data Flow
        #       Diagram, as a graphviz Digraph object
        st.session_state["input"]["app_description"] = ""
        st.session_state["input"]["app_type"] = ""
        st.session_state["input"]["types_of_data"] = []
        st.session_state["input"]["has_database"] = False
        st.session_state["input"]["database"] = [
            {"data_type": "Name", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Email", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Password", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Address", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Location", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Phone number", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Date of Birth", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "ID card number", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
            {"data_type": "Last access time", "encryption": True, "sensitive": True, "third_party": False, "storage_location": "", "purpose": "", "notes": ""},
        ]
        st.session_state["input"]["data_policy"] = ""
        st.session_state["input"]["user_data_control"] = ""
        st.session_state["input"]["dfd"] = [ 
            {"from": "User", "typefrom": "Entity", "to": "Application", "typeto": "Process", "trusted": True },
        ]
        st.session_state["input"]["graph"] = graphviz.Digraph()
        st.session_state["input"]["graph"].attr(
            bgcolor=f"{st.get_option("theme.backgroundColor")}",
        )
    if "backup_database" not in st.session_state:
        # "backup_database" is a list of dictionaries that stores the backup of the database information, to be able to restore it if needed
        st.session_state["backup_database"] = st.session_state["input"]["database"].copy()
    if "dfd_only" not in st.session_state:
        # "dfd_only" is a boolean that indicates whether only the DFD is
        # needed, in order to disable the application description
        st.session_state["dfd_only"] = False
    if "is_graph_generated" not in st.session_state:
        # "is_graph_generated" is a boolean that indicates whether the graph
        # has already been generated, to know if it has been updated at least
        # once
        st.session_state["is_graph_generated"] = False
    if "graph_seed" not in st.session_state:
        # "graph_seed" is a string that stores a random seed to generate the
        # graph, such that it changes every time the graph is updated
        st.session_state["graph_seed"] = str(random.randint(0, 100))
    
    # Initialize the session state for the Threat Model tab
    if "threat_model_output" not in st.session_state:
        # "threat_model_output" is a string that will store the Markdown output of the threat model
        st.session_state["threat_model_output"] = ""
    if "threat_model_threats" not in st.session_state:
        # "threat_model_threats" is a list of dictionaries that will store the JSON output of the threat model.
        # Each dictionary represents a threat, and contains the following keys:
        # - "title": string. The title of the threat.
        # - "threat_type": string. The LINDDUN category of the threat, such as "L - Linking"
        # - "Scenario": string. The scenario in which the threat occurs.
        # - "Reason": string. The reason for the detection of the threat.
        st.session_state["threat_model_threats"] = []
    
    # Initialize the session state for the LINDDUN Go tab
    if "linddun_go_output" not in st.session_state:
        # "linddun_go_output" is a string that stores the Markdown output of the LINDDUN Go simulation
        st.session_state["linddun_go_output"] = ""
    if "linddun_go_threats" not in st.session_state:
        # "linddun_go_threats" is a list of dictionaries that stores the threats generated by the LINDDUN Go simulation.
        # Each dictionary represents a threat and contains the following
        # keys: 
        # - "question": string. The questions on the card, asked to the LLM to elicit the threat.
        # - "threat_title": string. The title of the threat.
        # - "threat_description": string. The description of the threat.
        # - "threat_type": int. The LINDDUN category of the threat, from 1 to 7.
        # - "reply": boolean. Whether the threat was deemed present or not in the application by the LLM.
        # - "reason": string. The reason for the detection or non-detection of the threat.
        st.session_state["linddun_go_threats"] = []
    if "max_threats" not in st.session_state:
        # "max_threats" is an integer that stores the maximum number of threats that can be analyzed in the LINDDUN Go simulation.
        # It is used to set the slider for the number of threats to analyze.
        # It is determined by the total number of cards in the LINDDUN Go deck.
        with open("misc/deck.json", "r") as deck_file:
            deck = json.load(deck_file)
        st.session_state["max_threats"] = len(deck["cards"])

    # Initialize session state for the LINDDUN Pro tab
    if "linddun_pro_output" not in st.session_state:
        # "linddun_pro_output" is a string used to store the markdown output of the LINDDUN Pro threat model
        st.session_state["linddun_pro_output"] = ""
    if "linddun_pro_threats" not in st.session_state:
        # "linddun_pro_threats" is a list of lists of dictionaries used to store the threats for each edge in the DFD.
        # The list has the same length as the DFD, and each element is a list of threats for the corresponding edge, one for each of the LINDDUN categories.
        # Thus, the structure is a matrix of N rows (one for each edge) and 7 columns (one for each LINDDUN category), where each cell is a dictionary with the threat information.
        # The dictionary contains the following keys:
        # - "category": string. The category of the threat, such as "Linking".
        # - "source_id": string. The ID of the source of the threat.
        # - "source_title": string. The title of the threat at the source.
        # - "source": string. The description of the threat at the source.
        # - "data_flow_id": string. The ID of the data flow of the threat.
        # - "data_flow_title": string. The title of the threat at the data flow.
        # - "data_flow": string. The description of the threat at the data flow.
        # - "destination_id": string. The ID of the destination of the threat.
        # - "destination_title": string. The title of the threat at the destination.
        # - "destination": string. The description of the threat at the destination.
        # - "edge": dictionary. The edge of the DFD that the threat is associated with, with the same keys as the DFD edge.
        st.session_state["linddun_pro_threats"] = []
        
    # Initialize session state for the Risk Assessment tab
    if "to_assess" not in st.session_state:
        # "to_assess" is a list of dictionaries used to store the threats to
        # assess. Each dictionary can contain different keys depending on the
        # threat elicitation method that has been used. For Threat Model and
        # LINDDUN Go, the dictionaries contain the same keys as
        # "threat_model_threats" and "linddun_go_threats", respectively.
        # For LINDDUN Pro, the dictionaries contain the following keys:
        # - "category": string. The category of the threat.
        # - "description": string. The description of the threat.
        # - "edge": dictionary. The edge of the DFD that the threat is associated with, with the same keys as the DFD edge.
        # - "threat_tree_node": string. The nodes of the threat tree involved in the threat.
        # - "threat_title": string. The title of the threat.
        # - "threat_location": string. The location of the threat in the DFD edge (source, data_flow, or destination).
        # - "data_flow_number": integer. The number of the data flow in the DFD edge
        st.session_state["to_assess"] = []
    if "current_threat" not in st.session_state:
        # "current_threat" is an integer used to store the index of the current threat being assessed.
        st.session_state["current_threat"] = 0
    if "threat_source" not in st.session_state:
        # "threat_source" is a string used to store the source of the threats being assessed.
        st.session_state["threat_source"] = ""
    if "assessments" not in st.session_state:
        # "assessments" is a list of dictionaries used to store the impact assessments of the threats.
        # Each dictionary contains only one key (in the future, it could be expanded to include more information):
        # - "impact": string. The impact of the threat on the system.
        st.session_state["assessments"] = []
    if "control_measures" not in st.session_state:
        # "control_measures" is a list of lists of dictionaries used to store
        # the control measures for the threats. The list has the same length as
        # the "to_assess" list, and each element is a list of dictionaries
        # representing control measures for the corresponding threat. Thus, the
        # structure is a matrix of N rows (one for each threat) and M columns
        # (one for each control measure), where each cell is a dictionary with
        # the control measure information.
        # Each dictionary contains the following keys:
        # - "filename": string. The filename of the control measure on the Privacy Patterns website.
        # - "title": string. The title of the control measure.
        # - "explanation": string. The explanation of the control measure.
        # - "implementation": string. The implementation of the control measure.
        st.session_state["control_measures"] = []
    if "to_report" not in st.session_state:
        # "to_report" is a list of booleans used to store whether each threat should be included in the report.
        st.session_state["to_report"] = []

        
# Streamlit configuration
st.set_page_config(
    page_title="P.I.L.L.A.R.",
    page_icon="images/logo1.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
            'Report a bug': "https://github.com/AndreaBissoli/PILLAR/issues",
            'About': """
**PILLAR** (**P**rivacy risk **I**dentification with **L**INDDUN and **L**LM
**A**nalysis **R**eport) is a tool developed by [Andrea Bissoli](https://www.linkedin.com/in/andrea-bissoli/) 
under the supervision of
[Dr. Majid Mollaeefar](https://www.linkedin.com/in/majid-mollaeefar/) as an
internship project for [Fondazione Bruno Kessler](https://www.fbk.eu/). The
tool is designed to help developers and security professionals to assess the
privacy and information leakage risks of their applications. It provides a
user-friendly interface to create Data Flow Diagrams, generate threat models,
and perform risk assessments based on the LINDDUN methodology. The tool is
open-source and can be found on
[GitHub](https://github.com/AndreaBissoli/PILLAR).""",
    }
)

# Initialization for the whole app
init_session_state()

# Call all the UI functions
sidebar()

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Application Info", "DFD", "Threat Model", "LINDDUN Go", "LINDDUN Pro", "Risk Assessment", "Report"],
)

with tab1:
    application_info()
        
with tab2:
    dfd()

with tab3:
    threat_model()

with tab4:
    linddun_go()

with tab5:
    linddun_pro()

with tab6:
    risk_assessment()

with tab7:
    report()
    

