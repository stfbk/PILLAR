# main.py

import base64
import streamlit as st
import streamlit.components.v1 as components

from threat_model import (
    create_threat_model_prompt,
    get_threat_model,
    get_threat_model_quality_prompt,
    get_threat_model_azure,
    get_threat_model_google,
    get_threat_model_mistral,
    threat_model_gen_markdown,
    get_image_analysis,
    create_image_analysis_prompt,
)

from linddun_go import (
    get_linddun_go,
    linddun_go_gen_markdown,
)

# ------------------ Helper Functions ------------------ #


# Function to get user input for the application description and key details
def get_input():
    input_text = st.text_area(
        label="Describe the application to be modelled",
        placeholder="Enter your application details...",
        height=150,
        key="app_desc",
        help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
    )

    st.session_state["app_input"] = input_text

    return input_text


# Function to render Mermaid diagram
def mermaid(code: str, height: int = 500) -> None:
    components.html(
        f"""
        <pre class="mermaid" style="height: {height}px;">
            {code}
        </pre>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """,
        height=height,
    )


# ------------------ Streamlit UI Configuration ------------------ #

st.set_page_config(
    page_title="LINDDUN GPT",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------ Sidebar ------------------ #

st.sidebar.image("images/logo.png")

# Add instructions on how to use the app to the sidebar
st.sidebar.header("How to use LINDDUN GPT")

with st.sidebar:
    # Add model selection input field to the sidebar
    model_provider = st.selectbox(
        "Select your preferred model provider:",
        [
            "OpenAI API",
            "Google AI API",
        ],  # ["OpenAI API", "Azure OpenAI Service", "Google AI API", "Mistral API"],
        key="model_provider",
        help="Select the model provider you would like to use. This will determine the models available for selection.",
    )

    if model_provider == "OpenAI API":
        st.markdown(
            """
    1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) and chosen model below 🔑
    2. Provide details of the application that you would like to threat model  📝
    3. Generate a threat list, attack tree and/or mitigating controls for your application 🚀
    """
        )
        # Add OpenAI API key input field to the sidebar
        openai_api_key_input = st.text_input(
            "Enter your OpenAI API key:",
            type="password",
            help="You can find your OpenAI API key on the [OpenAI dashboard](https://platform.openai.com/account/api-keys).",
        )
        openai_api_key = openai_api_key_input if openai_api_key_input else st.secrets["openai_api_key"]

        # Add model selection input field to the sidebar
        selected_model = st.selectbox(
            "Select the model you would like to use:",
            ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4", "gpt-4o"],
            key="selected_model",
            help="OpenAI have moved to continuous model upgrades so `gpt-3.5-turbo`, `gpt-4` and `gpt-4-turbo` point to the latest available version of each model.",
        )

    if model_provider == "Azure OpenAI Service":
        st.markdown(
            """
    1. Enter your Azure OpenAI API key, endpoint and deployment name below 🔑
    2. Provide details of the application that you would like to threat model  📝
    3. Generate a threat list, attack tree and/or mitigating controls for your application 🚀
    """
        )

        # Add Azure OpenAI API key input field to the sidebar
        azure_api_key = st.text_input(
            "Azure OpenAI API key:",
            type="password",
            help="You can find your Azure OpenAI API key on the [Azure portal](https://portal.azure.com/).",
        )

        # Add Azure OpenAI endpoint input field to the sidebar
        azure_api_endpoint = st.text_input(
            "Azure OpenAI endpoint:",
            help="Example endpoint: https://YOUR_RESOURCE_NAME.openai.azure.com/",
        )

        # Add Azure OpenAI deployment name input field to the sidebar
        azure_deployment_name = st.text_input(
            "Deployment name:",
        )

        st.info("Please note that you must use an 1106-preview model deployment.")

        azure_api_version = "2023-12-01-preview"  # Update this as needed

        st.write(f"Azure API Version: {azure_api_version}")

    if model_provider == "Google AI API":
        st.markdown(
            """
    1. Enter your [Google AI API key](https://makersuite.google.com/app/apikey) and chosen model below 🔑
    2. Provide details of the application that you would like to threat model  📝
    3. Generate a threat list, attack tree and/or mitigating controls for your application 🚀
    """
        )
        # Add OpenAI API key input field to the sidebar
        google_api_key_input = st.text_input(
            "Enter your Google AI API key:",
            type="password",
            help="You can generate a Google AI API key in the [Google AI Studio](https://makersuite.google.com/app/apikey).",
        )
        google_api_key = google_api_key_input if google_api_key_input else st.secrets["google_api_key"]

        # Add model selection input field to the sidebar
        google_model = st.selectbox(
            "Select the model you would like to use:",
            ["gemini-1.5-pro-latest"],
            key="selected_model",
        )

    if model_provider == "Mistral API":
        st.markdown(
            """
    1. Enter your [Mistral API key](https://console.mistral.ai/api-keys/) and chosen model below 🔑
    2. Provide details of the application that you would like to threat model  📝
    3. Generate a threat list, attack tree and/or mitigating controls for your application 🚀
    """
        )
        # Add OpenAI API key input field to the sidebar
        mistral_api_key = st.text_input(
            "Enter your Mistral API key:",
            type="password",
            help="You can generate a Mistral API key in the [Mistral console](https://console.mistral.ai/api-keys/).",
        )

        # Add model selection input field to the sidebar
        mistral_model = st.selectbox(
            "Select the model you would like to use:",
            ["mistral-large-latest", "mistral-small-latest"],
            key="selected_model",
        )

    st.markdown("""---""")

# Add "About" section to the sidebar
st.sidebar.header("About")

with st.sidebar:
    st.markdown(
        """Welcome to LINDDUN GPT, an AI-powered tool designed to help developers
    in privacy threat modelling for their applications, using the [LINDDUN](https://linddun.org/) methodology."""
    )
    st.markdown(
        """Privacy threat modelling is a key activity in the software development
        lifecycle, but is often overlooked or poorly executed. LINDDUN GPT aims
            to help teams produce more comprehensive threat models by
            leveraging the power of Large Language Models (LLMs) to generate a
            threat list for an
    application based on the details provided, analyzing threats specified by the LINDDUN scheme."""
    )
    st.markdown("""---""")


# Add "Example Application Description" section to the sidebar
st.sidebar.header("Example Application Description")

with st.sidebar:
    st.markdown(
        "Below is an example application description that you can use to test LINDDUN GPT:"
    )
    st.markdown(
        "> A web application that allows users to create, store, and share personal notes. The application is built using the React frontend framework and a Node.js backend with a MongoDB database. Users can sign up for an account and log in using OAuth2 with Google or Facebook. The notes are encrypted at rest and are only accessible by the user who created them. The application also supports real-time collaboration on notes with other users."
    )
    st.markdown("""---""")

# Add "FAQs" section to the sidebar
st.sidebar.header("FAQs")

#with st.sidebar:


# ------------------ Main App UI ------------------ #

tab1, tab2, tab3 = st.tabs(
    ["Application info", "Threat Model", "LINDDUN Go"],
)

with tab1:
    st.markdown("""
In this section, you should describe as clearly and precisely as possible the
application. Include technical details and information about database schemas,
user roles, and any other relevant information. The more detailed the
description, the more accurate the threat model will be.
""")
    st.markdown("""---""")

    # Two column layout for the main app content
    col1, col2 = st.columns([1, 1])

    # Initialize app_input in the session state if it doesn't exist
    if "app_input" not in st.session_state:
        st.session_state["app_input"] = ""

    # If model provider is OpenAI API and the model is gpt-4-turbo or gpt-4o
    with col1:
        if model_provider == "OpenAI API" and selected_model in [
            "gpt-4-turbo",
            "gpt-4o",
        ]:
            uploaded_file = st.file_uploader(
                "Upload architecture diagram", type=["jpg", "jpeg", "png"]
            )

            if uploaded_file is not None:
                if not openai_api_key:
                    st.error("Please enter your OpenAI API key to analyse the image.")
                else:
                    if (
                        "uploaded_file" not in st.session_state
                        or st.session_state.uploaded_file != uploaded_file
                    ):
                        st.session_state.uploaded_file = uploaded_file
                        with st.spinner("Analysing the uploaded image..."):

                            def encode_image(uploaded_file):
                                return base64.b64encode(uploaded_file.read()).decode(
                                    "utf-8"
                                )

                            base64_image = encode_image(uploaded_file)

                            image_analysis_prompt = create_image_analysis_prompt()

                            try:
                                image_analysis_output = get_image_analysis(
                                    openai_api_key,
                                    selected_model,
                                    image_analysis_prompt,
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
                                    st.session_state.image_analysis_content = (
                                        image_analysis_content
                                    )
                                    # Update app_input session state
                                    st.session_state["app_input"] = (
                                        image_analysis_content
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

            # Use text_area with the session state value and update the session state on change
            app_input = st.text_area(
                label="Describe the application to be modelled",
                value=st.session_state["app_input"],
                key="app_input_widget",
                help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
            )
            # Update session state only if the text area content has changed
            if app_input != st.session_state["app_input"]:
                st.session_state["app_input"] = app_input

        else:
            # For other model providers or models, use the get_input() function
            app_input = get_input()
            # Update session state
            st.session_state["app_input"] = app_input

    # Ensure app_input is always up to date in the session state
    app_input = st.session_state["app_input"]

    # Create input fields for additional details
    with col2:
        app_type = st.selectbox(
            label="Select the application type",
            options=[
                "Web application",
                "Mobile application",
                "Desktop application",
                "Cloud application",
                "IoT application",
                "Other",
            ],
            key="app_type",
        )
        if app_type != st.session_state["app_type"]:
            st.session_state["app_type"] = app_type

        sensitive_data = st.selectbox(
            label="What is the highest sensitivity level of the data processed by the application?",
            options=[
                "Top Secret",
                "Secret",
                "Confidential",
                "Restricted",
                "Unclassified",
                "None",
            ],
            key="sensitive_data",
        )
        if sensitive_data != st.session_state["sensitive_data"]:
            st.session_state["sensitive_data"] = sensitive_data

        # Create input fields for internet_facing and authentication
        internet_facing = st.selectbox(
            label="Is the application internet-facing?",
            options=["Yes", "No"],
            key="internet_facing",
        )
        if internet_facing != st.session_state["internet_facing"]:
            st.session_state["internet_facing"] = internet_facing

        authentication = st.multiselect(
            "What authentication methods are supported by the application?",
            ["SSO", "MFA", "OAUTH2", "Basic", "None"],
            key="authentication",
        )
        if authentication != st.session_state["authentication"]:
            st.session_state["authentication"] = authentication

with tab2:
    st.markdown("""
A [LINDDUN](https://linddun.org/) threat model helps identify and evaluate potential privacy threats to applications / systems. It provides a systematic approach to 
understanding possible privacy threats and provides suggestions on how to mitigate the risk. Use this tab to generate a threat model using the LINDDUN methodology.
""")
    st.markdown("""---""")

    # ------------------ Threat Model Generation ------------------ #

    # Create a submit button for Threat Modelling
    threat_model_submit_button = st.button(label="Generate Threat Model")

    # If the Generate Threat Model button is clicked and the user has provided an application description
    if threat_model_submit_button and st.session_state.get("app_input"):
        app_input = st.session_state["app_input"]  # Retrieve from session state
        # Generate the prompt using the create_prompt function
        threat_model_prompt = create_threat_model_prompt(
            app_type, authentication, internet_facing, sensitive_data, app_input
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
                            azure_api_endpoint,
                            azure_api_key,
                            azure_api_version,
                            azure_deployment_name,
                            threat_model_prompt,
                        )
                    elif model_provider == "OpenAI API":
                        model_output = get_threat_model(
                            openai_api_key, selected_model, threat_model_prompt
                        )
                    elif model_provider == "Google AI API":
                        model_output = get_threat_model_google(
                            google_api_key, google_model, threat_model_prompt
                        )
                    elif model_provider == "Mistral API":
                        model_output = get_threat_model_mistral(
                            mistral_api_key, mistral_model, threat_model_prompt
                        )

                    # Access the threat model and improvement suggestions from the parsed content
                    threat_model = model_output.get("threat_model", [])
                    improvement_suggestions = model_output.get(
                        "improvement_suggestions", []
                    )

                    # Save the threat model to the session state for later use in mitigations
                    st.session_state["threat_model"] = threat_model
                    break  # Exit the loop if successful
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        st.error(
                            f"Error generating threat model after {max_retries} attempts: {e}"
                        )
                        threat_model = []
                        improvement_suggestions = []
                    else:
                        st.warning(
                            f"Error generating threat model. Retrying attempt {retry_count+1}/{max_retries}..."
                        )

        # Convert the threat model JSON to Markdown
        markdown_output = threat_model_gen_markdown(threat_model, improvement_suggestions)

        # Display the threat model in Markdown
        st.markdown(markdown_output, unsafe_allow_html=True)

        # Add a button to allow the user to download the output as a Markdown file
        st.download_button(
            label="Download Threat Model",
            data=markdown_output,  # Use the Markdown output
            file_name="linddun_gpt_threat_model.md",
            mime="text/markdown",
        )

# If the submit button is clicked and the user has not provided an application description
if threat_model_submit_button and not st.session_state.get("app_input"):
    st.error("Please enter your application details before submitting.")
    
# ------------------ LINDDUN Go ------------------ #

with tab3:
    st.markdown("""
The [LINDDUN Go](https://linddun.org/go/) process enables teams to dynamically apply the
LINDDUN methodology to identify and assess privacy threats in real-time. This
interactive simulation guides the LLM through the steps of the LINDDUN Go
framework, asking questions about the application to elicit potential threats.
By simulating [this process](https://linddun.org/go-getting-started/), developers can quickly identify and address privacy
threats just by providing the description.
""")
    st.markdown("""---""")
    
    linddun_go_submit_button = st.button(label="Simulate LINDDUN Go")
    
    if linddun_go_submit_button and st.session_state.get('app_input'):
        app_input = st.session_state.get('app_input')
        authentication = st.session_state.get('authentication')
        internet_facing = st.session_state.get('internet_facing')
        sensitive_data = st.session_state.get('sensitive_data')
        app_type = st.session_state.get('app_type')


        # Show a spinner while generating the attack tree
        with st.spinner("Answering questions..."):
            try:
                if model_provider == "OpenAI API":
                    present_threats = get_linddun_go(openai_api_key, selected_model, app_type, authentication, internet_facing, sensitive_data, app_input)

            except Exception as e:
                st.error(f"Error generating simulation: {e}")

        # Convert the threat model JSON to Markdown
        markdown_output = linddun_go_gen_markdown(present_threats)

        # Display the threat model in Markdown
        st.markdown(markdown_output, unsafe_allow_html=True)

        # Add a button to allow the user to download the output as a Markdown file
        st.download_button(
            label="Download Output",
            data=markdown_output,  # Use the Markdown output
            file_name="linddun_go_process_output.md",
            mime="text/markdown",
        )

if linddun_go_submit_button and not st.session_state.get("app_input"):
    st.error("Please enter your application details before submitting.")