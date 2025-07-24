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
import pdfkit
import urllib.parse
import graphviz
import os
import platform
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

    col1, col2 = st.columns([1, 1])
    with col1:
        st.text_input("Application name", help="Enter the name of the application.", key="app_name")
        st.text_input("Author", help="Enter the name of the author.", key="author")
        st.text_area("High-level description (optional)", help="Enter a high-level description of the application, if you want to include it in the report.", key="high_level_description")
        st.checkbox("Include DFD graph in the report", help="Include the Data Flow Diagram in the report.", key="include_graph")
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
    except OSError as e:
        if "wkhtmltopdf" in str(e):
            st.error("""
            **PDF Generation Failed: wkhtmltopdf not installed**
            
            To generate PDF reports, you need to install wkhtmltopdf on your system:
            
            **Windows:**
            1. Download the installer from: https://wkhtmltopdf.org/downloads.html
            2. Run the installer and follow the setup wizard
            3. Restart this application
            
            **macOS:**
            ```bash
            brew install wkhtmltopdf
            ```
            
            **Linux (Ubuntu/Debian):**
            ```bash
            sudo apt-get install wkhtmltopdf
            ```
            
            **Linux (CentOS/RHEL):**
            ```bash
            sudo yum install wkhtmltopdf
            ```
            
            For detailed installation instructions, visit: https://github.com/JazzCore/python-pdfkit/wiki/Installing-wkhtmltopdf
            """)
        else:
            st.error(f"Error generating PDF: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error generating report: {str(e)}")
    
def generate_report():
    """
    This function generates the PDF report based on the information provided by the user.
    Returns:
        PDF file: The PDF file with the report.
    """
    try:
        # Try to find wkhtmltopdf automatically
        wkhtmltopdf_path = find_wkhtmltopdf()
        
        # Start the markdown text with the general information
        text="""# Privacy Threat Modeling and Risk Assessment Report\n"""
        text += "## Report Details \n\n"
        
        # Make this into a variable, because it is later used in the replace function to add CSS styles to the table
        description_message = "High-level Description"

        # Add the general information to the report as a table
        text += f"| | | | |\n"
        text += f"|------|-------|-----|-----|\n"
        text += f"| **Application Name** | {st.session_state['app_name']} | **Application Version** | {st.session_state['app_version']} |\n"
        text += f"| **Report author** | {st.session_state['author']} | **Date** | {st.session_state['date']} |\n"
        if st.session_state["high_level_description"]: # the high-level description is optional
            text += f"| **{description_message}** | {st.session_state['high_level_description']} | | |\n\n"
        else:
            text += f"\n\n"

            
            
        # if st.session_state["include_graph"] and st.session_state["is_graph_generated"]:
        if (st.session_state["include_graph"] and 
            st.session_state.get("input") and 
            st.session_state["input"].get("dfd") and 
            len(st.session_state["input"]["dfd"]) > 0):
            text+="## Data Flow Diagram\n\n"
            text+="The Data Flow Diagram (DFD) is a graphical representation of the data flow within the application. To reduce ambiguity, the labels are close to the **tail** of the arrow they refer to.\n\n"
            
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
        
        # Add the threats found with the selected methodology to the report
        if st.session_state["threat_source"] == "threat_model":
            text = from_threat_model(text)
        elif st.session_state["threat_source"] == "linddun_go":
            text = from_linddun_go(text)
        elif st.session_state["threat_source"] == "linddun_pro":
            text = from_linddun_pro(text)
        
        # Convert the markdown text to HTML
        html = markdown.markdown(text, extensions=["markdown.extensions.tables"])
        
        
        
        column_widths = [10, 40, 10, 40]
        colgroup_html = "<colgroup>" + "".join([f"<col style='width: {width}%;'>" for width in column_widths]) + "</colgroup>"
        html = html.replace("<table>", f"<table table-layout='fixed'>{colgroup_html}", 1)
        html = html.replace(f"<td><strong>{description_message}</strong></td>\n<td>{st.session_state['high_level_description']}</td>\n<td></td>\n<td></td>", 
                            f"<td><strong>{description_message}</strong></td>\n<td colspan='3'>{st.session_state['high_level_description']}</td>\n", 1)


        # Add the CSS styles to the HTML
        html_with_style = f"""
    <html>
    <head>
    <style type="text/css">
    body {{
        font-family: {st.session_state["font"]};
        font-size: {st.session_state["font_size"]}px;
    }}
    table {{
        width: 100%;
    }}
    table, th, td {{
        border: 1px solid black;
        border-collapse: collapse;
    }}
    th, td {{
        padding: 10px;
        text-align: left;
    }}
    th {{
        background-color: #f2f2f2;
    }}
    </style>
    </head>
    <body>
        {colgroup_html}
        {html}
    </body>
    </html>
        """
        
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
        }

        # Configure pdfkit with the found path if available
        config = None
        if wkhtmltopdf_path:
            import pdfkit
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        # Generate the PDF report with the styled HTML content and the specified options
        if config:
            return pdfkit.from_string(html_with_style, False, options=options, configuration=config)
        else:
            return pdfkit.from_string(html_with_style, False, options=options)
        
    except OSError as e:
        if "wkhtmltopdf" in str(e):
            raise OSError("wkhtmltopdf executable not found. Please install wkhtmltopdf to generate PDF reports.")
        else:
            raise e
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

def find_wkhtmltopdf():
    """
    Try to find wkhtmltopdf executable in common installation paths
    """
    system = platform.system().lower()
    
    if system == "windows":
        # Common Windows installation paths
        common_paths = [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\wkhtmltopdf\bin\wkhtmltopdf.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
    elif system == "darwin":  # macOS
        common_paths = [
            "/usr/local/bin/wkhtmltopdf",
            "/opt/homebrew/bin/wkhtmltopdf",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
    elif system == "linux":
        common_paths = [
            "/usr/bin/wkhtmltopdf",
            "/usr/local/bin/wkhtmltopdf",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    return None

