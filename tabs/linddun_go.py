# Copyright 2024 [name of copyright owner]
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


def linddun_go():

    st.markdown("""
The [LINDDUN Go](https://linddun.org/go/) process enables teams to dynamically
apply the LINDDUN methodology to identify and assess privacy threats in a
game-like fashion. This interactive simulation guides the LLM through the steps
of the LINDDUN Go framework, asking questions about the application for each
one of the LINDDUN Go deck to elicit potential threats. The simulation can also
be carried out by a team of experts (whose role is played by the LLMs), with
each expert contributing their expertise to the threat modeling process,
carrying out a discussion between the LLMs. The final decision on the threats
is made by a judge LLM, which evaluates the opinions proposed by the experts.

---
""")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        threats_to_analyze = st.slider("Number of cards to analyze", 1, st.session_state["max_threats"], 3)
        multiagent_linddun_go = st.checkbox("Use multiple LLM agents to simulate LINDDUN Go with a team of experts")
        rounds = st.slider("Number of rounds", 1, 5, 3, disabled=not multiagent_linddun_go)
        
        # Add the available LLMs to the multiagent simulation
        available_llms = []
        if st.session_state["keys"]["openai_api_key"] and st.session_state["openai_model"]:
            available_llms.append("OpenAI API")
        if st.session_state["keys"]["mistral_api_key"] and st.session_state["mistral_model"]:
            available_llms.append("Mistral API")
        if st.session_state["keys"]["google_api_key"] and st.session_state["google_model"]:
            available_llms.append("Google AI API")
        
        llms_to_use = st.multiselect(
            "Select the LLMs to use",
            available_llms,
            default=[available_llms[0]] if available_llms else [],
            help="Select the LLM providers to use for the multi-agent simulation, if you want to have multiple ones.",
            disabled=not multiagent_linddun_go,
        )
    with c2:
        linddun_go_submit_button = st.button(label="Simulate LINDDUN Go", help="Simulate the LINDDUN Go process to identify privacy threats.", disabled=not st.session_state["input"]["app_description"] and not st.session_state["dfd_only"])
    

    if linddun_go_submit_button: 
        inputs = st.session_state["input"]
        threats = []
        # Show a spinner while generating the attack tree
        with st.spinner("Answering questions..."):
            try:
                if multiagent_linddun_go:
                    if not llms_to_use:
                        raise ValueError("Please select at least one LLM to use.")
                    threats = get_multiagent_linddun_go(
                        st.session_state["keys"], 
                        {
                            "openai_model": st.session_state["openai_model"],
                            "mistral_model": st.session_state["mistral_model"],
                            "google_model": None,
                        },
                        inputs, 
                        st.session_state["temperature"],
                        rounds, 
                        threats_to_analyze,
                        llms_to_use,
                    )
                elif st.session_state["model_provider"] == "OpenAI API":
                    threats = get_linddun_go(
                        st.session_state["keys"]["openai_api_key"], 
                        st.session_state["openai_model"], 
                        inputs,
                        threats_to_analyze,
                        st.session_state["temperature"],
                    )
            except Exception as e:
                st.error(f"Error generating simulation: {e}")

        # Convert the threat model JSON to Markdown
        markdown_output = linddun_go_gen_markdown(threats)
        st.session_state["linddun_go_output"] = markdown_output
        st.session_state["linddun_go_threats"] = threats


    # If present, display the LINDDUN Go simulation result
    if st.session_state["linddun_go_output"] != "":
        st.markdown("# LINDDUN Go simulation result")
        # Display the threat model in Markdown
        st.markdown(st.session_state["linddun_go_output"], unsafe_allow_html=True)
        # Add a button to allow the user to download the output as a Markdown file
        st.download_button(
            label="Download Output",
            data=st.session_state["linddun_go_output"],  # Use the Markdown output
            file_name="linddun_go_output.md",
            mime="text/markdown",
        )
