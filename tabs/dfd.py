# Copyright 2024 Fondazione Bruno Kessler
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import streamlit as st
import graphviz
import csv
import pandas as pd
import base64
import json
from io import StringIO
from llms.dfd import (
    get_dfd,
    get_image_analysis,
    update_graph,
)

# Default boundaries
DEFAULT_BOUNDARIES = [
    {
        "id": "boundary_1",
        "name": " Boundary 1",
        "color": "#00a6fb",
        "description": "description"
    },
    {
        "id": "boundary_2",
        "name": "Boundary 2",
        "color": "#701796",
        "description": "description"
    },
    {
        "id": "boundary_3",
        "name": "Boundary 3",
        "color": "#9c5b28",
        "description": "description"
    },
    {
        "id": "boundary_4",
        "name": "Boundary 4",
        "color": "#ad2a95",
        "description": "description"
    }
]

def synchronize_boundaries_from_csv(dfd_list):
    """
    Synchronize trust boundaries from CSV DFD data.
    - Extracts all unique boundary IDs from the DFD data.
    - Preserves existing boundaries from session state.
    - Adds any missing boundaries with default IDs, names, descriptions, and colors.
    - Updates st.session_state["boundaries"] with the new list.
    """
    try:
        # Retrieve current boundaries from session state (or default if not set)
        current_boundaries = st.session_state.get("boundaries", DEFAULT_BOUNDARIES.copy())
        # Build a dictionary for quick lookup using boundary ID as key
        boundary_dict = {b["id"]: b for b in current_boundaries}

        # Extract unique boundary IDs from the CSV DFD data
        csv_boundaries = set()
        for edge in dfd_list:
            if "boundary" in edge and edge["boundary"]:
                csv_boundaries.add(edge["boundary"])

        # For each boundary ID found in CSV, add it if missing
        for b_id in csv_boundaries:
            if b_id not in boundary_dict:
                # Generate a new boundary object with default values.
                new_boundary = {
                    "id": b_id,
                    "name": f"Boundary {b_id.replace('boundary_','')}",
                    "description": "description",
                    "color": "#ff7f50"  
                }
                current_boundaries.append(new_boundary)
                boundary_dict[b_id] = new_boundary
                # st.write(f"Added new boundary: {new_boundary}")  

        st.session_state["boundaries"] = current_boundaries
        print(f"Boundary synchronization complete. Total boundaries: {len(current_boundaries)}")
    except Exception as e:
        st.error(f"Error synchronizing boundaries: {str(e)}")
        print(f"Error synchronizing boundaries: {str(e)}")

def validate_dfd(dfd_data):
    """
    Validate the DFD data and return a list of issues.
    """
    issues = []
    if not dfd_data:
        return ["No DFD data available."]
    components = set()
    for edge in dfd_data:
        components.add(edge["from"])
        components.add(edge["to"])
    incoming = {comp: 0 for comp in components}
    outgoing = {comp: 0 for comp in components}
    for edge in dfd_data:
        outgoing[edge["from"]] += 1
        incoming[edge["to"]] += 1
    data_stores = set()
    processes = set()
    entities = set()
    for edge in dfd_data:
        if edge["typefrom"] == "Data store":
            data_stores.add(edge["from"])
        elif edge["typefrom"] == "Process":
            processes.add(edge["from"])
        elif edge["typefrom"] == "Entity":
            entities.add(edge["from"])
        if edge["typeto"] == "Data store":
            data_stores.add(edge["to"])
        elif edge["typeto"] == "Process":
            processes.add(edge["to"])
        elif edge["typeto"] == "Entity":
            entities.add(edge["to"])
    for ds in data_stores:
        if incoming[ds] < 1:
            issues.append(f"Data store '{ds}' has no incoming connections")
        if outgoing[ds] < 1:
            issues.append(f"Data store '{ds}' has no outgoing connections")
    for proc in processes:
        if incoming[proc] < 1:
            issues.append(f"Process '{proc}' has no incoming connections")
        if outgoing[proc] < 1:
            issues.append(f"Process '{proc}' has no outgoing connections")
    for edge in dfd_data:
        if edge["typefrom"] == "Entity" and edge["typeto"] == "Data store":
            issues.append(f"Invalid connection: Entity '{edge['from']}' directly connects to Data store '{edge['to']}'")
        if edge["typefrom"] == "Data store" and edge["typeto"] == "Entity":
            issues.append(f"Invalid connection: Data store '{edge['from']}' directly connects to Entity '{edge['to']}'")
    return issues

