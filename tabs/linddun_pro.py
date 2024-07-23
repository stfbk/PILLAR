import streamlit as st
from llms.linddun_pro import get_linddun_pro


def linddun_pro():
    st.markdown("""
The LINDDUN Pro tab allows you to model the privacy threats associated with your application using the LINDDUN Pro methodology.
First, you have to provide a Data Flow Diagram in the DFD tab. Then, choose which edges of the DFD to assess the risks for,
and which LINDDUN threat category to look for. Finally, click the button below to generate the LINDDUN Pro threat modeling.
""")
    st.markdown("""---""")
    if "linddun_pro_output" not in st.session_state:
        st.session_state["linddun_pro_output"] = ""
    if "linddun_pro_threats" not in st.session_state:
        st.session_state["linddun_pro_threats"] = []
    
    if len(st.session_state["linddun_pro_threats"]) != len(st.session_state["input"]["dfd"]):
        st.session_state["linddun_pro_threats"] = [[] for _ in st.session_state["input"]["dfd"]]
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.graphviz_chart(st.session_state["input"]["graph"])
    with col2:
        st.selectbox("Select the edge to consider", 
            [i for i in range(len(st.session_state["input"]["dfd"]))],
            help="Select the edge of the DFD to find threats for. Choosing a bidirectional edge will assess both flows.",
            key="edge_num"
        )
        st.multiselect("Select the LINDDUN threat categories to look for",
            ["Linking", "Identifying", "Non-repudiation", "Detecting", "Data disclosure", "Unawareness and unintervenability", "Non-compliance"],
            help="Select the LINDDUN threat categories to look for in the threat model.",
            key="threat_categories"
        )
        st.text_area("Data flow description", help="Describe in detail the data flow for the selected edge.", key="data_flow_description")
        if st.button("Analyze"):
            for category in st.session_state["threat_categories"]:
                st.session_state["linddun_pro_threats"][st.session_state["edge_num"]].append(
                    get_linddun_pro(
                        st.session_state["keys"]["openai_api_key"],
                        st.session_state["openai_model"],
                        st.session_state["input"]["dfd"][st.session_state["edge_num"]],
                        category,
                        st.session_state["data_flow_description"],
                    )
                )
                print(st.session_state["linddun_pro_threats"])
    
    
    