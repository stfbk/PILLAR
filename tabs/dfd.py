import streamlit as st
import graphviz
import csv
from io import StringIO


def dfd():
    st.markdown("""
In this section, you can create a Data Flow Diagram (DFD) to visualize the flow of data within your application. Use the editor below to create a DFD for your application.
""")
    st.markdown("""---""")
    col1, col2 = st.columns([0.6,0.4])
    if "dfd" not in st.session_state["input"]:
        st.session_state["input"]["dfd"] = []
    if "graph" not in st.session_state["input"]:
        st.session_state["input"]["graph"] = graphviz.Digraph()
    with col1:
        col11, col12 = st.columns([1,1])
        with col11:
            if st.button("Update graph", help="Update the graph with the data currently in the table."):
                graph = graphviz.Digraph()
                graph.attr(
                    bgcolor=f"{st.get_option("theme.backgroundColor")}",
                )
                graph.node_attr.update(
                    color=f"{st.get_option("theme.primaryColor")}",
                    fontcolor="white",
                )
                for object in st.session_state["input"]["dfd"]:
                    graph.node(object["from"], shape=f"{"box" if object["typefrom"] == "Entity" else "ellipse" if object["typefrom"] == "Process" else "cylinder"}")
                    graph.node(object["to"], shape=f"{"box" if object["typeto"] == "Entity" else "ellipse" if object["typeto"] == "Process" else "cylinder"}")
                    graph.edge(object["from"], object["to"], _attributes={"color": "white"})
                print(graph.source)
                st.session_state["input"]["graph"] = graph
        with col12:
            uploaded_file = st.file_uploader(
                "Upload DFD", 
                type=["csv"], 
                help="Upload a CSV file containing the DFD, in the format of a list of dictionaries with keys 'from', 'typefrom', 'to', and 'typeto', representing each edge.",
                key="dfd_file"
            )
            if uploaded_file is not None:
                try:
                    reader = csv.DictReader(StringIO(uploaded_file.getvalue().decode("utf-8-sig")), delimiter=",")
                    dfd = list(reader)
                    st.session_state["input"]["dfd"] = dfd
                except Exception as e:
                    st.error(f"Error reading the uploaded file: {e}")
        edges = st.data_editor(
            data=[
                {"from": "User", "typefrom": "Entity", "to": "Application", "typeto": "Process"}
            ],
            column_config={
                "from": st.column_config.TextColumn("From", help="The starting point of the edge.", width="medium", required=True),
                "typefrom": st.column_config.SelectboxColumn("Type", help="The type of the starting element", width="medium", required=True, options=["Entity", "Data store", "Process"]),
                "to": st.column_config.TextColumn("To", help="The destination of the edge.", width="medium", required=True),
                "typeto": st.column_config.SelectboxColumn("Type", help="The type of the destination element", width="medium", required=True, options=["Entity", "Data store", "Process"]),
            },
            num_rows="dynamic",
        )
        if edges != st.session_state["input"]["dfd"] and st.session_state["dfd_file"] is None:
            st.session_state["input"]["dfd"] = []
            st.session_state["input"]["dfd"] = edges
    with col2:
        st.graphviz_chart(st.session_state["input"]["graph"])