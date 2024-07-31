import streamlit as st
import markdown 
import pdfkit
import base64
import urllib.parse
import graphviz

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
        
        
    if st.session_state["include_graph"] and st.session_state["is_graph_generated"]:
        text += f"![Data Flow Diagram](data:image/svg+xml,{urllib.parse.quote(graph.pipe(encoding="utf-8"))})"
    html = markdown.markdown(text)
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