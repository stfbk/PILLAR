import streamlit as st

def sidebar():
    st.sidebar.image("images/logo1.png")

    st.sidebar.markdown("By [Andrea Bissoli](https://www.linkedin.com/in/andrea-bissoli/) and [Majid Mollaeefar](https://www.linkedin.com/in/majid-mollaeefar/).")
    st.sidebar.markdown(
        "Star on GitHub: [![Star on GitHub](https://img.shields.io/github/stars/AndreaBissoli/linddun-gpt?style=social)](https://github.com/AndreaBissoli/linddun-gpt)"
    )
    st.sidebar.header("How to use LINDDUN GPT")
    if "keys" not in st.session_state:
        st.session_state["keys"] = {}
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"
    if "google_model" not in st.session_state:
        st.session_state["google_model"] = "gemini-1.5-pro-latest"
    if "mistral_model" not in st.session_state:
        st.session_state["mistral_model"] = "mistral-large-latest"

    with st.sidebar:
        try:
            openai_api_key = st.secrets["openai_api_key"]
            st.session_state["keys"]["openai_api_key"] = openai_api_key
            google_api_key = st.secrets["google_api_key"]
            st.session_state["keys"]["google_api_key"] = google_api_key
            mistral_api_key = st.secrets["mistral_api_key"]
            st.session_state["keys"]["mistral_api_key"] = mistral_api_key
        except Exception as e:
            st.warning("No secrets file found")
            if "openai_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["openai_api_key"] = ""
            if "google_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["google_api_key"] = ""
            if "mistral_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["mistral_api_key"] = ""
            openai_api_key = ""
            google_api_key = ""
            mistral_api_key = ""
        # Add model selection input field to the sidebar
        model_provider = st.selectbox(
            "Select your preferred model provider:",
            [
                "OpenAI API",
                "Google AI API",
                "Mistral API",
            ],
            key="model_provider",
            help="Select the model provider you would like to use. This will determine the models available for selection.",
        )
        st.markdown(
                """
        1. Enter your [OpenAI API
           key](https://platform.openai.com/account/api-keys), [Google AI API
           key](https://makersuite.google.com/app/apikey) and/or [Mistral API
           key](https://console.mistral.ai/api-keys/) below. Also, choose the
           models you would like to use for each provider.
        2. Provide details of the application that you would like to privacy threat model, both in the Application Info and DFD tabs.
        3. Generate a privacy threat model with different methods, choosing the
           Threat model, LINDDUN Go or LINDDUN Pro tab. You can use more than
           one tab to compare the results.
        4. Analyze each threat generated by the models and generate control
           measures and impact assessments in the Risk Assessment tab.
        5. Finally, download the complete report in the Report tab.
        """
            )
        st.header("""Configure here the API keys and models you would like to use for the privacy threat modelling:""")
        llm_to_configure = st.selectbox(
            "Select LLM to configure:",
            [
                "OpenAI API",
                "Google AI API",
                "Mistral API",
            ],
            help="Select the model provider you would like to insert the keys for. This will determine the models available for selection.",
        )

        c1, c2 = st.columns([1, 1])

        with c1:
            if llm_to_configure == "OpenAI API":
                openai_api_key_input = st.text_input(
                    "OpenAI API key:",
                    type="password",
                    help="You can find your OpenAI API key on the [OpenAI dashboard](https://platform.openai.com/account/api-keys).",
                )
                if openai_api_key_input:
                    openai_api_key = openai_api_key_input
                st.session_state["keys"]["openai_api_key"] = openai_api_key

            if llm_to_configure == "Google AI API":
                google_api_key_input = st.text_input(
                    "Google AI API key:",
                    type="password",
                    help="You can generate a Google AI API key in the [Google AI Studio](https://makersuite.google.com/app/apikey).",
                )
                if google_api_key_input:
                    google_api_key = google_api_key_input
                st.session_state["keys"]["google_api_key"] = google_api_key

            if llm_to_configure == "Mistral API":
                mistral_api_key_input = st.text_input(
                    "Mistral API key:",
                    type="password",
                    help="You can generate a Mistral API key in the [Mistral console](https://console.mistral.ai/api-keys/).",
                )
                if mistral_api_key_input:
                    mistral_api_key = mistral_api_key_input
                st.session_state["keys"]["mistral_api_key"] = mistral_api_key

        with c2:
            if llm_to_configure == "OpenAI API":
                openai_model = st.selectbox(
                    "OpenAI model:",
                    ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo", "gpt-4", "gpt-4o"],
                    help="OpenAI have moved to continuous model upgrades so `gpt-3.5-turbo`, `gpt-4` and `gpt-4-turbo` point to the latest available version of each model.",
                )
                if openai_model != st.session_state["openai_model"]:
                    st.session_state["openai_model"] = openai_model
            if llm_to_configure == "Google AI API":
                google_model = st.selectbox(
                    "Google AI model:",
                    ["gemini-1.5-pro-latest"],
                )
                if google_model != st.session_state["google_model"]:
                    st.session_state["google_model"] = google_model
            if llm_to_configure == "Mistral API":
                mistral_model = st.selectbox(
                    "Mistral model:",
                    ["mistral-large-latest", "mistral-small-latest", "open-mixtral-8x22b"],
                )
                if mistral_model != st.session_state["mistral_model"]:
                    st.session_state["mistral_model"] = mistral_model

        st.markdown("""---""")
        st.slider("Temperature setting", 0.0, 1.0, 0.7, key="temperature", help="The randomness of the model's responses. Lower values lead to more deterministic answers, higher values make the model more creative, but also more prone to hallucination.")