def dfd():
    st.markdown("""
    In this tab, you can create a Data Flow Diagram (DFD) to visualize the flow of
    data within your application. 
    You have multiple options to generate your DFD:
    - **Automatic Generation:** Generate a DFD based on your application description.
    - **Image Upload:** Extract a DFD from an uploaded image.
    - **CSV Import:** Load a saved DFD from a CSV file.
    
    Once generated, you can edit the DFD interactively using the table editor, update the trust boundaries, 
    and download your diagram for later use. Note, if you want to have a new trust boundary, you need to add it 
    in the "Manage Trust Boundaries" section, pressing the "Update Boundaries" button.
    The DFD is represented as a list of dictionaries with keys 'from', 'typefrom', 'to',
    'typeto' and 'trusted', representing each edge. The 'trusted' key is a boolean
    value representing whether the edge stays inside the trusted boundary or traverses it. 


    ---    
    """)

    # Initialize session state with default values if not present
    if "input" not in st.session_state:
        st.session_state["input"] = {}
    if "dfd" not in st.session_state["input"]:
        st.session_state["input"]["dfd"] = [{
            "from": "User",
            "typefrom": "Entity",
            "to": "System",
            "typeto": "Process",
            "trusted": True,
            "boundary": "boundary_1",
            "description": ""
        }]
    if "boundaries" not in st.session_state:
        st.session_state["boundaries"] = DEFAULT_BOUNDARIES.copy()
    if "graph" not in st.session_state["input"]:
        update_graph()
    if "dfd_generated" not in st.session_state:
        # Flag to track whether a DFD has been generated
        st.session_state["dfd_generated"] = False

    print("Current DFD data:", st.session_state["input"]["dfd"])

    # ------------------------------------
    # Threat Modeling Options
    # ------------------------------------
    with st.expander("Threat Modeling Options", expanded=True):
        st.checkbox("DFD only", value=False, key="dfd_only",
                    help="Check this box if you only want to use a Data Flow Diagram for the threat modeling, without including the application description.")
        st.session_state["input"]["dfd_only"] = st.session_state["dfd_only"]

        st.checkbox("Include DFD in threat modeling", key="use_dfd",
                    help="Include the DFD in the subsequent threat modeling process.",
                    disabled=st.session_state["dfd_only"])
        st.session_state["input"]["use_dfd"] = st.session_state["use_dfd"]

    # ------------------------------------
    # DFD Generation Options 
    # ------------------------------------
    with st.expander("Generate Data Flow Diagram", expanded=True):
        # Generate DFD from Application Description
        if st.button("Generate DFD from Application Description", 
                     help="Generate a DFD based on the application information provided.",
                     disabled=st.session_state["dfd_only"]):
            with st.spinner("Generating DFD..."):
                result = get_dfd(
                    st.session_state["keys"]["openai_api_key"],
                    st.session_state["openai_model"],
                    st.session_state["temperature"],
                    st.session_state["input"],
                )
                if result and "dfd" in result:
                    st.session_state["input"]["dfd"] = result["dfd"]
                    update_graph()
                    st.session_state["dfd_generated"] = True
                    st.success(f"DFD generated successfully with {len(result['dfd'])} connections!")
                    st.rerun()
                else:
                    st.error("Failed to generate DFD. Please check your application description and try again.")
        
        # Generate DFD from Image 
        if st.session_state["model_provider"] == "OpenAI API":
            # st.subheader("Upload a DFD Image")
            selected_model = "gpt-4o"  
            openai_api_key = st.session_state["keys"]["openai_api_key"]
            uploaded_image = st.file_uploader(
                "Upload DFD image", type=["jpg", "jpeg", "png"],
                help="Upload an image of a DFD to be analyzed by the AI model.",
            )
            if uploaded_image is not None:
                if not openai_api_key:
                    st.error("Please enter your OpenAI API key to analyze the image.")
                else:
                    if ("uploaded_image" not in st.session_state or 
                        st.session_state["uploaded_image"] != uploaded_image):
                        st.session_state["uploaded_image"] = uploaded_image
                        with st.spinner("Analyzing the uploaded image..."):
                            def encode_image(uploaded_image):
                                return base64.b64encode(uploaded_image.read()).decode("utf-8")
                            base64_image = encode_image(uploaded_image)
                            try:
                                image_analysis_output = get_image_analysis(
                                    openai_api_key,
                                    selected_model,
                                    base64_image,
                                )
                                if (image_analysis_output and 
                                    "choices" in image_analysis_output and 
                                    image_analysis_output["choices"][0]["message"]["content"]):
                                    
                                    image_analysis_content = image_analysis_output["choices"][0]["message"]["content"]
                                    st.session_state["image_analysis_content"] = image_analysis_content
                                    try:
                                        content_json = json.loads(image_analysis_content)
                                        if "dfd" in content_json and isinstance(content_json["dfd"], list):
                                            st.session_state["input"]["dfd"] = content_json["dfd"]
                                            update_graph()
                                            st.session_state["dfd_generated"] = True
                                            st.success(f"DFD extracted from image with {len(content_json['dfd'])} connections!")
                                            # st.rerun()
                                        else:
                                            st.error("The image analysis did not return a valid DFD structure.")
                                    except json.JSONDecodeError:
                                        st.error("Failed to parse the image analysis result.")
                                else:
                                    st.error("Failed to analyze the image. Please check the API key and try again.")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
        
        # CSV Upload Option
        # st.subheader("Or Upload a CSV File")
        uploaded_file = st.file_uploader(
            "Upload DFD CSV file", 
            type=["csv"], 
            help="Upload a CSV file containing the DFD data.",
            key="dfd_file"
        )
        if uploaded_file is not None:
            try:
                reader = csv.DictReader(StringIO(uploaded_file.getvalue().decode("utf-8-sig")), delimiter=",")
                dfd_list = list(reader)
                for edge in dfd_list:
                    if "trusted" in edge:
                        edge["trusted"] = edge["trusted"].lower() == "true"
                # Synchronize boundaries from CSV data before updating the graph
                synchronize_boundaries_from_csv(dfd_list)
                st.session_state["input"]["dfd"] = dfd_list
                update_graph()
                st.session_state["dfd_generated"] = True
                st.success(f"DFD loaded from CSV with {len(dfd_list)} connections!")
                # st.rerun()
            except Exception as e:
                st.error(f"Error reading the uploaded file: {e}")

    
    # -----------------------------------------------------------------
    # Display DFD Visualization and Edit Table 
    # -----------------------------------------------------------------
    if st.session_state.get("dfd_generated", False):
        # Two-column layout: left for editing table, right for visualization
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Edit Data Flow Diagram")
            st.info(f"Current DFD has {len(st.session_state['input']['dfd'])} connections")
            
            dfd_df = pd.DataFrame(st.session_state["input"]["dfd"]).copy()
            # Ensure required columns exist
            required_columns = ["from", "typefrom", "to", "typeto", "trusted", "boundary"]
            for col in required_columns:
                if col not in dfd_df.columns:
                    if col == "trusted":
                        dfd_df[col] = True
                    elif col == "boundary":
                        dfd_df[col] = "boundary_1"
                    else:
                        dfd_df[col] = ""
            
            edited_df = st.data_editor(
                dfd_df,
                column_config={
                    "from": st.column_config.TextColumn(
                        "From",
                        help="The source of the connection.",
                        required=True
                    ),
                    "typefrom": st.column_config.SelectboxColumn(
                        "Type From",
                        help="The type of the source element.",
                        required=True,
                        options=["Entity", "Data store", "Process"]
                    ),
                    "to": st.column_config.TextColumn(
                        "To",
                        help="The destination of the connection.",
                        required=True
                    ),
                    "typeto": st.column_config.SelectboxColumn(
                        "Type To",
                        help="The type of the destination element.",
                        required=True,
                        options=["Entity", "Data store", "Process"]
                    ),
                    "trusted": st.column_config.CheckboxColumn(
                        "Trusted",
                        help="Whether the connection stays inside the trusted boundary.",
                        required=True,
                        default=True
                    ),
                    "boundary": st.column_config.SelectboxColumn(
                        "Boundary",
                        help="The trust boundary this connection belongs to",
                        required=True,
                        options=[b["id"] for b in st.session_state["boundaries"]]
                    ),
                    "description": st.column_config.TextColumn(
                        "Description",
                        help="Description of the data flow, to use in LINDDUN Pro",
                        required=False,
                        width="small"
                    ),
                },
                key="dfd_editor",
                num_rows="dynamic",
                hide_index=True
            )
        
        with col_right:
            st.subheader("DFD Visualization")
            graph_placeholder = st.empty()  # Create a placeholder for the graph
            graph_placeholder.graphviz_chart(st.session_state["input"]["graph"])
        
        # Graph Functions 
        # ------------------------------------
        with st.expander("Graph Functions", expanded=False):
            if st.button("Save Changes and Update Graph"):
                # Save the edited table to session state
                st.session_state["input"]["dfd"] = edited_df.to_dict('records')
                # Update the graph (make sure update_graph() returns the new graph if needed)
                new_graph = update_graph()
                st.session_state["input"]["graph"] = new_graph
                st.success("Changes saved and graph updated!")
                # Update the graph placeholder with the new graph so it refreshes
                graph_placeholder.empty()  # Clear previous content
                graph_placeholder.graphviz_chart(new_graph)
                
            if st.session_state["input"]["dfd"]:
                csv_data = pd.DataFrame(st.session_state["input"]["dfd"]).to_csv(index=False)
                csv_data = csv_data.replace("True", "true").replace("False", "false")
                st.download_button(
                    "Download DFD as CSV",
                    data=csv_data,
                    file_name="dfd_data.csv",
                    mime="text/csv",
                    help="Download the current DFD data as a CSV file."
                )
            if "graph" in st.session_state["input"]:
                st.download_button(
                    "Download Graphviz Source",
                    data=st.session_state["input"]["graph"].source,
                    file_name="dfd.dot",
                    help="Download the Graphviz source code for the current DFD."
                )
        
        # Manage Trust Boundaries
        # ------------------------------------
        with st.expander("Manage Trust Boundaries", expanded=False):
            st.write("Define trust boundaries for your DFD:")
            boundaries_df = pd.DataFrame(st.session_state["boundaries"])
            edited_boundaries = st.data_editor(
                boundaries_df,
                column_config={
                    "id": st.column_config.TextColumn(
                        "ID",
                        help="Unique identifier for the boundary",
                        required=True
                    ),
                    "name": st.column_config.TextColumn(
                        "Name",
                        help="Descriptive name for the boundary",
                        required=True
                    ),
                    "description": st.column_config.TextColumn(
                        "Description",
                        help="Description of the boundary's purpose",
                        required=True
                    ),
                    "color": st.column_config.TextColumn(
                        "Color",
                        help="Color for the boundary (hex code)",
                        required=True
                    ),
                },
                key="boundary_editor",
                num_rows="dynamic",
                hide_index=True
            )
            if st.button("Update Boundaries"):
                try:
                    new_boundaries = edited_boundaries.to_dict('records')
                    valid = True
                    for b in new_boundaries:
                        if not all(k in b and b[k] for k in ["id", "name", "color", "description"]):
                            valid = False
                            st.error("All boundary fields are required")
                            break
                    if valid:
                        st.session_state["boundaries"] = new_boundaries
                        update_graph()
                        st.success("Boundaries updated!")
                except Exception as e:
                    st.error(f"Error updating boundaries: {str(e)}")
        
        # DFD Validation Issues  
        # ------------------------------------
        issues = validate_dfd(st.session_state["input"]["dfd"])
        if issues:
            with st.expander("DFD Validation Issues", expanded=True):
                st.warning("The following issues were found in your DFD:")
                for issue in issues:
                    st.markdown(f"- {issue}")
                st.markdown("These issues may lead to an incomplete threat model. Consider addressing them for a more accurate analysis.")

