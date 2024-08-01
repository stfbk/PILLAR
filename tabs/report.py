import streamlit as st
import markdown 
import pdfkit
import urllib.parse
import graphviz
from misc.utils import (
    match_color,
    match_number_color,
    match_letter,
    match_number_category,
    match_category_number,
)
from tabs.risk_assessment import measures_gen_markdown

def report():
    st.markdown("""
Here you can download the complete report of the privacy threat modeling and risk assessment, after the previous steps have been completed.
Just fill in the required information and you will be able to download the PDF report.
    """)
    st.markdown("""---""")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.text_input("Application name", help="Enter the name of the application", key="app_name")
        st.text_input("Author", help="Enter the name of the author", key="author")
        st.text_area("High-level description", help="Enter a high-level description of the application", key="high_level_description")
    with col2:
        st.text_input("Application version", help="Enter the version of the application", key="app_version")
        st.text_input("Date", help="Enter the date of the report", key="date")
        st.checkbox("Include graph in the report", help="Include the Data Flow Diagram in the report", key="include_graph")
    

    st.download_button(
        "Download report",
        data=generate_report(),
        file_name="report.pdf",
        mime="application/pdf",
        disabled=not (st.session_state.app_name and st.session_state.author and st.session_state.high_level_description and st.session_state.app_version and st.session_state.date),
    )

    
def generate_report():
    text="""# Privacy Threat Modeling and Risk Assessment Report\n"""
    
    text += "## Report Details \n\n"
    
    text += f"| | | | |\n"
    text += f"|------|-------|-----|-----|\n"
    text += f"| **Application Name** | {st.session_state['app_name']} | **Application Version** | {st.session_state['app_version']} |\n"
    text += f"| **Report author** | {st.session_state['author']} | **Date** | {st.session_state['date']} |\n"
    text += f"| **High-level Description** | {st.session_state['high_level_description']} | | |\n\n"

        
        
    if st.session_state["include_graph"] and st.session_state["is_graph_generated"]:
        graph = graphviz.Digraph(engine='fdp', format='svg')
        graph.attr(
            bgcolor="white",
            overlap="false",
            K="1.5",
            start=st.session_state["graph_seed"]
        )
        graph.node_attr.update(
            color="black",
            fontcolor="black",
        )
        graph.edge_attr.update(
            color="black",
            fontcolor="black",
        )
        with graph.subgraph(name='cluster_0') as c:
            c.attr(
                color="#00a6fb",
                label="Trusted",
                fontcolor="#00a6fb",
                style="dashed"
            )
            for object in st.session_state["input"]["dfd"]:
                if object["trusted"]:
                    c.node(object["from"])
                if object["trusted"]:
                    c.node(object["to"])
        for (i, object) in enumerate(st.session_state["input"]["dfd"]):
            graph.node(object["from"], shape=f"{"box" if object["typefrom"] == "Entity" else "ellipse" if object["typefrom"] == "Process" else "cylinder"}")
            graph.node(object["to"], shape=f"{"box" if object["typeto"] == "Entity" else "ellipse" if object["typeto"] == "Process" else "cylinder"}")
            graph.edge(object["from"], object["to"], label=f"DF{i}", constraint="false")
        text += f"![Data Flow Diagram](data:image/svg+xml,{urllib.parse.quote(graph.pipe(encoding="utf-8"))})\n"
    
    if st.session_state["threat_source"] == "threat_model":
        text = from_threat_model(text)
    elif st.session_state["threat_source"] == "linddun_go":
        text = from_linddun_go(text)
    elif st.session_state["threat_source"] == "linddun_pro":
        text = from_linddun_pro(text)
    


    
    html = markdown.markdown(text, extensions=["markdown.extensions.tables"])
    options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }

    pdf = pdfkit.from_string(html, False, options=options)
    return pdf


def from_threat_model(text):
    text += "## Threats found with the simple threat model\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat["title"]}\n\n"
            color = match_color(threat["threat_type"])
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"

            text += f"**Category**: {color_html}{threat['threat_type']}</span>\n\n"
            text += f"**Reason for detection**: {threat['Reason']}\n\n"
            text += f"**Scenario**: {threat['Scenario']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state["control_measures"][i])}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state["assessments"][i]["impact"]}\n\n"

    return text
def from_linddun_go(text):
    text += "## Threats found with the LINDDUN Go methodology\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat["threat_title"]}\n\n"
            color = match_number_color(threat["threat_type"])
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"

            text += f"**Category**: {color_html}{match_letter(threat["threat_type"])} - {match_number_category(threat["threat_type"])}</span>\n\n"
            text += f"**Threat description**: {threat['threat_description']}\n\n"
            text += f"**Reason for detection**: {threat['reason']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state["control_measures"][i])}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state["assessments"][i]["impact"]}\n\n"
    return text
def from_linddun_pro(text):
    text += "## Threats found with the LINDDUN Pro methodology\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat["threat_title"]}\n\n"
            color = match_number_color(match_category_number(threat["category"]))
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"

            text += f"**Category**: {color_html}{match_letter(match_category_number(threat["category"]))} - {threat["category"]}</span>\n\n"
            text += f"**DFD edge**:         "
            if threat["threat_location"] == "source":
                text += f"<u>{threat['edge']['from']}</u>, DF{threat["data_flow_number"]}, {threat['edge']['to']}\n\n"
            elif threat["threat_location"] == "data_flow":
                text += f"{threat['edge']['from']}, <u>DF{threat["data_flow_number"]}</u>, {threat['edge']['to']}\n\n"
            elif threat["threat_location"] == "destination":
                text += f"{threat['edge']['from']}, DF{threat["data_flow_number"]}, <u>{threat['edge']['to']}</u>\n\n"
            text += f"**Threat tree involved nodes**: {threat['threat_tree_node']}\n\n"
            text += f"**Threat description**: {threat['description']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state["control_measures"][i])}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state["assessments"][i]["impact"]}\n\n"
    return text