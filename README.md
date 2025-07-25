# P.I.L.L.A.R.

<img src="images/logo1.png" width="200" height="245" />


**P.I.L.L.A.R.** (Privacy risk Identification with LINDDUN and LLM Analysis
Report) is a tool which helps developers to identify privacy threats in their
software. It uses the [LINDDUN](https://linddun.org/) methodology executed by
Large Language Models (LLMs) to identify privacy threats given the description
of the application to analyze or its Data Flow Diagram (DFD). Once privacy
threats have been elicited, P.I.L.L.A.R. offers the possibility to assess their
impact and suggest control measures, based on the [privacy
patterns](https://privacypatterns.org/) website. Finally, users can download a
report of their privacy threat modeling. 

The tool is designed to be used by developers and security analysts to easily
evaluate the privacy risks of their software and take the necessary actions to
mitigate them, offering a good starting point for privacy analysis.


## Installation

To install the project, you need to clone the repository and install the
dependencies. You can do this by running the following commands:

```bash 
git clone https://github.com/stfbk/PILLAR.git 
cd PILLAR 
pip install -r requirements.txt 
streamlit run main.py 
```

## Usage

To use the tool, follow the instructions on the web interface. You will need
API keys of some LLM providers to use the tool, especially an OpenAI API key,
as some features only work with it (for now). You can find more information on
how to get an API key in the [OpenAI
website](https://platform.openai.com/account/api-keys). Other supported LLM
providers are [MistralAI](https://console.mistral.ai/api-keys) and [Google
Gemini](https://makersuite.google.com/app/apikey). 

### Using Local Models

**PILLAR** also supports local models through Ollama and LM Studio. To enable these options:

1. In the `sidebar.py` file, uncomment the local model options in the `model_options` list.

2. Alternatively, create a `.streamlit/secrets.toml` file to control which local models are available.  
   The absence of `disable_local_lm_studio` and `disable_local_ollama` settings will enable these providers.

For Ollama, you'll need to set up an SSH tunnel if using a remote instance.
For LM Studio, you need to have it installed and running locally with models downloaded.



## Features

- **Application Description**: Provide a natural language description of your
application, specifying the type (e.g., mobile app, web app), the data it
collects, and the data policy.
- **Data Flow Diagram (DFD) Management**: Upload, edit, generate from an image
or description, and download a Data Flow Diagram (DFD) of the application to 
identify privacy threats.
- **LINDDUN Analysis**: Perform a simple LINDDUN analysis of the application in
the SIMPLE tab.
- **LINDDUN GO Simulation**: Conduct a [LINDDUN
GO](https://linddun.org/linddun-go/) simulation for the application in the
LINDDUN GO tab, utilizing one or multiple LLM agents.
- **LINDDUN PRO Methodology**: Use the [LINDDUN
PRO](https://linddun.org/linddun-pro/) methodology with the provided DFD to
identify precise privacy threats in the LINDDUN PRO tab.
- **Impact Assessment and Control Measures**: Assess the impact of identified
privacy threats and suggest control measures based on the [privacy
patterns](https://privacypatterns.org/) website.
- **Report Generation**: Download a comprehensive report on the privacy threat
modeling of the application.


## Roadmap

Here’s an outline of our upcoming features and enhancements for **PILLAR**:

- [x] **Locally Hosted Models** by implementing support for locally hosted models, such as **Ollama** and **LM Studio**, to give users more control over privacy and security when running AI models.

- [x] **Enhanced DFD Management** by improving the DFD functionality to support multiple trust boundaries and manage them, color-coded visualization, and different graph functions.

- [ ] **Improve Risk Assessment Methodology and Control Suggestions** by integrating frameworks/methodologies in the state-of-the-art. 
 
- [ ] **Models' Performance Evaluation** by defining a comprehensive benchmarking methodology focused on measuring and comparing different LLMs' effectiveness in privacy threat modeling tasks.

- [ ] **Prompt Engineering Optimization** by experimenting with different prompt techniques, structures, and tactics to analyze their impact on threat elicitation accuracy, comprehensiveness, and overall performance across various threat elicitation variants in PILLAR. 

- [ ] **Support for Open Threat Modeling (OTM) Format** by adding the ability to export threat modeling results in the widely-adopted OTM format to enhance compatibility with other tools.



---


## Citation

If you use **PILLAR** in your research or project, please cite our [paper](https://arxiv.org/abs/2410.08755) as follows:

```bash
@inproceedings{pillar,
title={PILLAR: LINDDUN Privacy Threat Modeling using LLMs},
author={Mollaeefar, Majid, Bissoli, Andrea, Van Landuyt, Dimitri and Ranise, Silvio},
journal={International Workshop on Privacy Engineering (IWPE25)},
year={2025}
}
```


## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE.txt)
file for details.

## Contacts

This project is developed by [Andrea
Bissoli](https://www.linkedin.com/in/andrea-bissoli/) and [Majid
Mollaeefar](https://www.linkedin.com/in/majid-mollaeefar/) as an internship
project for [Fondazione Bruno Kessler](https://www.fbk.eu/). For any questions
or feedback, feel free to contact us.
