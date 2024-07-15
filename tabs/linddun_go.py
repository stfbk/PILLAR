import streamlit as st
from llms.linddun_go import (
    get_linddun_go,
    get_multiagent_linddun_go,
    linddun_go_gen_markdown,
)


def linddun_go():
    st.markdown("""
The [LINDDUN Go](https://linddun.org/go/) process enables teams to dynamically apply the
LINDDUN methodology to identify and assess privacy threats in real-time. This
interactive simulation guides the LLM through the steps of the LINDDUN Go
framework, asking questions about the application to elicit potential threats.
By simulating [this process](https://linddun.org/go-getting-started/), developers can quickly identify and address privacy
threats just by providing the description.
""")
    st.markdown("""---""")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        multiagent_linddun_go = st.checkbox("Use multiple LLM agents to simulate LINDDUN Go with a team of experts")
        rounds = st.slider("Number of rounds", 1, 5, 3, disabled=not multiagent_linddun_go)
        threats_to_analyze = st.slider("Number of threats to analyze", 1, 10, 3, disabled=not multiagent_linddun_go)
    with c2:
        linddun_go_submit_button = st.button(label="Simulate LINDDUN Go")
    
    if linddun_go_submit_button and st.session_state["input"]["app_description"]:
        inputs = st.session_state["input"]
        # Show a spinner while generating the attack tree
        with st.spinner("Answering questions..."):
            try:
                if st.session_state["model_provider"] == "OpenAI API":
                    if multiagent_linddun_go:
                        present_threats = get_multiagent_linddun_go(st.session_state["openai_api_key"], st.session_state["selected_model"], inputs, rounds, threats_to_analyze)
                    else:
                        present_threats = get_linddun_go(st.session_state["openai_api_key"], st.session_state["selected_model"], inputs)

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
            file_name="linddun_go_output.md",
            mime="text/markdown",
        )

    if linddun_go_submit_button and not st.session_state["input"]["app_description"]:
        st.error("Please enter your application details before submitting.")