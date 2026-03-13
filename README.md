# Do AI-Generated Patches Require Less Maintenance Effort Than Human-Written Patches?

This repository contains the code, scripts, dataset artifacts, and
experimental results used to compare the maintenance effort of
AI-generated patches and human-written patches.

The study evaluates patch-level characteristics using bug instances from
the SWE-bench dataset and measures metrics that approximate maintenance
effort in software maintenance tasks.

The objective of the project is to investigate whether patches generated
by large language models (LLMs) require less maintenance effort compared
to patches written by human developers.

------------------------------------------------------------------------

# Repository Structure

FinalProject │ ├── data │ ├── patches │ │ ├── ai \# AI-generated patches
│ │ └── human \# Human developer patches │ │ │ └── swebench_bugs │ └──
bug_details.csv \# SWE-bench bug metadata │ ├── outputs │ ├──
Codellama_AllPatches │ ├── Codellama_AllPatches-Modified-clear │ ├──
Codellama_AllPatches-Modified-un │ ├── Ai_Patch_metrics.csv │ └──
Human_bug_metrics.csv │ ├── repos │ ├── django │ ├── pytest │ └──
requests │ ├── scripts │ ├── Collect_Human_Patch.py │ └──
Generate_AI_Patch.py │ ├── README.md └── .gitignore

------------------------------------------------------------------------

# Dataset

This study uses bug instances from the SWE-bench dataset:

princeton-nlp/SWE-bench

Selected bugs come from the following open-source Python repositories:

-   django/django
-   pytest-dev/pytest
-   psf/requests

A total of 16 bug instances are used in the experiment.

Bug metadata such as bug ID, repository, description, and base commit
are stored in:

data/swebench_bugs/bug_details.csv

------------------------------------------------------------------------

# Human Patch Collection

Human-written patches are extracted using:

scripts/Collect_Human_Patch.py

This script: 1. Loads the SWE-bench dataset 2. Filters the selected bug
instances 3. Extracts the developer patch 4. Saves each patch as a
.patch file

Human patches are stored in:

data/patches/human

------------------------------------------------------------------------

# AI Patch Generation

AI-generated patches are produced using:

scripts/Generate_AI_Patch.py

The script generates patches by querying the CodeLlama 7B Instruct model
through a Hugging Face inference endpoint.

Patch generation process: 1. Load selected SWE-bench bugs 2. Extract
buggy code context 3. Build a prompt describing the bug 4. Query the
CodeLlama model 5. Generate a unified git diff patch 6. Validate and
store the generated patch

Generated patches are saved in:

data/patches/ai

------------------------------------------------------------------------

# Model Used

codellama/CodeLlama-7b-Instruct-hf

The model is accessed using a Hugging Face inference endpoint.

------------------------------------------------------------------------

# Environment Setup

Install dependencies:

pip install datasets requests

------------------------------------------------------------------------

# Hugging Face Configuration

Before generating AI patches set the environment variables.

Windows CMD:

set HF_TOKEN=your_huggingface_token set
CODELLAMA_ENDPOINT=https://your-endpoint-url

------------------------------------------------------------------------

# Cloning Required Repositories

Clone required repositories into the repos folder:

git clone https://github.com/django/django repos/django git clone
https://github.com/pytest-dev/pytest repos/pytest git clone
https://github.com/psf/requests repos/requests

These repositories are not included in GitHub to keep the project
lightweight.

------------------------------------------------------------------------

# Running the Experiment

Step 1 -- Collect Human Patches

python scripts/Collect_Human_Patch.py

Step 2 -- Generate AI Patches

python scripts/Generate_AI_Patch.py

------------------------------------------------------------------------

# Metrics and Results

Patch metrics approximating maintenance effort are stored in:

outputs/Ai_Patch_metrics.csv outputs/Human_bug_metrics.csv

Metrics include:

-   patch size
-   number of modified lines
-   number of affected files
-   other patch-level attributes related to maintenance effort

------------------------------------------------------------------------

# Research Context

This project explores whether AI-generated bug fixes require less
maintenance effort compared to human-written patches, helping understand
the role of large language models in automated software maintenance.
