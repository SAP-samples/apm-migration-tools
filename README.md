<!--# SAP-samples/repository-template
This default template for SAP Samples repositories includes files for README, LICENSE, and .reuse/dep5. All repositories on github.com/SAP-samples will be created based on this template.

# Containing Files

1. The LICENSE file:
In most cases, the license for SAP sample projects is `Apache 2.0`.

2. The .reuse/dep5 file: 
The [Reuse Tool](https://reuse.software/) must be used for your samples project. You can find the .reuse/dep5 in the project initial. Please replace the parts inside the single angle quotation marks < > by the specific information for your repository.
3. The README.md file (this file):
Please edit this file as it is the primary description file for your project. You can find some placeholder titles for sections below.-->

# ![SAP Logo](https://github.com/user-attachments/assets/90192cd9-0330-4ae5-a24f-01991dd18af4)

# APM Migration Tools
<!-- Please include descriptive title -->

<!--- Register repository https://api.reuse.software/register, then add REUSE badge:
[![REUSE status](https://api.reuse.software/badge/github.com/SAP-samples/REPO-NAME)](https://api.reuse.software/info/github.com/SAP-samples/REPO-NAME)
-->

## Description
<!-- Please include SEO-friendly description -->
This repository contains a list of tools for migrating customers from PAI(PDMS) / ASPM to APM. Following are the list of available tools in this repository.

| Tool | PAI → APM | ASPM → APM |
| ----- | :---------: | :---------: |
| **Indicator** | ✔ | ✔ |
| **Alerts**    | ✔ | n/a |
| **Timeseries** | ✔ | n/a |

The tool is built using Python Scripting in Jupyter Notebooks for easier sequencing & execution of the migration steps.

## Requirements

* [Python](https://www.python.org/) version 3.12 or above
* [Jupyter](https://jupyter.org/) (or) [Visual Studio Code](https://code.visualstudio.com/)[^1][^2]
* [Git](https://git-scm.com/)[^3]

## Download and Installation

1. Ensure that all the necessary requirements stated above are installed & setup.
2. Clone the repository into your local machine.

   * Clone using `Git`[^3]

   ```bash
   git clone https://github.com/SAP-samples/apm-migration-tools.git
   cd apm-migration-tools
   ```

   * Download the repository from GitHub and extract by clicking [here](https://github.com/SAP-samples/apm-migration-tools/archive/refs/heads/main.zip)
  
3. Setup a **Python Virtual Environment** in the working (cloned or extracted) directory as follows:

* The following command creates a virtual environment named `.venv`. You are free to use any other text instead.

> **🪟 Windows**
>
> ```powershell
> python  -m venv .venv
> .venv/Scripts/activate
> pip install -r requirements.txt
> python -m ipykernel install --user --name=.venv
> ```
>
> **🐧 Linux**
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip3 install -r requirements.txt
> python -m ipykernel install --user --name=.venv
> ```
>
> **🍎 Mac OS**
>
> ```bash
> python3  -m venv .venv
> source .venv/bin/activate
> pip3 install -r requirements.txt
> python -m ipykernel install --user --name=.venv
> ```

## Execution

Navigate to the `/notebooks` directory. Notebooks specific to the tool may be executed in the specified sequence, individually either cell by cell (or using the Run All option). Detailed information regarding the tools and the steps are also linked for reference

|  |    |
| --------- | ------------- |
| **Indicators**| [Documentation](docs/indicator-migration.md)|
| 1 | `Indicators-01-Extract-Stage.ipynb` |  
| 2 | `Indicators-02-Transform-1-UDR-Generate.ipynb` |
| 3 | `Indicators-02-Transform-2-UDR-Load.ipynb` |
| 4 | `Indicators-03-Load-1-Sync.ipynb` |
| 5 | `Indicators-03-Load-2-Validate.ipynb` |
| 6 | `Indicators-03-Load-3-Data-Load.ipynb` |
| **Timeseries** |[Documentation](wrong_link.md)|
| 1 | `IOT-Extract-Time-Series-Data-From-IOT.ipynb` |  
| 2 | `IOT-Transform-Time-Series-Data-To-eIOT.ipynb` |
| **Alerts** |[Documentation](wrong_link.md)|
| 1 | `Alerts.ipynb` |  

## Known Issues
<!-- You may simply state "No known issues. -->
No known Issues

## How to obtain support

[Create an issue](https://github.com/SAP-samples/apm-migration-tools/issues) in this repository if you find a bug or have questions about the content.

## Contributing

If you wish to contribute code, offer fixes or improvements, please send a pull request. Due to legal reasons, contributors will be asked to accept a DCO when they create the first pull request to this project. This happens in an automated fashion during the submission process. SAP uses [the standard DCO text of the Linux Foundation](https://developercertificate.org/).

## License

Copyright (c) 2024 SAP SE or an SAP affiliate company. All rights reserved. This project is licensed under the Apache Software License, version 2.0 except as noted otherwise in the [LICENSE](LICENSE) file.

## References

### Citations

[^1]: Visual Studio Code needs to be enabled with Jupyter Extension Support to support the execution of Jupyter Notebook (.ipynb) files.
[^2]: The tools have been written and tested in Visual Studio Code. Any other IDE with Jupyter support may be used for execution.
[^3]: Installation of Git is optional. It is required only if the repository is being cloned using `terminal` or `command prompt` (or) if there are any enhancements to be done in the tool.