# Add "About" section to the sidebar
    st.sidebar.header("About")

    with st.sidebar:
        st.markdown(
            """Welcome to LINDDUN GPT, an AI-powered tool designed to help developers
        in privacy threat modelling for their applications, using the [LINDDUN](https://linddun.org/) methodology."""
        )
        st.markdown(
            """
Privacy threat modelling is a key activity in the software development
lifecycle, but is often overlooked or poorly executed. LINDDUN GPT aims
to help teams produce more comprehensive threat models by
leveraging the power of Large Language Models (LLMs) to generate a
threat list for an application based on the details provided, analyzing threats
specified by the LINDDUN scheme. To do so, LINDDUN GPT leverages different
LINDDUN methodologies, such as LINDDUN Go and LINDDUN Pro, to generate a list
of threats based on the application's Data Flow Diagram and description. Once
the threat list has been generated, LINDDUN GPT allows users to analyze each
threat individually, generating control measures and assessing the impact of
each threat. Finally, users can complete the privacy threat modeling process by
downloading a complete report of the privacy threat modeling and risk
assessment, which allows for a subsequent improvement of the application's
privacy protection. LINDDUN GPT is a tool that aims to make privacy threat
modelling more accessible and efficient for developers, helping them to
identify and mitigate privacy risks in their applications, and ultimately
improve the privacy protection of their users.

---
"""
        )


# Add "Example Application Description" section to the sidebar
    st.sidebar.header("Example Application Description")

    with st.sidebar:
        st.markdown(
            "Below is an example application description that you can use to test LINDDUN GPT:"
        )
        st.code(
            """
            A web application that 
            allows users to create, store, and share
            personal notes. The application is built using the React frontend
            framework and a Node.js backend with a MongoDB database. Users can
            sign up for an account and log in using OAuth2 with Google or
            Facebook. The notes are encrypted at rest and are only accessible
            by the user who created them. The application also supports
            real-time collaboration on notes with other users.
            """,
            language="md"
        )
        st.markdown(
            "Additionally, this is an example for the data policy section that works with the example application and highlights some possible issues:"
        )
        st.code(
            """
            The application stores 
            user data in a MongoDB database. Users can
            access, modify, or delete their data by logging into their account.
            The data retention policy specifies that user data is stored for 2
            years after account deletion, after which it is permanently deleted.
            The application uses encryption to protect user data at rest and in
            transit. User data is never shared with third parties without user
            consent, except for advertising purposes.
            """,
            language="md"
        )
        st.markdown("""---""")
    

# Add "FAQs" section to the sidebar
    st.sidebar.header("FAQs")

    with st.sidebar:
        st.markdown(
            """
        ### **What is LINDDUN?**
        [LINDDUN](https://linddun.org/) is a privacy threat modeling methodology that helps developers
        identify and mitigate privacy risks in their applications, similar to
        the STRIDE security threat modeling methodology. The LINDDUN acronym
        stands for Linking, Identifying, Non-repudiation, Detecting, Data
        disclosure, Unawareness and unintervenability, and Non-compliance.
        LINDDUN GPT uses the LINDDUN methodology to generate threat models for
        applications.
        """
        )
        st.markdown(
            """
        ### **How does LINDDUN GPT work?**
        When you enter an application description, other relevant details and
        optionally a Data Flow Diagram, the tool will use an LLM to generate a
        threat model for your application. The model uses the application
        description and DFD and details to generate a list of potential threats
        and then categorises each threat according to the LINDDUN methodology.
        """
        )
        st.markdown(
            """
        ### **Do you store the application details provided?**
        No, LINDDUN GPT does not store your application description or other
        details. All entered data is deleted after you close the browser tab.
        Of course, to query the LLM, a request containing the data is sent to
        the respective API provider, and they may store the request data
        according to their privacy policies.
        """
        )
        st.markdown(
            """
        ### **Why does it take so long to generate a threat model?**
        Since LINDDUN GPT uses Large Language Models (LLMs) to generate threat
        models, the process can take some time, especially for complex
        applications. The time taken depends on the complexity of the
        application, the model provider, and the model used. Also, some
        functionalities of LINDDUN GPT take more than others, such as the
        multi-agent LINDDUN Go. Please be patient while the model generates the
        threat model.
        """
        )
        st.markdown(
            """
        ### **Are the threat models 100% accurate?**
        No, the threat models are not 100% accurate. LINDDUN GPT uses Large
        Language Models (LLMs) to generate its output. The LLMs are powerful
        and are prompted in such a way that they generate relevant content, but
        they sometimes make mistakes and are prone to 'hallucinations'
        (generating irrelevant or inaccurate content). The output is meant
        only as a starting point for identifying and addressing potential
        privacy risks in your applications.
        """
        )
        st.markdown(
            """
        ### **How can I improve the accuracy of the threat models?**
        You can improve the accuracy of the threat models by providing a
        detailed description of the application and selecting the correct
        application type, authentication methods, and other details.
        The more information you provide, the more accurate the threat models
        will be.
        """
        )
