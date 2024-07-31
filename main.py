import streamlit as st
import streamlit.components.v1 as components


from tabs.sidebar import sidebar
from tabs.application_info import application_info
from tabs.dfd import dfd
from tabs.threat_model import threat_model
from tabs.linddun_go import linddun_go
from tabs.linddun_pro import linddun_pro
from tabs.risk_assessment import risk_assessment
from tabs.report import report


# ------------------ Helper Functions ------------------ #


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

sidebar()

# ------------------ Main App UI ------------------ #

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Application info", "DFD", "Threat Model", "LINDDUN Go", "LINDDUN Pro", "Risk Assessment", "Report"],
)

with tab1:
    application_info()
        
with tab2:
    dfd()


with tab3:
    threat_model()

with tab4:
    linddun_go()

with tab5:
    linddun_pro()

with tab6:
    risk_assessment()

with tab7:
    report()