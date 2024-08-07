import streamlit as st
from llms.linddun_go import linddun_go_gen_markdown
from llms.threat_model import threat_model_gen_markdown
from llms.risk_assessment import (
    get_assessment,
    get_control_measures,
    measures_gen_markdown,
    linddun_pro_gen_individual_markdown,
)


def risk_assessment():
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
        
        
    st.markdown("""
This tab allows you to carry out impact assessment associated the threats found
within your application. First, you have to execute privacy threat modeling in
either the Threat Model, LINDDUN Go or LINDDUN Pro tabs, to generate the
potential threats. Then, import the threats using the buttons below. You can
then navigate through the threats, and generate an impact assessment and
control measures for each one.

---
"""
    )

    # Import the threats from the Threat Model, LINDDUN Go, or LINDDUN Pro tabs
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Import Threat Model", help="Import the output of the Threat Model to assess the risks.", disabled=not st.session_state["threat_model_threats"]):
            st.session_state["to_assess"] = st.session_state["threat_model_threats"]
            st.session_state["threat_source"] = "threat_model"
            st.session_state["assessments"] = [{"impact": ""} for _ in st.session_state["to_assess"]]
            st.session_state["control_measures"] = [[] for _ in st.session_state["to_assess"]]
            st.session_state["to_report"] = [False for _ in st.session_state["to_assess"]]
            st.session_state["current_threat"] = 0
    with col2:
        if st.button("Import LINDDUN Go", help="Import the output of the LINDDUN Go simulation to assess the risks.", disabled=not st.session_state["linddun_go_threats"]):
            st.session_state["to_assess"] = st.session_state["linddun_go_threats"]
            st.session_state["threat_source"] = "linddun_go"
            st.session_state["assessments"] = [{"impact": ""} for _ in st.session_state["to_assess"]]
            st.session_state["control_measures"] = [[] for _ in st.session_state["to_assess"]]
            st.session_state["to_report"] = [False for _ in st.session_state["to_assess"]]
            st.session_state["current_threat"] = 0
    with col3:
        # The LINDDUN Pro initialization is a bit more complex, as it requires some transformation of the data
    
        # This variable is used to check if the list of threats is empty, to disable the import button
        empty = True
        for threat in st.session_state["linddun_pro_threats"]:
            if threat:
                empty = False
                break
        
        if st.button("Import LINDDUN Pro", help="Import the output of the LINDDUN Pro threat modeling to assess the risks.", disabled=empty):
            analyzed_edges = st.session_state["linddun_pro_threats"]
            to_assess = []
            
            # For each edge in the DFD, the LINDDUN Pro tab finds a threat at the source, data flow, and destination.
            # For the risk assessment, we want to assess each of these threats separately.
            # Thus, we create three separate threats for each edge, one for each location.
            for (i, edge) in enumerate(analyzed_edges):
                for threats_of_categories in edge:
                    to_assess.append({
                        "category": threats_of_categories["category"], 
                        "description": threats_of_categories["source"], 
                        "edge": threats_of_categories["edge"], 
                        "threat_tree_node": threats_of_categories["source_id"],
                        "threat_title": threats_of_categories["source_title"],
                        "threat_location": "source",
                        "data_flow_number": i,
                    })
                    to_assess.append({
                        "category": threats_of_categories["category"], 
                        "description": threats_of_categories["data_flow"], 
                        "edge": threats_of_categories["edge"], 
                        "threat_tree_node": threats_of_categories["data_flow_id"],
                        "threat_title": threats_of_categories["data_flow_title"],
                        "threat_location": "data_flow",
                        "data_flow_number": i,
                    })
                    to_assess.append({
                        "category": threats_of_categories["category"], 
                        "description": threats_of_categories["destination"],
                        "edge": threats_of_categories["edge"], 
                        "threat_tree_node": threats_of_categories["destination_id"],
                        "threat_title": threats_of_categories["destination_title"],
                        "threat_location": "destination",
                        "data_flow_number": i,
                    })


            st.session_state["to_assess"] = to_assess
            st.session_state["threat_source"] = "linddun_pro"
            st.session_state["assessments"] = [{"impact": ""} for _ in st.session_state["to_assess"]]
            st.session_state["control_measures"] = [[] for _ in st.session_state["to_assess"]]
            st.session_state["to_report"] = [False for _ in st.session_state["to_assess"]]
            st.session_state["current_threat"] = 0
            
        
    
    col1, col2, col3 = st.columns([0.1,0.8,0.1])
    with col1:
        if st.button("<", help="Go to the previous threat."):
            st.session_state["current_threat"] = max(0, st.session_state["current_threat"] - 1)
    with col3:
        if st.button(r"\>", help="Go to the next threat."):
            st.session_state["current_threat"] = min(len(st.session_state["to_assess"]) - 1, st.session_state["current_threat"] + 1)
    with col2:
        if st.session_state["to_assess"]:
            if st.session_state["threat_source"] == "linddun_go":
                markdown = linddun_go_gen_markdown([st.session_state["to_assess"][st.session_state["current_threat"]]])
            elif st.session_state["threat_source"] == "threat_model":
                markdown = threat_model_gen_markdown([st.session_state["to_assess"][st.session_state["current_threat"]]])
            elif st.session_state["threat_source"] == "linddun_pro":
                markdown = linddun_pro_gen_individual_markdown(st.session_state["to_assess"][st.session_state["current_threat"]])
            st.markdown(markdown, unsafe_allow_html=True)
    
    def update_checkbox():
        """Simple function to update the checkbox value in the session state."""
        st.session_state["to_report"][st.session_state["current_threat"]] = st.session_state["report"]

    if st.session_state["to_assess"]:
        st.checkbox(
            "Include this threat in the report",
            value=st.session_state["to_report"][st.session_state["current_threat"]],
            key="report",
            on_change=update_checkbox,
        )
    
    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        if st.button("Impact assessment", help="Generate an assessment of the impact of the current threat, which can then be modified.", disabled=not st.session_state["to_assess"]):
            with st.spinner("Assessing impact..."):
                assessment = get_assessment(
                    st.session_state["keys"]["openai_api_key"],
                    st.session_state["openai_model"],
                    st.session_state["to_assess"][st.session_state["current_threat"]],
                    st.session_state["input"],
                    st.session_state["temperature"],
                )
                st.session_state["assessments"][st.session_state["current_threat"]] = assessment
    with col2:
        if st.session_state["assessments"]:
            st.text_area(
                "Impact",
                value=st.session_state["assessments"][st.session_state["current_threat"]]["impact"], 
                key="impact",
                on_change=lambda: st.session_state["assessments"][st.session_state["current_threat"]].update({"impact": st.session_state["impact"]}),
                label_visibility="collapsed",
                help="The impact of the threat on the system, as generated by the AI model.",
                height=150,
            )
    
    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        if st.button("Control suggestions", help="Get control measures for the current threat, based on [privacy patterns](https://privacypatterns.org/).", disabled=not st.session_state["to_assess"]):
            with st.spinner("Generating control measures..."):
                control_measures = get_control_measures(
                    st.session_state["keys"]["openai_api_key"],
                    st.session_state["openai_model"],
                    st.session_state["to_assess"][st.session_state["current_threat"]],
                    st.session_state["input"],
                    st.session_state["temperature"],
                )
                st.session_state["control_measures"][st.session_state["current_threat"]] = control_measures
    with col2:
        if st.session_state["control_measures"] and st.session_state["control_measures"][st.session_state["current_threat"]] != []:
            st.markdown(measures_gen_markdown(st.session_state["control_measures"][st.session_state["current_threat"]]), unsafe_allow_html=True)



