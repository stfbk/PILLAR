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
from llms.linddun_go import (
    get_linddun_go,
    get_multiagent_linddun_go,
    linddun_go_gen_markdown,
)
from tabs.sidebar import get_ollama_models
import lmstudio as lms
import requests
from llms.config import OLLAMA_CONFIG

def linddun_go():
    st.markdown("""
The [LINDDUN GO](https://linddun.org/go/) process enables teams to dynamically
apply the LINDDUN methodology to identify and assess privacy threats in a
game-like fashion. This interactive simulation guides the LLM through the steps
of the LINDDUN GO framework, asking questions about the application for each
one of the LINDDUN GO deck to elicit potential threats. The simulation can also
be carried out by a team of experts (whose role is played by the LLMs), with
each expert contributing their expertise to the threat modeling process,
carrying out a discussion between the LLMs. The final decision on the threats
is made by a judge LLM, which evaluates the opinions proposed by the experts.

---
""")
    
    provider = st.session_state.get("model_provider", "OpenAI API")
    multi_agent = st.checkbox("Use multiple LLM agents to simulate LINNDUN GO with a team of expert")

    # Model selection logic based on provider
    if provider in ["Ollama", "Local LM Studio"]:
        if multi_agent:
            if provider == "Ollama":
                available_models = get_ollama_models()
                key = "ollama_models_multi"
            else:  # LM Studio
                available_models = [model.model_key for model in lms.list_downloaded_models()]
                key = "lmstudio_models_multi"

            judge_model = st.session_state.get("ollama_model" if provider == "Ollama" else "lmstudio_model")
            if not judge_model:
                st.error("Please load a model from sidebar first - it will be used as the Judge")
                return

            # Remove judge model from available models
            agent_available_models = [m for m in available_models if m != judge_model]
            
            st.markdown("### Select models for agents:")
            st.info(f"💡 Model '{judge_model}' (loaded from sidebar) will be used as Judge")
            
            # Model selection with multiselect
            selected_models = st.multiselect(
                "Select additional models (max 3):",
                agent_available_models,
                max_selections=3,
                key=f"{key}_models"
            )
            
            # A temporary placeholder, the roles will be determined by the card's competent_agents during the debate
            agent_roles = ["Expert"] * len(selected_models)

            if selected_models:
                # Load selected models for Ollama
                if provider == "Ollama":
                    with st.spinner("Loading selected models..."):
                        for model in selected_models:
                            try:
                                response = requests.post(
                                    f"{OLLAMA_CONFIG['base_url']}/api/pull",
                                    json={"name": model}
                                )
                                if response.status_code == 200:
                                    st.session_state["ollama_loaded"] = True
                            except Exception as e:
                                st.error(f"Failed to load model {model}: {str(e)}")
                                st.stop()

                # Store agent roles in session state
                st.session_state["agent_roles"] = agent_roles
                
                # Set up models and configurations
                all_models = [judge_model] + selected_models
                llms_to_use = [provider] * len(all_models)
                
                if provider == "Ollama":
                    models_dict = {
                        "ollama_model": judge_model,
                        "ollama_models": all_models
                    }
                else:  # LM Studio
                    models_dict = {
                        "lmstudio_model": judge_model,
                        "lmstudio_models": all_models
                    }
        else:
            # Single agent case - use model from sidebar directly
            if provider == "Ollama":
                selected_models = [st.session_state.get("ollama_model")]
            else:
                selected_models = [st.session_state.get("lmstudio_model")]
            llms_to_use = [provider]
    else:
        if multi_agent:
            # Show all cloud providers as options, regardless of API key status
            available_llms = []
            
            # Always include all cloud providers
            if provider == "OpenAI API":
                # Current provider is always available
                available_llms.append("OpenAI API")
            else:
                # Check if OpenAI is configured and add it
                openai_key = st.session_state["keys"].get("openai_api_key")
                if openai_key:
                    available_llms.append("OpenAI API")
            
            if provider == "Mistral API":
                # Current provider is always available
                available_llms.append("Mistral API")
            else:
                # Check if Mistral is configured and add it
                mistral_key = st.session_state["keys"].get("mistral_api_key")
                if mistral_key:
                    available_llms.append("Mistral API")
            
            if provider == "Google AI API":
                # Current provider is always available
                available_llms.append("Google AI API")
            else:
                # Check if Google is configured and add it
                google_key = st.session_state["keys"].get("google_api_key")
                if google_key:
                    available_llms.append("Google AI API")
            
            # Always include the current provider
            if provider in ["OpenAI API", "Mistral API", "Google AI API"] and provider not in available_llms:
                available_llms.append(provider)
            
            if not available_llms:
                st.error("Please configure at least one API key in the sidebar first")
                return
            
            # Create a session state key for LLM selection if it doesn't exist
            if "selected_llms" not in st.session_state:
                st.session_state["selected_llms"] = []
            
            # Filter out any previously selected LLMs that are no longer available
            st.session_state["selected_llms"] = [
                llm for llm in st.session_state["selected_llms"] 
                if llm in available_llms
            ]
            
            # Use multiselect with cached selections
            llms_to_use = st.multiselect(
                "Select the LLMs to use (max 3, first selected will be Judge)",
                available_llms,
                default=st.session_state["selected_llms"] if st.session_state["selected_llms"] else [available_llms[0]] if available_llms else [],
                max_selections=3,
                help="Select the LLM providers to use for the multi-agent simulation.",
                key="llms_multiselect"
            )
            
            # Store the current selection for next render
            st.session_state["selected_llms"] = llms_to_use
        else:
            # Single agent case - use model from sidebar directly
            llms_to_use = [provider]

    c1, c2 = st.columns([1, 1])
    with c1:
        threats_to_analyze = st.slider("Number of cards to analyze", 1, st.session_state["max_threats"], 3)
        rounds = st.slider("Number of rounds", 1, 5, 3, disabled=not multi_agent)
        
    with c2:
        # Check if judge model is loaded
        judge_loaded = False
        if provider == "Ollama":
            judge_loaded = st.session_state.get("ollama_model") is not None
        elif provider == "Local LM Studio":
            judge_loaded = st.session_state.get("lmstudio_model") is not None
        else:
            judge_loaded = True  # For other providers, no explicit loading needed

        button_disabled = (
            not st.session_state["input"]["app_description"] and 
            not st.session_state["dfd_only"]
        ) or (not judge_loaded)

        if not judge_loaded and (provider in ["Ollama", "Local LM Studio"]):
            st.error("Please load a model from sidebar first - it will be used as the Judge agent.")

        linddun_go_submit_button = st.button(
            label="Simulate LINDDUN GO", 
            help="Simulate the LINDDUN GO process to identify privacy threats.", 
            disabled=button_disabled
        )


    if linddun_go_submit_button: 
        inputs = st.session_state["input"]
        inputs["boundaries"] = st.session_state["boundaries"]
        threats = []
        
        with st.spinner("Answering questions..."):
            try:
                # Check judge model before proceeding
                if provider == "Ollama":
                    if not st.session_state.get("ollama_model"):
                        raise Exception("No judge model loaded from sidebar. Please load an Ollama model first.")
                elif provider == "Local LM Studio":
                    if not st.session_state.get("lmstudio_model"):
                        raise Exception("No judge model loaded from sidebar. Please load a LM Studio model first.")

                if multi_agent:
                    if not llms_to_use:
                        raise ValueError("Please select at least one LLM to use.")
                    
                    # Set up models dictionary based on provider
                    if provider == "Ollama":
                        models_dict = {
                            "ollama_model": judge_model,  # Judge model from sidebar
                            "ollama_models": all_models     # All models including judge
                        }
                    elif provider == "Local LM Studio":
                        models_dict = {
                            "lmstudio_model": selected_models[0],  # First model for Judge
                            "lmstudio_models": selected_models     # All models for agents
                        }
                    else:
                        models_dict = {
                            "openai_model": st.session_state.get("openai_model"),
                            "mistral_model": st.session_state.get("mistral_model"),
                            "google_model": st.session_state.get("google_model")
                        }

                    threats = get_multiagent_linddun_go(
                        st.session_state["keys"],
                        models_dict,
                        inputs,
                        st.session_state["temperature"],
                        rounds,
                        threats_to_analyze,
                        llms_to_use,
                        lmstudio=(provider == "Local LM Studio"),
                        ollama=(provider == "Ollama")
                    )
                else:
                    # Single agent case
                    if provider == "Ollama":
                        threats = get_linddun_go(
                            None,  
                            selected_models[0] if selected_models else st.session_state["ollama_model"],
                            inputs,
                            threats_to_analyze,
                            st.session_state["temperature"],
                            provider="Ollama"  
                        )
                    elif provider == "Local LM Studio":
                        threats = get_linddun_go(
                            None,  
                            st.session_state["lmstudio_model"],
                            inputs,
                            threats_to_analyze,
                            st.session_state["temperature"],
                            provider="Local LM Studio"
                        )
                    elif provider == "Google AI API":
                        google_api_key = st.session_state["keys"].get("google_api_key")
                        if not google_api_key:
                            raise Exception("Google API key is not configured. Please set your Google API key in the sidebar.")
                        
                        google_model = st.session_state.get("google_model")
                        if not google_model:
                            raise Exception("Google model is not selected. Please select a model in the sidebar.")
                        
                        threats = get_linddun_go(
                            google_api_key,
                            google_model,
                            inputs,
                            threats_to_analyze,
                            st.session_state["temperature"],
                            provider="Google AI API"
                        )
                    elif provider == "Mistral API":
                        threats = get_linddun_go(
                            st.session_state["keys"]["mistral_api_key"],
                            st.session_state["mistral_model"],
                            inputs,
                            threats_to_analyze,
                            st.session_state["temperature"],
                            provider="Mistral API"
                        )
                    else:
                        threats = get_linddun_go(
                            st.session_state["keys"]["openai_api_key"],
                            st.session_state["openai_model"],
                            inputs,
                            threats_to_analyze,
                            st.session_state["temperature"],
                            provider="OpenAI API"
                        )

            except Exception as e:
                st.error(f"Error generating simulation: {e}")
                return

        # Convert the threat model JSON to Markdown
        markdown_output = linddun_go_gen_markdown(threats)
        st.session_state["linddun_go_output"] = markdown_output
        st.session_state["linddun_go_threats"] = threats



    if st.session_state["linddun_go_output"] != "":
        st.markdown("# LINDDUN GO Simulation Result")
        st.markdown(st.session_state["linddun_go_output"], unsafe_allow_html=True)
        st.download_button(
            label="Download Output",
            data=st.session_state["linddun_go_output"],  
            file_name="linddun_go_output.md",
            mime="text/markdown",
        )

