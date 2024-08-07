import streamlit as st
import graphviz
import csv
import pandas as pd
import base64
import json
import random
from io import StringIO
from llms.dfd import (
    get_dfd,
    get_image_analysis,
)

    
def dfd():
    st.markdown("""
In this tab, you can create a Data Flow Diagram (DFD) to visualize the flow of
data within your application. You can, at first, let the LLM generate a DFD for
you, and then you can modify it with the table editor to refine it exactly to
your needs. The AI generation can be based either on the application
description provided or on an uploaded picture of the DFD. You can also
download (in the upper right corner of the table editor) and upload a CSV file
representing the DFD, to be able to save it for the future. The DFD is
represented as a list of dictionaries with keys 'from', 'typefrom', 'to',
'typeto' and 'trusted', representing each edge. The 'trusted' key is a boolean
value representing whether the edge stays inside the trusted boundary or traverses it.

To avoid ambiguity, in the DFD the labels are close to the _tail_ of the arrow they refer to.

---
""")
    # Initialize the session state for the DFD tab
    if "is_graph_generated" not in st.session_state:
        # "is_graph_generated" is a boolean that indicates whether the graph
        # has already been generated, to know if it has been updated at least
        # once
        st.session_state["is_graph_generated"] = False
    if "graph_seed" not in st.session_state:
        # "graph_seed" is a string that stores a random seed to generate the
        # graph, such that it changes every time the graph is updated
        st.session_state["graph_seed"] = str(random.randint(0, 100))

    # Never have an empty DFD, it breaks the data editor
    if not st.session_state["input"]["dfd"]: 
        st.session_state["input"]["dfd"] = [
            { "from": "User", "typefrom": "Entity", "to": "Application", "typeto": "Process", "trusted": True },
        ]

    def update_edges():
        """
        Update the DFD with the changes made in the data editor. This is needed
        to keep the DFD in sync with the table editor, because the data editor
        uses a pandas DataFrame, which is a different format than the
        edge-based DFD we use.
        """
        # "edges" is what is returned by the data editor, and it contains the
        # changes made in the table editor. It has three keys: "edited_rows",
        # "added_rows" and "deleted_rows".
        changes = st.session_state["edges"]
        # "state" is the DFD currently stored in the session state
        state = st.session_state["input"]["dfd"]
        # Update the DFD with the changes made in the table editor
        for item in changes["edited_rows"]:
            for key in changes["edited_rows"][item]:
                state[item][key] = changes["edited_rows"][item][key]
        for added in changes["added_rows"]:
            state.append(added)
        for deleted in sorted(changes["deleted_rows"], reverse=True): # to avoid index errors, delete from the end
            state.pop(deleted)
        # Update the DFD in the session state   
        st.session_state["input"]["dfd"] = state

    st.checkbox("DFD only", value=False, key="dfd_only", help="Check this box if you only want to use a Data Flow Diagram for the threat modeling, without including the application description.")
    st.session_state["input"]["dfd_only"] = st.session_state["dfd_only"]
    st.checkbox("Include DFD in application info for threat modeling", key="use_dfd", help="Choose whether or not to include the DFD in the subsequent threat modeling process, together with the application description. Including it adds context to the LLM, but also increases token count.", disabled=st.session_state["dfd_only"])
    st.session_state["input"]["use_dfd"] = st.session_state["use_dfd"]
    col1, col2 = st.columns([0.6,0.4])
    with col1:
        col11, col12, col13 = st.columns([0.4,0.4,0.2])
        # ATTENTION: The order of the following columns is important, as the
        # OpenAI API key is needed to generate the DFD from the image
        # Thus, they are used in the order col12, col13, col11
        with col12:
            # Generate DFD from image with OpenAI API
            if st.session_state["model_provider"] == "OpenAI API":
                selected_model = "gpt-4o" # use gpt-4o for image analysis
                openai_api_key = st.session_state["keys"]["openai_api_key"]
                uploaded_image = st.file_uploader(
                    "Upload DFD image", type=["jpg", "jpeg", "png"],
                    help="Upload an image of the DFD to be analyzed by the AI model and converted to our representation.",
                )
                if uploaded_image is not None:
                    if not openai_api_key:
                        st.error("Please enter your OpenAI API key to analyse the image.")
                    else:
                        if (
                            "uploaded_image" not in st.session_state
                            or st.session_state["uploaded_image"] != uploaded_image
                        ):
                            st.session_state["uploaded_image"] = uploaded_image
                            with st.spinner("Analysing the uploaded image..."):

                                def encode_image(uploaded_image):
                                    return base64.b64encode(uploaded_image.read()).decode(
                                        "utf-8"
                                    )

                                base64_image = encode_image(uploaded_image)

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
        # Generate DFD from app description, based on the application text
        with col13:
            if st.button("Generate from app description", help="Generate a DFD graph from the application information provided in the Application info tab, using the AI model.", disabled=st.session_state["dfd_only"]):
                st.session_state["input"]["dfd"] = get_dfd(
                    st.session_state["keys"]["openai_api_key"],
                    st.session_state["openai_model"],
                    st.session_state["temperature"],
                    st.session_state["input"],
                )["dfd"]
            if st.button("Update graph", help="Update the graph with the data currently in the table."):
                update_graph()
        # Generate DFD from uploaded CSV file
        with col11:
            uploaded_file = st.file_uploader(
                "Upload DFD CSV file", 
                type=["csv"], 
                help="Upload a CSV file containing the DFD, in the format of a list of dictionaries with keys 'from', 'typefrom', 'to', 'typeto' and 'trusted', representing each edge.",
                key="dfd_file"
            )
            if uploaded_file is not None:
                try:
                    # Read the uploaded file as a CSV, transform it into a list of dictionaries and store it in the session state
                    reader = csv.DictReader(StringIO(uploaded_file.getvalue().decode("utf-8-sig")), delimiter=",")
                    dfd = list(reader)
                    st.session_state["input"]["dfd"] = dfd
                    for edge in st.session_state["input"]["dfd"]:
                        # Convert the "trusted" key to a boolean, otherwise it will be a string
                        if edge["trusted"] == "true":
                            edge["trusted"] = True
                        else:
                            edge["trusted"] = False
                    # If the user does not remove the uploaded file, the DFD will not change until they do
                    st.info("Please remove the uploaded file to modify the DFD from the table.")
                except Exception as e:
                    st.error(f"Error reading the uploaded file: {e}")
    with col2:
        # Display the DFD as a graph
        st.graphviz_chart(st.session_state["input"]["graph"])
        
        
    def format_correct(state):
        """
        This function formats the DFD in the correct format for the data
        editor. It takes the DFD in the format of a list of dictionaries and
        returns a dictionary with keys "from", "typefrom", "to", "typeto" and
        "trusted", indicating the columns of the data editor. Thus, it
        transforms the DFD from a list of dictionaries to a dictionary of
        lists, or essentially from a row-based to a column-based format.
        
        Args:
            state (list): The DFD in the format of a list of dictionaries, with
                keys "from", "typefrom", "to", "typeto" and "trusted".
        Returns:
            dict: The DFD in the format of a dictionary of lists, with keys
                "from", "typefrom", "to", "typeto" and "trusted", where each
                list represents a column of the data editor.
        """
        
        # Create a new dictionary with the correct format
        new_dict = {
            "from": [],
            "typefrom": [],
            "to": [],
            "typeto": [],
            "trusted": [],
        }
        # For each row, append the values to the corresponding list
        for object in state:
            new_dict["from"].append(object.get("from"))
            new_dict["typefrom"].append(object.get("typefrom"))
            new_dict["to"].append(object.get("to"))
            new_dict["typeto"].append(object.get("typeto"))
            new_dict["trusted"].append(object.get("trusted"))

        return new_dict
        
    # The data editor for the DFD
    edges = st.data_editor(
        data=pd.DataFrame().from_dict(format_correct(st.session_state["input"]["dfd"])),
        column_config={
            "from": st.column_config.TextColumn("From", help="The starting point of the edge.", width="medium", required=True),
            "typefrom": st.column_config.SelectboxColumn("Type", help="The type of the starting element.", width="medium", required=True, options=["Entity", "Data store", "Process"]),
            "to": st.column_config.TextColumn("To", help="The destination of the edge.", width="medium", required=True),
            "typeto": st.column_config.SelectboxColumn("Type", help="The type of the destination element.", width="medium", required=True, options=["Entity", "Data store", "Process"]),
            "trusted": st.column_config.CheckboxColumn("Trusted", help="Whether the edge stays inside the trusted boundary (true) or traverses it (false).", width="medium"),
        },
        key="edges",
        num_rows="dynamic",
        on_change=update_edges,
    )
    # Download the DFD as a dot file, which can be useful to the user
    st.download_button(
        "Download graphviz source", 
        help="Download the graphviz source code for the current DFD, to be used in PDF or PNG generation.",
        data=st.session_state["input"]["graph"].source,
        file_name="dfd.dot",
    )


