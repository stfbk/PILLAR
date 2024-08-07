import streamlit as st
import graphviz



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

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        app_description = st.text_area(
            label="Describe the application to be modelled",
            placeholder="Enter your application details...",
            height=250,
            help="Please provide a detailed description of the application, including the purpose of the application, the technologies used, and any other relevant information.",
            disabled=st.session_state["dfd_only"],
        )
        st.session_state["input"]["app_description"] = app_description

    # Ensure app_description is always up to date in the session state
    app_description = st.session_state["input"]["app_description"]


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
    
    # The data_editor widget allows the user to input the database schema The
    # database schema is a list of dictionaries, where each dictionary
    # represents a data type The variable database returns the list of
    # dictionaries
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
            # Configuration for the columns in the data_editor widget
            "data_type": st.column_config.TextColumn("Type", help="The type of data stored in the database.", width="medium", required=True),
            "encryption": st.column_config.CheckboxColumn("Encrypted", help="Whether the data type is encrypted.", width="small", required=True, default=True),
            "sensitive": st.column_config.CheckboxColumn("Sensitive", help="Whether the data is to be considered sensitive.", width="small", required=True, default=True),
            "notes": st.column_config.TextColumn("Notes", help="Enter any additional information which might be important in the privacy realm, such as the data's collection frequency.", width="medium", required=False, default=None),
        },
        # Allow the user to add or remove rows, modifying the database schema
        num_rows="dynamic",
        # Disable the widget if the application is in DFD-only mode or if the
        # user has unchecked the "has_database" checkbox
        disabled=not has_database or st.session_state["dfd_only"],
    )

    # Set the database schema in the session state
    # If the user has unchecked the "has_database" checkbox, set the database
    # schema to None
    database = None if not has_database else database
    if database != st.session_state["input"]["database"]:
        st.session_state["input"]["database"] = database

