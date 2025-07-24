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
import json
from llms.linddun_pro import (
    get_linddun_pro,
    linddun_pro_gen_markdown,
    get_linddun_pro_mistral,
    get_linddun_pro_google
)


def linddun_pro():

    # Check if the number of edges in the DFD has changed, and update the threats list accordingly
    if len(st.session_state["linddun_pro_threats"]) != len(st.session_state["input"]["dfd"]):
        st.session_state["linddun_pro_threats"] = [[] for _ in st.session_state["input"]["dfd"]]

    st.markdown("""
    The [LINDDUN PRO](https://linddun.org/pro/) tab allows you to model the privacy
    threats associated with your application using the LINDDUN PRO methodology.
    First, you have to provide a Data Flow Diagram in the DFD tab. Then, have two options: 1) Single Analyze: with this option, you can choose each specific edge to elicit threats 
    on that data flow. You can also choose the categories to look for. 2) Full Analyze: with this option, you can analyze all edges and categories at once.

    ---
    """)
    
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.graphviz_chart(st.session_state["input"]["graph"])
    with col2:
        st.selectbox("Select the edge to consider", 
            [i for i in range(len(st.session_state["input"]["dfd"]))],
            help="Select the Data Flow (edge of the DFD) to find threats for.",
            key="edge_num"
        )
        # Display the selected edge
        st.markdown(f'{st.session_state["input"]["dfd"][st.session_state["edge_num"]]["from"]} -> DF{st.session_state["edge_num"]} -> {st.session_state["input"]["dfd"][st.session_state["edge_num"]]["to"]}')
        st.multiselect("Select the LINDDUN threat categories to look for",
            ["Linking", "Identifying", "Non-repudiation", "Detecting", "Data disclosure", "Unawareness and unintervenability", "Non-compliance"],
            help="Select the LINDDUN threat categories to look for in the threat model.",
            key="threat_categories"
        )
        st.text_area(
            "Data flow description",
            help="Describe in detail the data flow for the selected edge.",
            key="data_flow_description",
            value=st.session_state["input"]["dfd"][st.session_state["edge_num"]]["description"],
            placeholder="Explain what is transferred between source and destination and how it is processed.",
            on_change=lambda: st.session_state["input"]["dfd"][st.session_state["edge_num"]].update({"description": st.session_state["data_flow_description"]})
        )
        print(st.session_state["data_flow_description"])
        # Create a columns layout for the buttons
        button_col1, button_col2 = st.columns([1, 1])
        
        # Different disable conditions for Single and Full Analyze
        single_analyze_disabled = (
            not st.session_state["dfd_generated"] or 
            not st.session_state["threat_categories"]  # Need both DFD and selected categories
        )
        
        full_analyze_disabled = not st.session_state["dfd_generated"]  # Only need DFD
        
        with button_col1:
            single_analyze_button = st.button(
                "Single Analyze", 
                disabled=single_analyze_disabled,
                help="Analyze threats for the selected edge and categories only. Requires selecting edge and threat categories."
            )
            
        with button_col2:
            full_analyze_button = st.button(
                "Full Analyze", 
                disabled=full_analyze_disabled,
                help="Run LINDDUN PRO analysis for all edges and all categories. Only requires a DFD."
            )

        # Handle Analyze button logic
        if single_analyze_button:
            with st.spinner("Eliciting threats in the data flow..."):
                # Get the LINDDUN Pro threats for the selected edge, for each selected category
                provider = st.session_state.get("model_provider", "OpenAI API")
                
                # Select appropriate API key and model based on provider
                if provider == "Ollama":
                    api_key = None  
                    model_name = st.session_state.get("ollama_model")
                    if not model_name:
                        st.error("Please load an Ollama model from the sidebar first.")
                        return
                elif provider == "Local LM Studio":
                    if st.session_state.get("lmstudio_loaded", False):
                        api_key = st.session_state["keys"]["openai_api_key"] 
                        model_name = st.session_state.get("lmstudio_model")  
                        if not model_name:
                            st.error("Please select and load an LM Studio model from the sidebar first.")
                            return
                    else:
                        st.error("Please load an LM Studio model from the sidebar first.")
                        return
                elif provider == "Mistral API":
                    api_key = st.session_state["keys"]["mistral_api_key"]
                    model_name = st.session_state["mistral_model"]
                elif provider == "Google AI API":
                    api_key = st.session_state["keys"]["google_api_key"]
                    model_name = st.session_state["google_model"]
                else:
                    api_key = st.session_state["keys"]["openai_api_key"]
                    model_name = st.session_state["openai_model"]
                
                for category in st.session_state["threat_categories"]:
                    # Use appropriate function based on provider
                    if provider == "Mistral API":
                        new_threat = get_linddun_pro_mistral(
                            api_key,
                            model_name,
                            st.session_state["input"]["dfd"],
                            st.session_state["input"]["dfd"][st.session_state["edge_num"]],
                            category,
                            st.session_state["boundaries"],
                            st.session_state["temperature"]
                        )
                    elif provider == "Google AI API":
                        new_threat = get_linddun_pro_google(
                            api_key,
                            model_name,
                            st.session_state["input"]["dfd"],
                            st.session_state["input"]["dfd"][st.session_state["edge_num"]],
                            category,
                            st.session_state["boundaries"],
                            st.session_state["temperature"]
                        )
                    else:  # OpenAI, Ollama, or LM Studio
                        new_threat = get_linddun_pro(
                            api_key,
                            model_name,
                            st.session_state["input"]["dfd"],
                            st.session_state["input"]["dfd"][st.session_state["edge_num"]],
                            category,
                            st.session_state["boundaries"],
                            st.session_state["temperature"],
                            provider
                        )
                    new_threat["edge"] = st.session_state["input"]["dfd"][st.session_state["edge_num"]]
                    # Check if the threat category already exists in the list of threats for the edge, and update it if it does instead of appending
                    flag = False
                    for (i, threat) in enumerate(st.session_state["linddun_pro_threats"][st.session_state["edge_num"]]):
                        if new_threat["category"] == threat["category"]:
                            flag = True
                            st.session_state["linddun_pro_threats"][st.session_state["edge_num"]][i] = new_threat
                    if not flag:
                        st.session_state["linddun_pro_threats"][st.session_state["edge_num"]].append(new_threat)



    # Display Single Analysis results
    if st.session_state["linddun_pro_threats"][st.session_state["edge_num"]]:
        st.markdown(f"### Threats found for DF_{st.session_state['edge_num']}")
        markdown = linddun_pro_gen_markdown(st.session_state["linddun_pro_threats"][st.session_state["edge_num"]])
        st.markdown(markdown, unsafe_allow_html=True)
        st.session_state["linddun_pro_output"] = markdown
    
    # Display Full Analysis results outside the columns
    if full_analyze_button:
        with st.spinner("Running LINDDUN PRO for all edges and categories..."):
            all_threats = []
            linddun_categories = [
                "Linking", "Identifying", "Non-repudiation", "Detecting", 
                "Data disclosure", "Unawareness and unintervenability", "Non-compliance"
            ]
            provider = st.session_state.get("model_provider", "OpenAI API")
            
            # Select appropriate API key and model based on provider
            if provider == "Ollama":
                api_key = None  
                model_name = st.session_state.get("ollama_model")
                if not model_name:
                    st.error("Please load an Ollama model from the sidebar first.")
                    return
            elif provider == "Local LM Studio":
                    if st.session_state.get("lmstudio_loaded", False):
                        api_key = st.session_state["keys"]["openai_api_key"]  
                        model_name = st.session_state.get("lmstudio_model")  
                        if not model_name:
                            st.error("Please select and load an LM Studio model from the sidebar first.")
                            return
                    else:
                        st.error("Please load an LM Studio model from the sidebar first.")
                        return
            elif provider == "Mistral API":
                    api_key = st.session_state["keys"]["mistral_api_key"]
                    model_name = st.session_state["mistral_model"]
            elif provider == "Google AI API":
                api_key = st.session_state["keys"]["google_api_key"]
                model_name = st.session_state["google_model"]
            else:
                api_key = st.session_state["keys"]["openai_api_key"]
                model_name = st.session_state["openai_model"]
            
            # Collect threats
            for edge_num, edge in enumerate(st.session_state["input"]["dfd"]):
                for category in linddun_categories:
                    try:
                        # Use appropriate function based on provider
                        if provider == "Mistral API":
                            threat = get_linddun_pro_mistral(
                                api_key,
                                model_name,
                                st.session_state["input"]["dfd"],
                                edge,
                                category,
                                st.session_state["boundaries"],
                                st.session_state["temperature"]
                            )
                        elif provider == "Google AI API":
                            threat = get_linddun_pro_google(
                                api_key,
                                model_name,
                                st.session_state["input"]["dfd"],
                                edge,
                                category,
                                st.session_state["boundaries"],
                                st.session_state["temperature"]
                            )
                        else:  # OpenAI, Ollama, or LM Studio
                            threat = get_linddun_pro(
                                api_key,
                                model_name,
                                st.session_state["input"]["dfd"],
                                edge,
                                category,
                                st.session_state["boundaries"],
                                st.session_state["temperature"],
                                provider
                            )
                        threat["edge"] = edge
                        threat["category"] = category
                        all_threats.append(threat)
                    except Exception as e:
                        st.warning(f"Error for edge {edge_num}, category {category}: {e}")

            # Display results outside columns
            if all_threats:
                try:
                    st.markdown("---")
                    st.markdown("## Full Analysis Results")
                    md = linddun_pro_gen_markdown(all_threats)
                    st.markdown(md, unsafe_allow_html=True)

                    # Place download buttons in two columns
                    dl_col1, dl_col2 = st.columns(2)
                    with dl_col1:
                        st.download_button(
                            label="Download as Markdown",
                            data=md,
                            file_name="linddun_pro_full_analysis.md",
                            mime="text/markdown",
                        )
                    with dl_col2:
                        json_data = json.dumps(all_threats, indent=2)
                        st.download_button(
                            label="Download as JSON",
                            data=json_data,
                            file_name="linddun_pro_full_analysis.json",
                            mime="application/json",
                        )
                except Exception as e:
                    st.error(f"Error generating results: {str(e)}")
            else:
                st.info("No threats were generated in the analysis.")