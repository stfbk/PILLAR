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
from llms.simple import (
    get_threat_model_openai,
    get_threat_model_google,
    get_threat_model_mistral,
    threat_model_gen_markdown,
)
from llms.prompts import THREAT_MODEL_USER_PROMPT


def threat_model():

    st.markdown("""
    It is a basic zero-shot threat elicitation where the selected LLM uses the system description provided 
    and identifies threats with a focus on each of LINDDUN’s threat categories. 
    Use this tab to generate a simple threat model with the LLM, which will provide a
    list of potential threats to your application, classified by LINDDUN category.

    ---
    """)

    threat_model_submit_button = st.button(
        label="Generate Threats", 
        disabled= not st.session_state["input"]["app_description"] and not st.session_state["dfd_only"], 
        help="Generate privacy threats for the application."
    )

    model_provider = st.session_state["model_provider"]

    # If the Generate Threats button is clicked and the user has provided
    # an application description or a DFD in dfd_only mode, generate the threat
    # model
    if threat_model_submit_button and (st.session_state["input"]["app_description"] or st.session_state["dfd_only"]):
        inputs = st.session_state["input"]
        inputs["boundaries"] = st.session_state["boundaries"]
        threat_model_prompt = THREAT_MODEL_USER_PROMPT(
            inputs
        )

        with st.spinner("Analysing potential threats..."):
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Call the relevant get_threat_model function with the generated prompt
                    if model_provider == "OpenAI API":
                        model_output = get_threat_model_openai(
                            st.session_state["keys"]["openai_api_key"],
                            st.session_state["openai_model"], 
                            threat_model_prompt,
                            st.session_state["temperature"],
                        )
                    elif model_provider == "Google AI API":
                        model_output = get_threat_model_google(
                            st.session_state["keys"]["google_api_key"], 
                            st.session_state["google_model"], 
                            threat_model_prompt,
                            st.session_state["temperature"],
                        )
                    elif model_provider == "Mistral API":
                        model_output = get_threat_model_mistral(
                            st.session_state["keys"]["mistral_api_key"], 
                            st.session_state["mistral_model"], 
                            threat_model_prompt,
                            st.session_state["temperature"],
                        )
                    elif model_provider == "Local LM Studio":
                        if st.session_state["lmstudio_loaded"]:
                            model_output = get_threat_model_openai(
                                st.session_state["keys"]["openai_api_key"],
                                st.session_state["openai_model"], 
                                threat_model_prompt,
                                st.session_state["temperature"],
                                lmstudio=True,
                            )
                    elif model_provider == "Ollama":
                        if st.session_state.get("ollama_loaded"):
                            model_output = get_threat_model_openai(
                                api_key="ollama",
                                model_name=st.session_state["ollama_model"],
                                prompt=threat_model_prompt,
                                temperature=st.session_state["temperature"],
                                ollama=True
                            )
                        else:
                            raise Exception("No Ollama model loaded. Please load a model from the sidebar first.")

                    # Access the threat model from the parsed content, or set it to an empty list if not found
                    threat_model = model_output.get("threat_model", [])

                    # Save the threat model to the session state for later use.
                    st.session_state["threat_model_threats"] = threat_model
                    break  
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        st.error(
                            f"Error generating threat model after {max_retries} attempts: {e}"
                        )
                        threat_model = []
                    else:
                        st.warning(
                            f"Error generating threat model. Retrying attempt {retry_count+1}/{max_retries}..."
                        )

        # Convert the threat model JSON to Markdown
        markdown_output = threat_model_gen_markdown(threat_model)
        st.session_state["threat_model_output"] = markdown_output

    if st.session_state["threat_model_output"] != "":
        st.markdown("# Privacy Threats")
        st.markdown(st.session_state["threat_model_output"], unsafe_allow_html=True)
        st.download_button(
            label="Download",
            data=st.session_state["threat_model_output"],  
            file_name="privacy_threat_model.md",
            mime="text/markdown",
        )