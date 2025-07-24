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
import lmstudio as lms
from lmstudio import DownloadedLlm
import requests
import json
from llms.config import OLLAMA_CONFIG

def get_ollama_models():
    """Get list of available Ollama models from remote VM through SSH tunnel"""
    try:
        response = requests.get(f'http://localhost:{OLLAMA_CONFIG["port"]}/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json()
            if not models.get('models'):
                st.warning("No models found in remote Ollama instance")
                return []
            return [model['name'] for model in models['models']]
        st.error(f"Error fetching models from remote Ollama: {response.status_code}")
        return []
    except requests.Timeout:
        st.error("Connection to remote Ollama timed out. Is the SSH tunnel active?")
        return []
    except requests.ConnectionError:
        st.error(f"Could not connect to Ollama through SSH tunnel on port {OLLAMA_CONFIG['port']}. Check if:\n"
                "1. SSH tunnel is active\n"
                "2. Ollama is running on the remote machine\n"
                "3. Port forwarding is working")
        return []
    except Exception as e:
        st.error(f"Unexpected error connecting to remote Ollama: {str(e)}")
        return []

def sidebar():
        
        
    with st.sidebar:

        _, center, _ = st.columns([0.2, 1, 0.2]) # Columns to center the image
        with center:
            st.image("images/logo-bottom.png", width=200)

        
        st.header("How to use P.I.L.L.A.R.")

        try:
            # Load the API keys from the secrets file, if available
            openai_api_key = st.secrets["openai_api_key"]
            st.session_state["keys"]["openai_api_key"] = openai_api_key
            google_api_key = st.secrets["google_api_key"]
            st.session_state["keys"]["google_api_key"] = google_api_key
            mistral_api_key = st.secrets["mistral_api_key"]
            st.session_state["keys"]["mistral_api_key"] = mistral_api_key
        except Exception as e:
            # st.warning("No secrets file found")
            # If the API keys are not in the secrets file, initialize them as
            # empty strings
            if "openai_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["openai_api_key"] = ""
            if "google_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["google_api_key"] = ""
            if "mistral_api_key" not in st.session_state["keys"]:
                st.session_state["keys"]["mistral_api_key"] = ""
            openai_api_key = ""
            google_api_key = ""
            mistral_api_key = ""

        model_options =[
                "OpenAI API",
                "Google AI API",
                "Mistral API",
                # "Local LM Studio",
                # "Ollama",
            ]
        if "disable_local_lm_studio" not in st.secrets:
                model_options.append("Local LM Studio")
        
        if "disable_local_ollama" not in st.secrets:
                model_options.append("Ollama")

        # Add model selection input field to the sidebar
        model_provider = st.selectbox(
            "Select your preferred model provider:",
            model_options,
            key="model_provider",
            help="Select the model provider you would like to use. This will determine the models available for selection.",
        )


        # Show provider-specific instructions
        if model_provider == "Ollama":
            st.markdown(
                """
        **For using remote Ollama through SSH tunnel on port 11434.**

        **Make sure:**\n

        1. The port 11434 on your machine is available (stop local Ollama if needed)
        2. SSH tunnel is active: `ssh -N -L 11434:localhost:11434 remote@ip`
        3. Ollama is running on the remote machine
        4. Select and load a model 
        """
            )
        elif model_provider == "Local LM Studio":
            st.markdown(
                """
        **Using Local LM Studio.**

        **Make sure:**
        1. LM Studio is installed and running on your machine
        2. You have downloaded the models you want to use
        3. Select and load a model 
        """
            )
        else:
            st.markdown(
                """
                1. Enter your [OpenAI API
                key](https://platform.openai.com/account/api-keys), [Google AI API
                key](https://makersuite.google.com/app/apikey) and/or [Mistral API
                key](https://console.mistral.ai/api-keys/) below. Also, choose the
                models you would like to use for each provider.
                2. Provide details of the application that you would like to privacy
                threat model, in the Application Info and DFD tabs (some features
                only require one of these).
                3. Generate a privacy threat model with different methods, choosing the
                Threat model, LINDDUN Go or LINDDUN Pro tab. You can use more than
                one tab to compare the results.
                4. Analyze each threat generated by the models and generate control
                measures and impact assessments in the Risk Assessment tab.
                5. Finally, download the complete report in the Report tab.
                """
            )
        
        # LLM configuration section, provider-specific header/instructions
        if model_provider == "Ollama":
            st.header("Select a model from the list of available models for your privacy threat modeling:")
            available_models = get_ollama_models()
            if not available_models:
                st.warning("No models found in remote Ollama instance. Check SSH tunnel and remote Ollama status.")
                ollama_model = st.selectbox(
                    "Ollama model:",
                    ["No models available"],
                    disabled=True,
                    key="ollama_model_select"
                )
                st.button("Load Model", key="ollama_load", disabled=True)
            else:
                ollama_model = st.selectbox(
                    "Ollama model:",
                    available_models,
                    key="ollama_model_select"
                )
                if st.button("Load Model", key="ollama_load"):
                    try:
                        response = requests.post(
                            f'http://localhost:{OLLAMA_CONFIG["port"]}/api/pull',
                            json={"name": ollama_model}
                        )
                        if response.status_code == 200:
                            st.session_state["ollama_loaded"] = True
                            st.session_state["ollama_model"] = ollama_model
                            st.success(f"Successfully loaded {ollama_model} model")
                        else:
                            st.error(f"Failed to load model : {response.text}")
                    except Exception as e:
                        st.error(f"Error loading model : {str(e)}")

        elif model_provider == "Local LM Studio":
            st.header("Configure here the models you would like to use for the privacy threat modelling:")
            try:
                available_models = lms.list_downloaded_models()
            except Exception as e:
                if "LMStudioWebsocketError" in str(type(e)) or "LM Studio is not reachable" in str(e):
                    st.error("LM Studio is not reachable at ws://localhost:1234/system. Is LM Studio running?")
                    return
                else:
                    st.error(f"Unexpected error connecting to LM Studio: {str(e)}")
                    return
            st.markdown(
                """
                Local LM Studio is a feature that allows you to run the models on your own machine.\nTo use this feature, you need to have the models installed on your machine and running PILLAR locally.
                """)
            lmstudio_model = st.selectbox(
                "LM Studio model:",
                [model.model_key for model in filter(lambda x: isinstance(x, DownloadedLlm), available_models)],
                key="lmstudio_model_select"
            )
            if lmstudio_model != st.session_state.get("lmstudio_model"):
                st.session_state["lmstudio_model"] = lmstudio_model
            if st.button("Load", key="lmstudio_load"):
                try:
                    lms.llm(lmstudio_model)
                    st.session_state["lmstudio_loaded"] = True
                    st.session_state["lmstudio_model"] = lmstudio_model 
                    st.success(f"Successfully loaded {lmstudio_model} model")
                except Exception as e:
                    if "LMStudioWebsocketError" in str(type(e)) or "LM Studio is not reachable" in str(e) or "httpx.ConnectError" in str(e):
                        st.error("LM Studio is not reachable at ws://localhost:1234/system (due to httpx.ConnectError: All connection attempts failed). Is LM Studio running?")
                    else:
                        st.error(f"Unexpected error loading model in LM Studio: {str(e)}")
            # Show success message if model is already loaded
            if st.session_state.get("lmstudio_loaded") and st.session_state.get("lmstudio_model") == lmstudio_model:
                st.success(f"Successfully loaded {lmstudio_model} model")

        else:
            st.header("Configure here the API keys and models you would like to use for the privacy threat modelling:")
            llm_to_configure = st.selectbox(
                "Select LLM to configure:",
                model_options,
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
                        ["gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-4o"],
                        help="OpenAI have moved to continuous model upgrades so `gpt-4` and `gpt-4-turbo` point to the latest available version of each model.",
                    )
                    if openai_model != st.session_state["openai_model"]:
                        st.session_state["openai_model"] = openai_model
                if llm_to_configure == "Google AI API":
                    google_model = st.selectbox(
                        "Google AI model:",
                        ["gemini-1.5-pro-latest","gemini-2.0-flash-lite","gemini-2.0-flash","gemini-2.5-flash-preview-05-20"],
                    )
                    if google_model != st.session_state["google_model"]:
                        st.session_state["google_model"] = google_model
                if llm_to_configure == "Mistral API":
                    mistral_model = st.selectbox(
                        "Mistral model:",
                        ["mistral-large-latest", "mistral-small-latest"],
                    )
                    if mistral_model != st.session_state["mistral_model"]:
                        st.session_state["mistral_model"] = mistral_model

        st.markdown("""---""")
        
        # Global temperature setting for the LLM interactions
        st.slider("Temperature setting", 0.0, 1.0, 0.7, key="temperature", help="The randomness of the model's responses. Lower values lead to more deterministic answers, higher values make the model more creative, but also more prone to hallucination.")

        st.markdown("""---""")
        
        st.markdown("""
            Star on GitHub: [![Star on
            GitHub](https://img.shields.io/github/stars/stfbk/PILLAR?style=social)](https://github.com/stfbk/PILLAR)
            """)

        # About section
        st.header("About")
        st.markdown(
            """
        Welcome to P.I.L.L.A.R., an AI-powered tool designed to help developers
        in privacy threat modelling for their applications, using the [LINDDUN](https://linddun.org/) methodology.
        P.I.L.L.A.R. is an acronym for:

        **P**rivacy risk **I**dentification with **L**INDDUN and **L**LM **A**nalysis **R**eport
        
        """
        )
        st.markdown(
            """
        Privacy threat modelling is a key activity in the software development
        lifecycle, but is often overlooked or poorly executed. PILLAR aims
        to help teams produce more comprehensive threat models by
        leveraging the power of Large Language Models (LLMs) to generate a
        threat list for an application based on the details provided, analyzing threats
        specified by the LINDDUN scheme. To do so, PILLAR supports three variants of
        LINDDUN privacy threat modeling, i.e. SIMPLE, LINDDUN GO and LINDDUN PRO, to generate a list
        of threats based on the application's Data Flow Diagram and description. Once
        the threat list has been generated, PILLAR allows users to analyze each
        threat individually, generating control measures and assessing the impact of
        each threat. Finally, users can complete the privacy threat modeling process by
        downloading a complete report of the privacy threat modeling and risk
        assessment, which allows for a subsequent improvement of the application's
        privacy protection. For a detailed description of PILLAR, its methodology, and evaluation, 
        see our [paper](https://github.com/stfbk/PILLAR/blob/master/papers/PILLAR-IWPE25.pdf) 
        presented at the IWPE25.

        ---
        """
        )

        # Example application description, to help users get started trying out the tool
        st.header("Example Application Description")
        st.markdown(
            "Below is an example application description that you can use to test PILLAR:"
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
    


        # FAQ section
        st.header("FAQs")
        st.markdown(
            """
        ### **What is LINDDUN?**
        [LINDDUN](https://linddun.org/) is a privacy threat modeling methodology that helps developers
        identify and mitigate privacy risks in their applications, similar to
        the STRIDE security threat modeling methodology. The LINDDUN acronym
        stands for Linking, Identifying, Non-repudiation, Detecting, Data
        disclosure, Unawareness and unintervenability, and Non-compliance.
        PILLAR uses the LINDDUN methodology to generate threat models for
        applications.
        """
        )
        st.markdown(
            """
        ### **How does PILLAR work?**
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
        No, PILLAR does not store your application description or other
        details. All entered data is deleted after you close the browser tab.
        Of course, to query the LLM, a request containing the data is sent to
        the respective API provider, and they may store the request data
        according to their privacy policies.
        """
        )
        st.markdown(
            """
        ### **Why does it take so long to generate a threat model?**
        Since PILLAR uses Large Language Models (LLMs) to generate threat
        models, the process can take some time, especially for complex
        applications. The time taken depends on the complexity of the
        application, the model provider, and the model used. Also, some
        functionalities of PILLAR take more than others, such as the
        multi-agent LINDDUN Go. Please be patient while the model generates the
        threat model.
        """
        )
        st.markdown(
            """
        ### **Are the threat models 100% accurate?**
        No, the threat models are not 100% accurate. PILLAR uses Large
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