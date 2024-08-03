import streamlit as st


# Function to get user input for the application description and key details
def get_description():
    input_text = st.text_area(
        label="Describe the application to be modelled",
        placeholder="Enter your application details...",
        height=250,
        help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
        disabled=st.session_state["dfd_only"],
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
In this tab, you should describe as clearly and precisely as possible the
application, by entering all the information in the slots below. Include
technical details and how the application works, as well as possible. In the
Data policy section, you should describe how personal data is handled by the
application, including how long it is retained. In the Database schema, you can
specify the data which is collected and used by the application, including if
it is encrypted at rest and whether it is considered sensitive. The more
details you include, the more accurate the subsequent analysis.

---
""")

    # Two column layout for the main app content
    col1, col2, col3 = st.columns([1, 1, 1])

    # Initialize app_input in the session state if it doesn't exist
    if "input" not in st.session_state:
        st.session_state["input"] = {}
        init_state()
    if "dfd_only" not in st.session_state:
        st.session_state["dfd_only"] = False

    # If model provider is OpenAI API and the model is gpt-4-turbo or gpt-4o
    with col1:
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
            disabled=st.session_state["dfd_only"],
        )
        if app_type != st.session_state["input"]["app_type"]:
            st.session_state["input"]["app_type"] = app_type

        authentication = st.multiselect(
            "What authentication methods are supported by the application?",
            ["SSO", "MFA", "OAUTH2", "Basic", "None"],
            disabled=st.session_state["dfd_only"],
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
            disabled=st.session_state["dfd_only"],
        )
        if data_policy != st.session_state["input"]["data_policy"]:
            st.session_state["input"]["data_policy"] = data_policy


    has_database = st.checkbox("The app uses a database", value=True, disabled=st.session_state["dfd_only"])
    if has_database != st.session_state["input"]["has_database"]:
        st.session_state["input"]["has_database"] = has_database
    st.markdown("""
    Describe the data that is stored in the database. Add or remove rows as needed.
    """
                )
    database = st.data_editor(
        data=[
            {"data_type": "Name", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Email", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Password", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Address", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Location", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Phone number", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Date of Birth", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "ID card number", "encryption": True, "sensitive": True, "notes": ""},
            {"data_type": "Last access time", "encryption": True, "sensitive": True, "notes": ""},
        ],
        column_config={
            "data_type": st.column_config.TextColumn("Type", help="The type of data stored in the database.", width="medium", required=True),
            "encryption": st.column_config.CheckboxColumn("Encrypted", help="Whether the data type is encrypted.", width="small", required=True, default=True),
            "sensitive": st.column_config.CheckboxColumn("Sensitive", help="Whether the data is to be considered sensitive.", width="small", required=True, default=True),
            "notes": st.column_config.TextColumn("Notes", help="Enter any additional information which might be important in the privacy realm, such as the data's collection frequency.", width="medium", required=False, default=None),
        },
        num_rows="dynamic",
        disabled=not has_database or st.session_state["dfd_only"],
    )

    database = None if not has_database else database
    if database != st.session_state["input"]["database"]:
        st.session_state["input"]["database"] = database

