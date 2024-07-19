import streamlit as st
from llms.linddun_go import linddun_go_gen_markdown
from llms.threat_model import threat_model_gen_markdown


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

    if st.button("Import LINDDUN Go", help="Import the output of the LINDDUN Go simulation to assess the risks.", disabled=not st.session_state["linddun_go_threats"]):
        st.session_state["to_assess"] = st.session_state["linddun_go_threats"]
        st.session_state["threat_source"] = "linddun_go"
    if st.button("Import Threat Model", help="Import the output of the Threat Model to assess the risks.", disabled=not st.session_state["threat_model_threats"]):
        st.session_state["to_assess"] = st.session_state["threat_model_threats"]
        st.session_state["threat_source"] = "threat_model"
    
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
            else:
                markdown = threat_model_gen_markdown([st.session_state["to_assess"][st.session_state["current_threat"]]])
            st.markdown(markdown, unsafe_allow_html=True)

    
    


