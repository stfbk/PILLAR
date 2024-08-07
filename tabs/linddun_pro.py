import streamlit as st
from llms.linddun_pro import (
    get_linddun_pro,
    linddun_pro_gen_markdown,
)


def linddun_pro():
    st.markdown("""
The [LINDDUN Pro](https://linddun.org/pro/) tab allows you to model the privacy
threats associated with your application using the LINDDUN Pro methodology.
First, you have to provide a Data Flow Diagram in the DFD tab. Then, you can
choose each specific edge to elicit threats on that data flow. You can choose
the categories to look for, and provide a brief description of the data flow.
Finally, click the button below to generate the LINDDUN Pro threat modeling.

---
""")
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
            help="Select the edge of the DFD to find threats for.",
            key="edge_num"
        )
        st.markdown(f"{st.session_state['input']['dfd'][st.session_state['edge_num']]["from"]} -> DF{st.session_state["edge_num"]} -> {st.session_state['input']['dfd'][st.session_state['edge_num']]["to"]}")
        st.multiselect("Select the LINDDUN threat categories to look for",
            ["Linking", "Identifying", "Non-repudiation", "Detecting", "Data disclosure", "Unawareness and unintervenability", "Non-compliance"],
            help="Select the LINDDUN threat categories to look for in the threat model.",
            key="threat_categories"
        )
        st.text_area("Data flow description", help="Describe in detail the data flow for the selected edge.", key="data_flow_description", placeholder="Explain what is transferred between source and destination and how it is processed.")
        if st.button("Analyze"):
            with st.spinner("Eliciting threats in the data flow..."):
                for category in st.session_state["threat_categories"]:
                    new_threat = get_linddun_pro(
                            st.session_state["keys"]["openai_api_key"],
                            st.session_state["openai_model"],
                            st.session_state["input"]["dfd"],
                            st.session_state["input"]["dfd"][st.session_state["edge_num"]],
                            category,
                            st.session_state["data_flow_description"],
                            st.session_state["temperature"],
                        )
                    new_threat["edge"] = st.session_state["input"]["dfd"][st.session_state["edge_num"]]
                    new_threat["category"] = category
                    flag = False
                    for (i, threat) in enumerate(st.session_state["linddun_pro_threats"][st.session_state["edge_num"]]):
                        if new_threat["category"] == threat["category"]:
                            flag = True
                            st.session_state["linddun_pro_threats"][st.session_state["edge_num"]][i] = new_threat
                    if not flag:
                        st.session_state["linddun_pro_threats"][st.session_state["edge_num"]].append(new_threat)
    st.markdown("## Threats for the specified edge")
    if st.session_state["linddun_pro_threats"][st.session_state["edge_num"]]:
        markdown = linddun_pro_gen_markdown(st.session_state["linddun_pro_threats"][st.session_state["edge_num"]])
        st.markdown(markdown, unsafe_allow_html=True)
        st.download_button(
            label="Download Threat Model",
            data=markdown,
            file_name="linddun_pro_threat_model.md",
            mime="text/markdown",
        )
        st.session_state["linddun_pro_output"] = markdown

    else:
        st.markdown("No threats found for the specified edge yet, provide the necessary information and press the analyze button to find some.")
    
    
    