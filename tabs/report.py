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
import streamlit.components.v1 as components
import base64
import markdown 
import urllib.parse
import graphviz
import os
from misc.utils import (
    match_color,
    match_number_color,
    match_letter,
    match_number_category,
    match_category_number,
)
from tabs.risk_assessment import measures_gen_markdown

def report():

    st.markdown("""
    In this tab you can download the complete report of the privacy threat modeling
    and risk assessment, after the previous steps have been completed. Just fill in
    the required general information and you will be able to download the PDF report.

    ---
    """)

    # Show warning for cloud environments about DFD limitations
    if is_cloud_environment() and not check_graphviz_available():
        st.warning("""
        **Cloud Environment Detected**: Graphical DFD rendering may not be available. 
        If PDF generation fails, try unchecking "Include DFD graph in the report" below 
        to generate a report with tabular DFD representation instead.
        """)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.text_input("Application name", help="Enter the name of the application.", key="app_name")
        st.text_input("Author", help="Enter the name of the author.", key="author")
        st.text_area("High-level description (optional)", help="Enter a high-level description of the application, if you want to include it in the report.", key="high_level_description")
        
        # Add additional help text for cloud environments
        dfd_help = "Include the Data Flow Diagram in the report."
        if is_cloud_environment():
            dfd_help += " Note: In cloud environments, this will show a tabular representation if graphical rendering is unavailable."
        
        st.checkbox("Include DFD graph in the report", help=dfd_help, key="include_graph")
    with col2:
        st.text_input("Application version", help="Enter the version of the application.", key="app_version")
        st.date_input("Date", key="date", help="Enter the date of the report.", format="YYYY/MM/DD")
        
        font_options = ["Arial", "Courier", "Times New Roman", "Verdana"]
        st.selectbox("Font face", options=font_options, key="font")
        st.slider("Font size", 8, 24, 16, key="font_size")
    
    if st.button("Download report", disabled=not (st.session_state.app_name and st.session_state.author and st.session_state.app_version and st.session_state.date)):
        download_file()

    

def download_file():
    """
    This function triggers the download of the PDF report, generating it just
    before. The download is done through a hidden HTML element that is
    triggered when the function is called.
    """
    try:
        file = generate_report()
        b64 = base64.b64encode(file).decode()

        download_html = f"""
        <html>
        <head>
        <title>Auto Download File</title>
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var link = document.createElement('a');
            link.href = 'data:application/pdf;base64,{b64}';
            link.download = 'report.pdf';
            link.click();
        }});
        </script>
        </head>
        </html>
        """

        components.html(
            download_html,
            height=0,
        )
    except Exception as e:
        error_msg = str(e)
        if "graphviz" in error_msg.lower() or ("dot" in error_msg and "failed to execute" in error_msg):
            st.error("""
            **PDF Generation Failed: Graphviz not available**
            
            This deployment environment doesn't have Graphviz installed, which is needed for DFD diagrams.
            
            **Solutions:**
            1. **Disable DFD diagrams**: Uncheck "Include DFD graph in the report" to generate a report with tabular DFD representation
            2. **For local deployment**: Install Graphviz from https://graphviz.org/download/
            3. **For cloud deployment**: Add Graphviz to your system requirements or use the tabular format
            """)
        else:
            st.error(f"Error generating PDF report: {error_msg}")
    
