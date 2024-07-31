import streamlit as st
from llms.linddun_go import linddun_go_gen_markdown
from llms.threat_model import threat_model_gen_markdown
from llms.risk_assessment import (
    assessment_gen_markdown,
    get_assessment,
    get_control_measures,
    measures_gen_markdown,
    linddun_pro_gen_individual_markdown,
)


def risk_assessment():
    st.markdown("""
    The Risk Assessment tab allows you to assess the risks associated with your application.
    First, you have to execute either a Threat Model or a LINDDUN Go simulation to generate the potential threats.
    Then, import them through with the buttons below.
"""
    )
    st.markdown("""---""")
    if "to_assess" not in st.session_state:
        st.session_state["to_assess"] = []
    if "current_threat" not in st.session_state:
        st.session_state["current_threat"] = 0
    if "threat_source" not in st.session_state:
        st.session_state["threat_source"] = ""
    if "assessments" not in st.session_state:
        st.session_state["assessments"] = []
    if "control_measures" not in st.session_state:
        st.session_state["control_measures"] = []
    if "to_report" not in st.session_state:
        st.session_state["to_report"] = []

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
        empty = True
        for threat in st.session_state["linddun_pro_threats"]:
            if threat:
                empty = False
                break
        if st.button("Import LINDDUN Pro", help="Import the output of the LINDDUN Pro threat modeling to assess the risks.", disabled=empty):
            analyzed_edges = st.session_state["linddun_pro_threats"]
            to_assess = []
            for edge in analyzed_edges:
                for threats_of_categories in edge:
                    to_assess.append({"category": threats_of_categories["category"], "description": threats_of_categories["source"]})
                    to_assess.append({"category": threats_of_categories["category"], "description": threats_of_categories["data_flow"]})
                    to_assess.append({"category": threats_of_categories["category"], "description": threats_of_categories["destination"]})


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
        st.session_state["to_report"][st.session_state["current_threat"]] = st.session_state["report"]
    if st.session_state["to_assess"]:
        st.checkbox(
            "Include this threat in the report",
            value=st.session_state["to_report"][st.session_state["current_threat"]],
            key="report",
            on_change=update_checkbox,
        )
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if st.button("Generate control measures", help="Get control measures for the current threat, based on [privacy patterns](https://privacypatterns.org/)."):
            control_measures = get_control_measures(
                st.session_state["keys"]["openai_api_key"],
                st.session_state["openai_model"],
                st.session_state["to_assess"][st.session_state["current_threat"]],
                st.session_state["input"],
            )
            st.session_state["control_measures"][st.session_state["current_threat"]] = control_measures
    with col2:
        if st.session_state["control_measures"] and st.session_state["control_measures"][st.session_state["current_threat"]] != []:
            st.markdown(measures_gen_markdown(st.session_state["control_measures"][st.session_state["current_threat"]]), unsafe_allow_html=True)

    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if st.button("Generate threat impact", help="Generate an assessment of the impact of the current threat, which can then be modified."):
            assessment = get_assessment(
                st.session_state["keys"]["openai_api_key"],
                st.session_state["openai_model"],
                st.session_state["to_assess"][st.session_state["current_threat"]],
                st.session_state["input"],
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
            )
    


