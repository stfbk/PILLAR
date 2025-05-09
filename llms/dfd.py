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
import json
import requests
from openai import OpenAI
from llms.prompts import (
    DFD_USER_PROMPT,
    DFD_SYSTEM_PROMPT,
    DFD_IMAGE_SYSTEM_PROMPT,
)
import streamlit as st
import graphviz

def get_dfd(api_key, model, temperature, inputs):
    """
    Generate DFD from application description.
    Returns a dictionary with 'dfd' edges and 'boundaries' definitions.
    """
    # Create a progress indicator
    progress_placeholder = st.empty()
    progress_placeholder.info("Analyzing application description...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Enhanced system prompt with clearer instructions for dynamic boundaries
    
        messages=[
            {"role": "system", "content": DFD_SYSTEM_PROMPT},
            {"role": "user", "content": DFD_USER_PROMPT(inputs)}
        ]

        progress_placeholder.info("Generating DFD with AI model...")
        
        # Use response_format to ensure we get JSON
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4096,
            temperature=temperature,
        )
        
        # Parse the response content
        content = response.choices[0].message.content
        print(f"Raw LLM response: {content}")
        
        try:
            result = json.loads(content)
            
            # Process boundaries if they exist in the response
            if "boundaries" in result and isinstance(result["boundaries"], list):
                boundaries = result["boundaries"]
                
                # Validate each boundary has required fields
                valid_boundaries = []
                for boundary in boundaries:
                    if all(k in boundary for k in ["id", "name", "description", "color"]):
                        valid_boundaries.append(boundary)
                
                if valid_boundaries:
                    # Update session state with the new boundaries
                    st.session_state["boundaries"] = valid_boundaries
                    print(f"Generated {len(valid_boundaries)} boundaries")
            
            # Check if we have a 'dfd' key with a list of edges
            if "dfd" in result and isinstance(result["dfd"], list):
                dfd_edges = result["dfd"]
                
                # Validate and clean up each edge
                valid_edges = []
                for edge in dfd_edges:
                    # Ensure all required fields are present
                    if all(k in edge for k in ["from", "typefrom", "to", "typeto"]):
                        # Set defaults for optional fields
                        if "trusted" not in edge:
                            edge["trusted"] = True
                        
                        # If boundary is missing, try to infer it or use default
                        if "boundary" not in edge:
                            # Default to first boundary or create one if none exist
                            if "boundaries" in st.session_state and st.session_state["boundaries"]:
                                edge["boundary"] = st.session_state["boundaries"][0]["id"]
                            else:
                                edge["boundary"] = "boundary_1"
                        
                        # Ensure trusted is a boolean
                        if isinstance(edge["trusted"], str):
                            edge["trusted"] = edge["trusted"].lower() == "true"
                            
                        valid_edges.append(edge)
                
                if valid_edges:
                    # Ensure consistent boundary assignment for components
                    component_boundaries = {}
                    for edge in valid_edges:
                        from_component = edge["from"]
                        to_component = edge["to"]
                        
                        # Check and set boundary for source component
                        if from_component in component_boundaries:
                            # Use previously assigned boundary
                            edge["boundary"] = component_boundaries[from_component]
                        else:
                            # Record this component's boundary
                            component_boundaries[from_component] = edge["boundary"]
                        
                        # For destination, we need to check if it already has a boundary
                        if to_component in component_boundaries:
                            # If destination already has a boundary and it's different from the edge boundary,
                            # we need to update the trusted flag
                            if component_boundaries[to_component] != edge["boundary"]:
                                edge["trusted"] = False
                        else:
                            # If this is the first time we're seeing this component, assign it to the same boundary
                            # unless the edge is marked as untrusted
                            if edge.get("trusted", True):
                                component_boundaries[to_component] = edge["boundary"]
                            else:
                                # For untrusted edges, we need to assign a different boundary
                                # Find or create a suitable boundary
                                for boundary in st.session_state["boundaries"]:
                                    if boundary["id"] != edge["boundary"]:
                                        component_boundaries[to_component] = boundary["id"]
                                        break
                                else:
                                    # If no other boundary exists, create a new one
                                    new_boundary_id = f"boundary_{len(st.session_state['boundaries']) + 1}"
                                    st.session_state["boundaries"].append({
                                        "id": new_boundary_id,
                                        "name": f"Boundary {len(st.session_state['boundaries']) + 1}",
                                        "description": "Auto-generated boundary",
                                        "color": "#ff7f50"  # Default color
                                    })
                                    component_boundaries[to_component] = new_boundary_id
                    
                    progress_placeholder.success(f"DFD generated successfully with {len(valid_edges)} connections across {len(st.session_state.get('boundaries', []))} boundaries!")
                    return {"dfd": valid_edges, "boundaries": st.session_state.get("boundaries", [])}
                else:
                    progress_placeholder.warning("No valid DFD edges found in the response.")
            else:
                progress_placeholder.warning("Response did not contain a valid 'dfd' list.")
            print(f"Invalid response structure: {result}")
        except json.JSONDecodeError as e:
            progress_placeholder.error(f"Failed to parse JSON response: {str(e)}")
            print(f"JSON parse error: {str(e)}")
            print(f"Content: {content}")
            
        # Return a default DFD if we couldn't generate one
        default_boundaries = [
            {
                "id": "boundary_1",
                "name": "Internal Network",
                "description": "Corporate internal network",
                "color": "#00a6fb"
            }
        ]
        
        # Only set default boundaries if none exist
        if "boundaries" not in st.session_state or not st.session_state["boundaries"]:
            st.session_state["boundaries"] = default_boundaries
            
        return {
            "dfd": [{"from": "User", "typefrom": "Entity", "to": "System", "typeto": "Process", "trusted": True, "boundary": "boundary_1", "description": ""}],
            "boundaries": st.session_state["boundaries"]
        }
        
    except Exception as e:
        error_msg = f"Error generating DFD: {str(e)}"
        print(error_msg)
        progress_placeholder.error(error_msg)
        
        # Return a default DFD in case of error
        default_boundaries = [
            {
                "id": "boundary_1",
                "name": "Internal Network",
                "description": "Corporate internal network",
                "color": "#00a6fb"
            }
        ]
        
        # Only set default boundaries if none exist
        if "boundaries" not in st.session_state or not st.session_state["boundaries"]:
            st.session_state["boundaries"] = default_boundaries
            
        return {
            "dfd": [{"from": "User", "typefrom": "Entity", "to": "System", "typeto": "Process", "trusted": True, "boundary": "boundary_1", "description": ""}],
            "boundaries": st.session_state["boundaries"]
        }

