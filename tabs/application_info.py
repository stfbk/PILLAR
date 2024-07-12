import streamlit as st
import base64

from llms.threat_model import (
    create_threat_model_prompt,
    get_threat_model,
    get_threat_model_azure,
    get_threat_model_google,
    get_threat_model_mistral,
    threat_model_gen_markdown,
    get_image_analysis,
    create_image_analysis_prompt,
)

# Function to get user input for the application description and key details
def get_description():
    input_text = st.text_area(
        label="Describe the application to be modelled",
        placeholder="Enter your application details...",
        height=150,
        help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
    )

    st.session_state["input"]["app_description"] = input_text

    return input_text

def init_state():
    st.session_state["input"]["app_description"] = ""
    st.session_state["input"]["app_type"] = ""
    st.session_state["input"]["authentication"] = []
    st.session_state["input"]["has_database"] = False
    st.session_state["input"]["database"] = None
    st.session_state["input"]["data_policy"] = ""


def application_info():
    st.markdown("""
In this section, you should describe as clearly and precisely as possible the
application. Include technical details and information about database schemas,
user roles, and any other relevant information. The more detailed the
description, the more accurate the threat model will be.
""")
    st.markdown("""---""")

    # Two column layout for the main app content
    col1, col2, col3 = st.columns([1, 1, 1])

    # Initialize app_input in the session state if it doesn't exist
    if "input" not in st.session_state:
        st.session_state["input"] = {}
        init_state()

    # If model provider is OpenAI API and the model is gpt-4-turbo or gpt-4o
    with col1:
        selected_model = st.session_state["selected_model"]
        openai_api_key = st.session_state["openai_api_key"]
        if st.session_state["model_provider"] == "OpenAI API" and selected_model in [
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
                                    # Update app_description session state
                                    st.session_state["app_description"] = (
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
            app_description = st.text_area(
                label="Describe the application to be modelled",
                value=st.session_state["input"]["app_description"],
                help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
                height=500,
            )
            # Update session state only if the text area content has changed
            if app_description != st.session_state["input"]["app_description"]:
                st.session_state["input"]["app_description"] = app_description

        else:
            # For other model providers or models, use the get_input() function
            app_description = get_description()
            # Update session state
            st.session_state["input"]["app_description"] = app_description

    # Ensure app_description is always up to date in the session state
    app_description = st.session_state["input"]["app_description"]




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
        )
        if app_type != st.session_state["input"]["app_type"]:
            st.session_state["input"]["app_type"] = app_type

        authentication = st.multiselect(
            "What authentication methods are supported by the application?",
            ["SSO", "MFA", "OAUTH2", "Basic", "None"],
        )
        if authentication != st.session_state["input"]["authentication"]:
            st.session_state["input"]["authentication"] = authentication
    with col3:
        data_policy = st.text_area(
            label="How can the user act on the data collected by the application?",
            value=st.session_state["input"]["data_policy"],
            help="Please describe the data policy of the application, including how users can access, modify, or delete their data. If possible, specify the data retention policy and how data is handled after account deletion.",
            placeholder="Enter the data policy details...",
            height=250,
        )
        if data_policy != st.session_state["input"]["data_policy"]:
            st.session_state["input"]["data_policy"] = data_policy


    has_database = st.checkbox("The app uses a database", value=True)
    if has_database != st.session_state["input"]["has_database"]:
        st.session_state["input"]["has_database"] = has_database
    st.markdown("""
    Describe the data that is stored in the database. Add or remove rows as needed.
    """
                )
    database = st.data_editor(
        data=[
            {"data_type": "Name", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Email", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Password", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Address", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Location", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Phone number", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Date of Birth", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "ID card number", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
            {"data_type": "Last access time", "encryption": True, "sensitive": True, "collection_frequency_minutes": 0},
        ],
        column_config={
            "data_type": st.column_config.TextColumn("Type", help="The type of data stored in the database.", width="medium", required=True),
            "encryption": st.column_config.CheckboxColumn("Encrypted", help="Whether the data type is encrypted.", width="small", required=True, default=True),
            "sensitive": st.column_config.CheckboxColumn("Sensitive", help="Whether the data is to be considered sensitive.", width="small", required=True, default=True),
            "collection_frequency_minutes": st.column_config.NumberColumn("Collection Frequency", help="The frequency at which the data is collected, in minutes. The value 0 means only once. Leaving the column empty gives no information.", width="medium", required=False, default=None),
        },
        num_rows="dynamic",
        disabled=not has_database,
    )

    database = None if not has_database else database
    if database != st.session_state["input"]["database"]:
        st.session_state["input"]["database"] = database

