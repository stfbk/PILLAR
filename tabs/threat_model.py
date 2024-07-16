import streamlit as st
from llms.threat_model import (
    create_threat_model_prompt,
    get_threat_model,
    get_threat_model_azure,
    get_threat_model_google,
    get_threat_model_mistral,
    threat_model_gen_markdown,
)


def threat_model():
    st.markdown("""
A [LINDDUN](https://linddun.org/) privacy threat model helps identify and evaluate potential privacy threats to applications / systems. It provides a systematic approach to 
understanding possible privacy threats and provides suggestions on how to mitigate the risk. Use this tab to generate a threat model using the LINDDUN methodology.
""")
    st.markdown("""---""")


    # Create a submit button for Threat Modelling
    threat_model_submit_button = st.button(label="Generate Threat Model")

    model_provider = st.session_state["model_provider"]
    
    if "threat_model_output" not in st.session_state:
        st.session_state["threat_model_output"] = ""

    # If the Generate Threat Model button is clicked and the user has provided an application description
    if threat_model_submit_button and st.session_state["input"]["app_description"]:
        inputs = st.session_state["input"]
        threat_model_prompt = create_threat_model_prompt(
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
                        model_output = get_threat_model(
                            st.session_state["keys"]["openai_api_key"], st.session_state["openai_model"], threat_model_prompt
                        )
                    elif model_provider == "Google AI API":
                        model_output = get_threat_model_google(
                            st.session_state["keys"]["google_api_key"], st.session_state["google_model"], threat_model_prompt
                        )
                    elif model_provider == "Mistral API":
                        model_output = get_threat_model_mistral(
                            st.session_state["keys"]["mistral_api_key"], st.session_state["mistral_model"], threat_model_prompt
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

    # If the submit button is clicked and the user has not provided an application description
    elif threat_model_submit_button and not st.session_state["input"]["app_description"]:
        st.error("Please enter your application details before submitting.")
        
    # Display the threat model in Markdown
    st.markdown(st.session_state["threat_model_output"], unsafe_allow_html=True)

    if st.session_state["threat_model_output"] != "":
        # Add a button to allow the user to download the output as a Markdown file
        st.download_button(
            label="Download Threat Model",
            data=st.session_state["threat_model_output"],  # Use the Markdown output
            file_name="privacy_threat_model.md",
            mime="text/markdown",
        )