def generate_report():
    """
    This function generates the PDF report based on the information provided by the user.
    Returns:
        PDF file: The PDF file with the report.
    """
    try:
        # Build the Report Details table directly as HTML so xhtml2pdf renders it correctly
        details_html = """<h1>Privacy Threat Modeling and Risk Assessment Report</h1>
<h2>Report Details</h2>
<table style="width:100%; border-collapse:collapse;">
  <tr>
    <td style="width:15%; font-weight:bold; border:1px solid black; padding:8px;">Application Name</td>
    <td style="width:35%; border:1px solid black; padding:8px;">{app_name}</td>
    <td style="width:15%; font-weight:bold; border:1px solid black; padding:8px;">Application Version</td>
    <td style="width:35%; border:1px solid black; padding:8px;">{app_version}</td>
  </tr>
  <tr>
    <td style="font-weight:bold; border:1px solid black; padding:8px;">Report Author</td>
    <td style="border:1px solid black; padding:8px;">{author}</td>
    <td style="font-weight:bold; border:1px solid black; padding:8px;">Date</td>
    <td style="border:1px solid black; padding:8px;">{date}</td>
  </tr>{desc_row}
</table>
""".format(
            app_name=st.session_state['app_name'],
            app_version=st.session_state['app_version'],
            author=st.session_state['author'],
            date=st.session_state['date'],
            desc_row=(
                """
  <tr>
    <td style="font-weight:bold; border:1px solid black; padding:8px;">High-level Description</td>
    <td colspan="3" style="border:1px solid black; padding:8px;">{desc}</td>
  </tr>""".format(desc=st.session_state['high_level_description'])
                if st.session_state["high_level_description"] else ""
            ),
        )

        # Build the rest of the content as markdown and convert to HTML
        text = ""

            
            
        # if st.session_state["include_graph"] and st.session_state["is_graph_generated"]:
        if (st.session_state["include_graph"] and 
            st.session_state.get("input") and 
            st.session_state["input"].get("dfd") and 
            len(st.session_state["input"]["dfd"]) > 0):
            text+="## Data Flow Diagram\n\n"
            text+="The Data Flow Diagram (DFD) is a graphical representation of the data flow within the application. To reduce ambiguity, the labels are close to the **tail** of the arrow they refer to.\n\n"
            
            try:
                graph = graphviz.Digraph(engine='fdp', format='svg')
                graph.attr(
                    bgcolor="white",
                    overlap="false",
                    K="5",
                    start=st.session_state["graph_seed"],
                    splines="ortho",
                )
                graph.node_attr.update(
                    color="black",
                    fontcolor="black",
                )
                graph.edge_attr.update(
                    color="grey",
                    fontcolor="fuchsia",
                    arrowsize="0.5",
                )
                with graph.subgraph(name='cluster_0') as c:
                    c.attr(
                        color="#00a6fb",
                        label="Trusted",
                        fontcolor="#00a6fb",
                        style="dashed"
                    )
                    for object in st.session_state["input"]["dfd"]:
                        if object["trusted"]:
                            c.node(object["from"])
                        if object["trusted"]:
                            c.node(object["to"])
                for (i, object) in enumerate(st.session_state["input"]["dfd"]):
                    graph.node(object["from"], shape=f"{'box' if object['typefrom'] == 'Entity' else 'ellipse' if object['typefrom'] == 'Process' else 'cylinder'}")
                    graph.node(object["to"], shape=f"{{'box' if object['typeto'] == 'Entity' else 'ellipse' if object['typeto'] == 'Process' else 'cylinder'}}")
                    graph.edge(object["from"], object["to"], taillabel=f"DF{i}", constraint="false")

                # Add the graph to the report as an SVG image
                text += f"![Data Flow Diagram](data:image/svg+xml,{urllib.parse.quote(graph.pipe(encoding='utf-8'))})\n"
            except Exception as e:
                # If Graphviz fails (common in cloud deployments), provide a textual representation instead
                text += "**Note**: Graphical DFD rendering is not available in this deployment environment. Showing textual representation instead:\n\n"
                text += "| Data Flow | From | Type | To | Type | Trusted | Boundary |\n"
                text += "|-----------|------|------|----|----- |---------|----------|\n"
                for (i, object) in enumerate(st.session_state["input"]["dfd"]):
                    trusted_text = "Yes" if object.get("trusted", False) else "No"
                    boundary = object.get("boundary", "N/A")
                    text += f"| DF{i} | {object['from']} | {object['typefrom']} | {object['to']} | {object['typeto']} | {trusted_text} | {boundary} |\n"
                text += "\n"
        
        # Add the threats found with the selected methodology to the report
        if st.session_state["threat_source"] == "threat_model":
            text = from_threat_model(text)
        elif st.session_state["threat_source"] == "linddun_go":
            text = from_linddun_go(text)
        elif st.session_state["threat_source"] == "linddun_pro":
            text = from_linddun_pro(text)
        
        # Convert the markdown threat content to HTML
        threats_html = markdown.markdown(text, extensions=["markdown.extensions.tables"])

        # Add the CSS styles to the HTML
        html_with_style = f"""
    <html>
    <head>
    <style type="text/css">
    @page {{
        size: Letter;
        margin: 0.75in;
    }}
    body {{
        font-family: {st.session_state["font"]};
        font-size: {st.session_state["font_size"]}px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    table, th, td {{
        border: 1px solid black;
    }}
    th, td {{
        padding: 8px;
        text-align: left;
    }}
    th {{
        background-color: #f2f2f2;
    }}
    </style>
    </head>
    <body>
        {details_html}
        {threats_html}
    </body>
    </html>
        """
        
        # Generate the PDF report using xhtml2pdf (pure Python, no native dependencies)
        try:
            from xhtml2pdf import pisa
            import io
        except ImportError as e:
            raise OSError(f"xhtml2pdf is not installed. Run: pip install xhtml2pdf\nDetails: {e}")
        pdf_buffer = io.BytesIO()
        status = pisa.CreatePDF(html_with_style, dest=pdf_buffer)
        if status.err:
            raise Exception("xhtml2pdf reported errors during PDF generation.")
        return pdf_buffer.getvalue()

    except OSError:
        raise
    except Exception as e:
        raise Exception(f"Error generating PDF report: {str(e)}")