def get_image_analysis(api_key, model_name, base64_image):
    """
    Generate DFD structure from an uploaded image.
    """
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}


    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": DFD_IMAGE_SYSTEM_PROMPT},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ]

    payload = {
        "model": model_name,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "max_tokens": 4096
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        if result and "choices" in result:
            try:
                content = json.loads(result["choices"][0]["message"]["content"])
                print("Image analysis result:", content)
                
                # Check if we have a direct DFD list in the result
                if "dfd" in content and isinstance(content["dfd"], list):
                    # Validate and clean up each edge
                    valid_edges = []
                    for edge in content["dfd"]:
                        # Ensure all required fields are present
                        if all(k in edge for k in ["from", "typefrom", "to", "typeto"]):
                            # Set defaults for optional fields
                            if "trusted" not in edge:
                                edge["trusted"] = True
                            if "boundary" not in edge:
                                edge["boundary"] = "boundary_1"
                            
                            # Ensure trusted is a boolean
                            if isinstance(edge["trusted"], str):
                                edge["trusted"] = edge["trusted"].lower() == "true"
                                
                            valid_edges.append(edge)
                    
                    if valid_edges:
                        st.session_state["input"]["dfd"] = valid_edges
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from image analysis: {e}")
                print(f"Raw content: {result['choices'][0]['message']['content']}")
        
        return result
    except Exception as err:
        print(f"Error occurred: {err}")
        print(f"Response content: {getattr(err, 'response', {}).get('content', 'No content')}")
        return None

def get_node_shape(component_type):
    """Returns the appropriate node shape based on component type."""
    if component_type == "Process":
        return "ellipse"
    elif component_type == "Entity":
        return "rectangle"
    elif component_type == "Data store":
        return "cylinder"
    return "rectangle"  # default shape

def update_graph():
    """Updates the DFD visualization with color-coded arrows for trust boundaries."""
    if "input" not in st.session_state or "dfd" not in st.session_state["input"]:
        print("No DFD data found in session state")
        return
    
    try:
        print(f"Updating graph with {len(st.session_state['input']['dfd'])} edges")
        
        # Create a new graph
        graph = graphviz.Digraph(engine='dot', format='svg')
        graph.attr(
            bgcolor='transparent',
            overlap="false",
            splines="ortho",
            rankdir="TB",
            concentrate="false",  # Keep this false to prevent edge concentration
            fontname="Arial",
            pad="0.5"
        )
        
        # Get boundaries from session state
        boundaries = st.session_state.get("boundaries", [
            {
                "id": "boundary_1",
                "name": "Internal Network",
                "color": "#00a6fb",
                "description": "Corporate internal network"
            }
        ])
        
        print(f"Processing {len(boundaries)} boundaries")
        
        # First, organize components by boundary
        boundary_components = {}
        for boundary in boundaries:
            boundary_components[boundary["id"]] = set()
        
        # Map to track component types and their boundaries
        component_types = {}
        component_boundaries = {}
        
        # Collect all components and their types
        for edge in st.session_state["input"]["dfd"]:
            from_component = edge["from"]
            to_component = edge["to"]
            from_type = edge["typefrom"]
            to_type = edge["typeto"]
            
            # Record component types - ensure we record BOTH from and to types
            component_types[from_component] = from_type
            component_types[to_component] = to_type
            
            # Record component boundaries
            if from_component not in component_boundaries:
                component_boundaries[from_component] = edge["boundary"]
            
            # For destination, we need to determine its boundary
            # First check if it's already assigned to a boundary
            if to_component not in component_boundaries:
                # Look for this component as source in other edges
                for other_edge in st.session_state["input"]["dfd"]:
                    if other_edge["from"] == to_component:
                        component_boundaries[to_component] = other_edge.get("boundary", "boundary_1")
                        break
                else:
                    # If not found as source, assign to the same boundary as the source of this edge
                    component_boundaries[to_component] = edge["boundary"]
            
            # Add components to their boundaries
            if edge["boundary"] in boundary_components:
                boundary_components[edge["boundary"]].add(from_component)
            
            to_boundary = component_boundaries[to_component]
            if to_boundary in boundary_components:
                boundary_components[to_boundary].add(to_component)
        
        # Create subgraphs for each boundary with its components
        for boundary in boundaries:
            boundary_id = boundary["id"]
            components = boundary_components.get(boundary_id, set())
            
            if not components:
                print(f"Boundary {boundary_id} has no components, skipping")
                continue
                
            print(f"Creating subgraph for boundary {boundary_id} with {len(components)} components")
            
            with graph.subgraph(name=f'cluster_{boundary_id}') as c:
                c.attr(
                    label=boundary["name"],
                    style="dashed",
                    color=boundary["color"],
                    fontcolor=boundary["color"],
                    penwidth="2.0"
                )
                
                # Add all components that belong to this boundary
                for component in components:
                    component_type = component_types.get(component)
                    if component_type:
                        shape = get_node_shape(component_type)
                        node_color = "#555555"  # Default node color
                        
                        # Use different colors based on component type
                        if component_type == "Entity":
                            fillcolor = "#e1f5fe"  # Light blue for entities
                        elif component_type == "Process":
                            fillcolor = "#e8f5e9"  # Light green for processes
                        elif component_type == "Data store":
                            fillcolor = "#fff3e0"  # Light orange for data stores
                        else:
                            fillcolor = "#f5f5f5"  # Default light gray
                        
                        c.node(
                            component, 
                            shape=shape, 
                            style="filled",
                            fillcolor=fillcolor,
                            color=node_color,
                            fontcolor="#333333",
                            fontsize="12",
                            height="0.6",
                            width="1.2"
                        )
        
        # Track parallel edges between the same nodes
        edge_counts = {}
        
        # Add all edges with color coding based on trusted value
        for i, edge in enumerate(st.session_state["input"]["dfd"]):
            from_component = edge["from"]
            to_component = edge["to"]
            
            # Get the trusted value directly from the edge
            is_trusted = edge.get("trusted", True)
            
            # Set edge styling based on trusted value
            if not is_trusted:
                # Red, dashed arrows for untrusted connections
                edge_color = "#ff0000"  # Red
                edge_style = "dashed"
                edge_penwidth = "1.5"
            else:
                # White, solid arrows for trusted connections
                edge_color = "#FFFFFF"  # White
                edge_style = "solid"
                edge_penwidth = "1.0"
            
            # Create a unique key for this edge pair
            edge_key = (from_component, to_component)
            
            # Count parallel edges and adjust positioning
            if edge_key in edge_counts:
                edge_counts[edge_key] += 1
                # Adjust the edge position for parallel edges
                pos_attr = f"pos_{edge_counts[edge_key]}"
            else:
                edge_counts[edge_key] = 0
                pos_attr = ""
            
            df_label = f"DF_{i}"
            
            
            # Add the edge with appropriate styling and a unique constraint
            graph.edge(
                from_component,
                to_component,
                label=df_label,
                style=edge_style,
                color=edge_color,
                penwidth=edge_penwidth,
                fontcolor=edge_color,
                fontsize="10",
                arrowsize="0.8",
                constraint="true",  # Ensure edge is drawn
                # Add slight curve for parallel edges
                pos=pos_attr,
                # Add a unique ID to prevent merging
                key=f"edge_{i}"
            )
        
        # Store the graph in session state
        st.session_state["input"]["graph"] = graph
        print("Graph updated successfully")
        return graph
        
    except Exception as e:
        print(f"Error updating graph: {str(e)}")
        import traceback
        traceback.print_exc()
