import streamlit as st
import graphviz
import csv
import pandas as pd
import base64
import json
from io import StringIO
from llms.dfd import get_dfd

from llms.threat_model import (
    get_image_analysis,
)

def dfd():
    st.markdown("""
In this section, you can create a Data Flow Diagram (DFD) to visualize the flow
of data within your application, helped by AI. You can let the LLM generate a
DFD for you, and then you can modify it with the table editor. You can also
download and upload a CSV file representing the DFD. The DFD is represented as
a list of dictionaries with keys 'from', 'typefrom', 'to', 'typeto' and
'bidirectional', representing each edge. 
""")
    st.markdown("""---""")
    if "dfd" not in st.session_state["input"]:
        st.session_state["input"]["dfd"] = [ 
            {"from": "User", "typefrom": "Entity", "to": "Application", "typeto": "Process", "bidirectional": True},
        ]
    if not st.session_state["input"]["dfd"]:
        st.session_state["input"]["dfd"] = [
            { "from": "User", "typefrom": "Entity", "to": "Application", "typeto": "Process", "bidirectional": True },
        ]
    if "graph" not in st.session_state["input"]:
        st.session_state["input"]["graph"] = graphviz.Digraph()
        st.session_state["input"]["graph"].attr(
            bgcolor=f"{st.get_option("theme.backgroundColor")}",
        )

    def update_edges():
        changes = st.session_state["edges"]
        state = st.session_state["input"]["dfd"]
        for item in changes["edited_rows"]:
            for key in changes["edited_rows"][item]:
                state[item][key] = changes["edited_rows"][item][key]
        for added in changes["added_rows"]:
            state.append(added)
        for deleted in sorted(changes["deleted_rows"], reverse=True): # to avoid index errors
            state.pop(deleted)

        st.session_state["input"]["dfd"] = state

    st.checkbox("DFD only", value=False, key="dfd_only", help="Check this box if you only want to use a Data Flow Diagram for the threat modeling, without including the application description.")
    st.session_state["input"]["dfd_only"] = st.session_state["dfd_only"]
    st.checkbox("Include DFD in application info for threat modeling", key="use_dfd", help="Choose whether or not to include the DFD in the subsequent threat modeling process, together with the application description. Including it adds context to the LLM, but also increases token count.", disabled=st.session_state["dfd_only"])
    st.session_state["input"]["use_dfd"] = st.session_state["use_dfd"]
    col1, col2 = st.columns([0.6,0.4])
    with col1:
        col11, col12, col13 = st.columns([0.4,0.4,0.2])
        with col12:
            if st.session_state["model_provider"] == "OpenAI API":
                selected_model = "gpt-4o"
                openai_api_key = st.session_state["keys"]["openai_api_key"]
                uploaded_file = st.file_uploader(
                    "Upload DFD image", type=["jpg", "jpeg", "png"],
                    help="Upload an image of the DFD to be analyzed by the AI model and converted for later usage.",
                )
                if uploaded_file is not None:
                    if not openai_api_key:
                        st.error("Please enter your OpenAI API key to analyse the image.")
                    else:
                        if (
                            "uploaded_file" not in st.session_state
                            or st.session_state["uploaded_file"] != uploaded_file
                        ):
                            st.session_state["uploaded_file"] = uploaded_file
                            with st.spinner("Analysing the uploaded image..."):

                                def encode_image(uploaded_file):
                                    return base64.b64encode(uploaded_file.read()).decode(
                                        "utf-8"
                                    )

                                base64_image = encode_image(uploaded_file)

                                try:
                                    image_analysis_output = get_image_analysis(
                                        openai_api_key,
                                        selected_model,
                                        base64_image,
                                    )
                                    if (
                                        image_analysis_output
                                        and "choices" in image_analysis_output
                                        and image_analysis_output["choices"][0]["message"][
                                            "content"
                                        ]
                                    ):
                                        image_analysis_content = image_analysis_output[
                                            "choices"
                                        ][0]["message"]["content"]
                                        st.session_state["image_analysis_content"] = (
                                            image_analysis_content
                                        )
                                        # Update app_description session state
                                        st.session_state["input"]["dfd"] = (
                                            json.loads(image_analysis_content)["dfd"]
                                        )
                                    else:
                                        st.error(
                                            "Failed to analyze the image. Please check the API key and try again."
                                        )
                                except KeyError as e:
                                    st.error(
                                        "Failed to analyze the image. Please check the API key and try again."
                                    )
                                    print(f"Error: {e}")
                                except Exception as e:
                                    st.error(
                                        "An unexpected error occurred while analyzing the image."
                                    )
                                    print(f"Error: {e}")
        with col13:
            if st.button("AI generation", help="Generate a DFD graph from the application information provided in the previous tab, using the AI model.", disabled=st.session_state["dfd_only"]):
                st.session_state["input"]["dfd"] = get_dfd(
                    st.session_state["keys"]["openai_api_key"],
                    st.session_state["openai_model"],
                    st.session_state["temperature"],
                    st.session_state["input"],
                )["dfd"]
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
                    if object["bidirectional"]:
                        graph.edge(object["to"], object["from"], _attributes={"color": "white"})
                #print(graph.source)
                st.session_state["input"]["graph"] = graph
        with col11:
            uploaded_file = st.file_uploader(
                "Upload DFD", 
                type=["csv"], 
                help="Upload a CSV file containing the DFD, in the format of a list of dictionaries with keys 'from', 'typefrom', 'to', 'typeto' and 'bidirectional', representing each edge.",
                key="dfd_file"
            )
            if uploaded_file is not None:
                try:
                    reader = csv.DictReader(StringIO(uploaded_file.getvalue().decode("utf-8-sig")), delimiter=",")
                    dfd = list(reader)
                    for edge in dfd:
                        edge["bidirectional"] = True if edge["bidirectional"] == "true" else False
                    st.session_state["input"]["dfd"] = dfd
                except Exception as e:
                    st.error(f"Error reading the uploaded file: {e}")
    with col2:
        st.graphviz_chart(st.session_state["input"]["graph"])
    def format_correct(state):
        new_dict = {
            "from": [],
            "typefrom": [],
            "to": [],
            "typeto": [],
            "bidirectional": [],
        }
        for object in state:
            new_dict["from"].append(object.get("from"))
            new_dict["typefrom"].append(object.get("typefrom"))
            new_dict["to"].append(object.get("to"))
            new_dict["typeto"].append(object.get("typeto"))
            bool(new_dict["bidirectional"].append(object.get("bidirectional")))
        return new_dict
        
    edges = st.data_editor(
        data=pd.DataFrame().from_dict(format_correct(st.session_state["input"]["dfd"])),
        column_config={
            "from": st.column_config.TextColumn("From", help="The starting point of the edge.", width="medium", required=True),
            "typefrom": st.column_config.SelectboxColumn("Type", help="The type of the starting element", width="medium", required=True, options=["Entity", "Data store", "Process"]),
            "to": st.column_config.TextColumn("To", help="The destination of the edge.", width="medium", required=True),
            "typeto": st.column_config.SelectboxColumn("Type", help="The type of the destination element", width="medium", required=True, options=["Entity", "Data store", "Process"]),
            "bidirectional": st.column_config.CheckboxColumn("Bidirectional", help="Whether the edge is bidirectional.", width="medium", required=True, default=True),
        },
        key="edges",
        num_rows="dynamic",
        on_change=update_edges,
    )
    