def from_threat_model(text):
    """
    This function generates the markdown text for the threats found with the simple threat model.
    """
    text += "## Threats found with the simple threat model\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat['title']}\n\n"
            color = match_color(threat["threat_type"])
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"
            text += f"**Category**: {color_html}{threat['threat_type']}</span>\n\n"
            text += f"**Reason for detection**: {threat['Reason']}\n\n"
            text += f"**Scenario**: {threat['Scenario']}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state['assessments'][i]['impact']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state['control_measures'][i])}\n\n"

    return text

def from_linddun_go(text):
    """
    This function generates the markdown text for the threats found with the LINDDUN Go methodology.
    """
    text += "## Threats found with the LINDDUN Go methodology\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat['threat_title']}\n\n"
            color = match_number_color(threat["threat_type"])
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"
            text += f"**Category**: {color_html}{match_letter(threat['threat_type'])} - {match_number_category(threat['threat_type'])}</span>\n\n"
            text += f"**Threat description**: {threat['threat_description']}\n\n"
            text += f"**Reason for detection**: {threat['reason']}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state['assessments'][i]['impact']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state['control_measures'][i])}\n\n"

    return text

def from_linddun_pro(text):
    """
    This function generates the markdown text for the threats found with the LINDDUN Pro methodology.
    """
    text += "## Threats found with the LINDDUN Pro methodology\n"
    for (i, threat) in enumerate(st.session_state["to_assess"]):
        if st.session_state["to_report"][i]:
            text += f"## Threat {i+1}: {threat['threat_title']}\n\n"
            color = match_number_color(match_category_number(threat["category"]))
            color_html = f"<span style='background-color:{color};color:#ffffff;'>"
            text += f"**Category**: {color_html}{match_letter(match_category_number(threat['category']))} - {threat['category']}</span>\n\n"
            text += f"**DFD edge**:         "
            # Underline the source, data flow, or destination node in the edge, depending on the threat location
            if threat["threat_location"] == "source":
                text += f"<u>{threat['edge']['from']}</u>, DF{threat['data_flow_number']}, {threat['edge']['to']}\n\n"
            elif threat["threat_location"] == "data_flow":
                text += f"{threat['edge']['from']}, <u>DF{threat['data_flow_number']}</u>, {threat['edge']['to']}\n\n"
            elif threat["threat_location"] == "destination":
                text += f"{threat['edge']['from']}, DF{threat['data_flow_number']}, <u>{threat['edge']['to']}</u>\n\n"
            text += f"**Threat tree involved nodes**: {threat['threat_tree_node']}\n\n"
            text += f"**Threat description**: {threat['description']}\n\n"
            if st.session_state["assessments"][i]["impact"]:
                text += f"**Impact assessment**: {st.session_state['assessments'][i]['impact']}\n\n"
            if st.session_state["control_measures"][i]:
                text += f"**Suggested control measures**: \n\n{measures_gen_markdown(st.session_state['control_measures'][i])}\n\n"

    return text

def is_cloud_environment():
    """
    Detect if running in a cloud environment like Streamlit Cloud
    """
    # Check for common cloud environment indicators
    cloud_indicators = [
        os.getenv('STREAMLIT_SHARING_MODE'),  # Streamlit Cloud
        os.getenv('HEROKU_APP_NAME'),         # Heroku
        os.getenv('VERCEL'),                  # Vercel
        os.getenv('NETLIFY'),                 # Netlify
        os.getenv('AWS_LAMBDA_FUNCTION_NAME') # AWS Lambda
    ]
    return any(indicator for indicator in cloud_indicators)

def check_graphviz_available():
    """
    Check if Graphviz is available on the system
    """
    try:
        import subprocess
        subprocess.run(['dot', '-V'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