def update_graph():
    """
    This function updates the graph with the data currently in the table editor,
    setting all of the customizations and attributes of the graph and recreating
    all of the nodes and edges.
    """
    st.session_state["is_graph_generated"] = True
    graph = graphviz.Digraph(engine='fdp', format='svg') # use fdp for a non-hierarchical layout
    # Set the graph attributes
    st.session_state["graph_seed"] = str(random.randint(0, 100))
    graph.attr(
        bgcolor=f"{st.get_option("theme.backgroundColor")}",
        overlap="false",
        K="2.5",
        start=st.session_state["graph_seed"],
        splines="ortho",
    )
    graph.node_attr.update(
        color=f"{st.get_option("theme.primaryColor")}",
        fontcolor="white",
        padding="0.4",
    )
    graph.edge_attr.update(
        color="white",
        fontcolor="white",
        arrowsize="0.5",
    )
    # Create the trusted cluster and add the trusted edges
    with graph.subgraph(name='cluster_0') as c:
        # Cluster attributes
        c.attr(
            color="#00a6fb",
            label="Trusted",
            fontcolor="#00a6fb",
            style="dashed"
        )
        for edge in st.session_state["input"]["dfd"]:
            if edge["trusted"]:
                c.node(edge["from"])
                c.node(edge["to"])
    # Add the edges to the graph
    for (i, object) in enumerate(st.session_state["input"]["dfd"]):
        graph.node(object["from"], shape=f"{"box" if object["typefrom"] == "Entity" else "ellipse" if object["typefrom"] == "Process" else "cylinder"}")
        graph.node(object["to"], shape=f"{"box" if object["typeto"] == "Entity" else "ellipse" if object["typeto"] == "Process" else "cylinder"}")
        graph.edge(object["from"], object["to"], taillabel=f"DF{i}", constraint="false")
        
        
    # Finally, update the graph in the session state
    st.session_state["input"]["graph"] = graph