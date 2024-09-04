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
import csv
from io import StringIO
import pandas as pd

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
    # Never have an empty schema, it breaks the data editor
    if not st.session_state["input"]["database"]: 
        st.session_state["input"]["database"] = [
            { "data_type": "", "encryption": False, "sensitive": False, "storage_location": "", "third_party": False, "purpose": "", "notes": "" },
        ]

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

        types_of_data = st.multiselect(
            "What types of data does your application collect, process, or store?",
            ["PII", "Financial information", "Health information", "User activity data", "Sensitive communication", "Geolocation", "Other"],
            disabled=st.session_state["dfd_only"],
        )
        if types_of_data != st.session_state["input"]["types_of_data"]:
            st.session_state["input"]["types_of_data"] = types_of_data

    with col3:
        user_data_control = st.text_area(
            label="How can the user act on the data collected by the application?",
            value=st.session_state["input"]["user_data_control"],
            help="Please describe how users can access, modify, or delete the data collected by the application or by relevant third-parties.",
            placeholder="Enter the possible actions...",
            height=100,
            disabled=st.session_state["dfd_only"],
        )
        if user_data_control != st.session_state["input"]["user_data_control"]:
            st.session_state["input"]["user_data_control"] = user_data_control
        data_policy = st.text_area(
            label="How does your application handle data retention and deletion?",
            value=st.session_state["input"]["data_policy"],
            help="Please describe the data retention and deletion policy of the application, including how long data is stored and how it is handled after account deletion, as well as any relevant third-party policies.",
            placeholder="Enter the data policy details...",
            height=100,
            disabled=st.session_state["dfd_only"],
        )
        if data_policy != st.session_state["input"]["data_policy"]:
            st.session_state["input"]["data_policy"] = data_policy

    def update_schema():
        """
        Update the schema with the changes made in the data editor. This is needed
        to keep the schema in sync with the table editor, because the data editor
        uses a pandas DataFrame, which is a different format than the
        row-based schema we use.
        """
        # "database" is what is returned by the data editor, and it contains the
        # changes made in the table editor. It has three keys: "edited_rows",
        # "added_rows" and "deleted_rows".
        changes = st.session_state["database"]
        # "state" is the schema currently stored in the session state
        # PLEASE NOTE: ["input"]["database"] is a list of dictionaries, while
        # ["database"] is an object with the changes. We need to update the list of
        # dictionaries with the changes made in the table editor.
        state = st.session_state["input"]["database"]
        # Update the schema with the changes made in the table editor
        for item in changes["edited_rows"]:
            for key in changes["edited_rows"][item]:
                state[item][key] = changes["edited_rows"][item][key]
        for added in changes["added_rows"]:
            state.append(added)
        for deleted in sorted(changes["deleted_rows"], reverse=True): # to avoid index errors, delete from the end
            state.pop(deleted)
        # Update the schema in the session state   
        st.session_state["input"]["database"] = state

    def format_correct(state):
        """
        This function formats the schema in the correct format for the data
        editor. It takes the schema in the format of a list of dictionaries and
        returns a dictionary with keys "data_type", "encryption", "sensitive",
        "storage_location", "third_party", "purpose", "notes", indicating the
        columns of the data editor. Thus, it transforms the DFD from a list of
        dictionaries to a dictionary of lists, or essentially from a row-based
        to a column-based format.
        
        Args:
            state (list): The DFD in the format of a list of dictionaries, with
                keys "data_type", "encryption", "sensitive", "storage_location",
                "third_party", "purpose", and "notes".
        Returns:
            dict: The DFD in the format of a dictionary of lists, with keys
                "data_type", "encryption", "sensitive", "storage_location",
                "third_party", "purpose", and "notes", where each list represents a
                column of the data editor.
        """
        
        # Create a new dictionary with the correct format
        new_dict = {
            "data_type": [],
            "encryption": [],
            "sensitive": [],
            "third_party": [],
            "storage_location": [],
            "purpose": [],
            "notes": [],
        }
        # For each row, append the values to the corresponding list
        for object in state:
            new_dict["data_type"].append(object["data_type"])
            new_dict["encryption"].append(object["encryption"])
            new_dict["sensitive"].append(object["sensitive"])
            new_dict["storage_location"].append(object["storage_location"])
            new_dict["third_party"].append(object["third_party"])
            new_dict["purpose"].append(object["purpose"])
            new_dict["notes"].append(object["notes"])
        return new_dict
    


    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")

    has_database = st.checkbox("Describe collected data", value=True, disabled=st.session_state["dfd_only"])
    has_database_toggled = False
    if has_database != st.session_state["input"]["has_database"]:
        has_database_toggled = True # The user has toggled the checkbox
        st.session_state["input"]["has_database"] = has_database
    
        

    if has_database:
        st.markdown("""
        Describe the data that is used by the application. You can specify the data
        types, whether they are encrypted, whether they are considered sensitive,
        whether they are shared with third parties, the location where they are
        stored, the purpose for collection and any additional notes. You can add or
        remove rows as needed.

        ---
        """
        )
        col1, col2 = st.columns([1, 2])
        with col1:
            uploaded_file = st.file_uploader(
                "Upload CSV file", 
                type=["csv"], 
                help="Upload a CSV file containing the collected data, in the format of a list of dictionaries with keys 'data_type', 'encryption', 'sensitive', 'storage_location', 'third_party', 'purpose', and 'notes'.",
                key="database_file",
                disabled=st.session_state["dfd_only"] or not st.session_state["input"]["has_database"],
            )
        if uploaded_file is not None:
            try:
                # Read the uploaded file as a CSV, transform it into a list of dictionaries and store it in the session state
                reader = csv.DictReader(StringIO(uploaded_file.getvalue().decode("utf-8-sig")), delimiter=",")
                schema_file = list(reader)
                st.session_state["input"]["database"] = schema_file
                for row in st.session_state["input"]["database"]:
                    # Convert the keys to a boolean, otherwise it will be a string
                    row["encryption"] = row["encryption"].lower() == "true"
                    row["sensitive"] = row["sensitive"].lower() == "true"
                    row["third_party"] = row["third_party"].lower() == "true"
                # If the user does not remove the uploaded file, the schema will not change until they do
                st.info("Please remove the uploaded file to modify the schema from the table.")
            except Exception as e:
                st.error(f"Error reading the uploaded file: {e}")
                


        # The data_editor widget allows the user to input the database schema The
        # database schema is a list of dictionaries, where each dictionary
        # represents a data type The variable database returns the list of
        # dictionaries
        database = st.data_editor(
            data=pd.DataFrame().from_dict(format_correct(st.session_state["input"]["database"])),
            column_config={
                # Configuration for the columns in the data_editor widget
                "data_type": st.column_config.TextColumn("Type", help="The type of data stored in the database.", width=None, required=True),
                "encryption": st.column_config.CheckboxColumn("Encrypted", help="Whether the data type is encrypted.", width=None, required=True, default=True),
                "sensitive": st.column_config.CheckboxColumn("Sensitive", help="Whether the data is to be considered sensitive.", width=None, required=True, default=True),
                "third_party": st.column_config.CheckboxColumn("Third Party", help="Whether the data is shared with a third party.", width=None, required=True, default=False),
                "storage_location": st.column_config.TextColumn("Storage Location", help="The location where the data is stored, such as a server-side database, the user's device or a cloud service.", width=None, required=False, default=""),
                "purpose": st.column_config.TextColumn("Purpose", help="The purpose for which the data is collected, such as user authentication or personalization. If it is shared with third parties, also specify them and their purposes.", width="medium", required=False, default=""),
                "notes": st.column_config.TextColumn("Additional Notes", help="Enter any additional information which might be important in the privacy realm, such as the data's collection frequency or for how long it is decrypted when used.", width="medium", required=False, default=""),
            },
            # Allow the user to add or remove rows, modifying the database schema
            num_rows="dynamic",
            # Disable the widget if the application is in DFD-only mode or if the
            # user has unchecked the "has_database" checkbox
            disabled=not has_database or st.session_state["dfd_only"],
            key="database",
            on_change=update_schema,
        )



    # If the user has unchecked the "has_database" checkbox, set the collected data
    # schema to None
    if has_database_toggled and not has_database:
        st.session_state["backup_database"] = st.session_state["input"]["database"]
        st.session_state["input"]["database"] = None
    # If the user has checked the "has_database" checkbox, restore the collected
    # data schema from the backup
    elif has_database_toggled and has_database:
        st.session_state["input"]["database"] = st.session_state["backup_database"]
        st.session_state["backup_database"] = None
        st.rerun()
    