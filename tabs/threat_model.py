import streamlit as st
from llms.threat_model import (
    get_threat_model_openai,
    get_threat_model_azure,
    get_threat_model_google,
    get_threat_model_mistral,
    threat_model_gen_markdown,
)
from llms.prompts import THREAT_MODEL_USER_PROMPT


def threat_model():
    st.markdown("""
A [LINDDUN](https://linddun.org/) privacy threat model helps identify and
evaluate potential privacy threats to applications / systems. It provides a
systematic approach to understanding possible privacy threats, classifying each
threat in one of the seven categories which compose the LINDDUN acronym. Use
this tab to generate a simple threat model with the LLM, which will provide a
list of potential threats to your application, classified by LINDDUN category.

---
""")


    # Create a submit button for Threat Modelling
    threat_model_submit_button = st.button(
        label="Generate Threat Model", 
        disabled= not st.session_state["input"]["app_description"] and not st.session_state["dfd_only"], 
        help="Generate a privacy threat model for the application."
    )

    model_provider = st.session_state["model_provider"]
    
    if "threat_model_output" not in st.session_state:
        st.session_state["threat_model_output"] = ""
    if "threat_model_threats" not in st.session_state:
        st.session_state["threat_model_threats"] = []

    # If the Generate Threat Model button is clicked and the user has provided an application description
    if threat_model_submit_button and (st.session_state["input"]["app_description"] or st.session_state["dfd_only"]):
        inputs = st.session_state["input"]
        threat_model_prompt = THREAT_MODEL_USER_PROMPT(
            inputs
        )

        # Show a spinner while generating the threat model
        with st.spinner("Analysing potential threats..."):
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Call the relevant get_threat_model function with the generated prompt
                    if model_provider == "Azure OpenAI Service":
                        model_output = get_threat_model_azure(
                            st.session_state["azure_api_endpoint"],
                            st.session_state["keys"]["azure_api_key"],
                            st.session_state["azure_api_version"],
                            st.session_state["azure_deployment_name"],
                            st.session_state["threat_model_prompt"],
                        )
                    elif model_provider == "OpenAI API":
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

                    # Access the threat model from the parsed content
                    threat_model = model_output.get("threat_model", [])

                    # Save the threat model to the session state for later use.
                    st.session_state["threat_model"] = threat_model
                    break  # Exit the loop if successful
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
        st.session_state["threat_model_threats"] = threat_model


    if st.session_state["threat_model_output"] != "":
        st.markdown("# Privacy threat model")
        # Display the threat model in Markdown
        st.markdown(st.session_state["threat_model_output"], unsafe_allow_html=True)
        # Add a button to allow the user to download the output as a Markdown file
        st.download_button(
            label="Download Threat Model",
            data=st.session_state["threat_model_output"],  # Use the Markdown output
            file_name="privacy_threat_model.md",
            mime="text/markdown",
        )
