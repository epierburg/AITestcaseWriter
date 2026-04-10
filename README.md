# AI Testcase Agent Connector

A lightweight Python-based connector service for generating test cases from Excel inputs and GitHub repository assets.

## Features

- REST API backend for any external UI or client
- Excel sheet parsing via `openpyxl`
- GitHub repo cloning and repository asset access
- Validator config loading from repo location
- Optional OpenAI integration for test-case generation
- Output written back to repository or returned as generated content

## Quick Start

1. Create a Python virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the service:

```powershell
python main.py
```

3. Access the web interface at `http://localhost:8000/ui` or use the API.

## Environment Variables

- `OPENAI_API_KEY` — optional, used for real AI generation when available

## Optional AI Integration

- Install the OpenAI client when you want real LLM-generated test cases:

```powershell
pip install openai
```

- Then set `OPENAI_API_KEY` before starting the service.

## Web Interface

Visit `http://localhost:8000/ui` for a user-friendly form with:

- **Example Framework Repo URL** (optional): GitHub repo with working test cases for reference.
- **Testcase Validator Repo URL**: GitHub repo with validation rules.
- **Validator Config File**: Select or enter the YAML config file (e.g., validator.yaml).
- **Output Location**: Path in the validator repo for saving generated test cases.
- **GitHub Token** (optional): For private repos.
- **Excel Spec Sheet**: Upload Excel file with requirements.
- **Excel Directive**: Instructions on how to use the Excel data.
- **Single Prompt Input**: Additional guidance for generation.
- **Requirements Text**: Manual entry as alternative to Excel.

## API Endpoints

- `GET /` - Homepage with links
- `GET /health` - Health check
- `GET /ui` - Web interface
- `POST /generate-testcases` - API for programmatic access

### POST /generate-testcases Parameters

- `github_repo_url` (string): URL of the repo with validator config
- `validator_path` (optional): Path to config file (default: validator.yaml)
- `testcase_output_path` (optional): Output path (default: generated_testcases.md)
- `github_token` (optional): Auth token
- `excel_file` (file): Excel upload

## Notes

- The service is designed as a reusable connector. External UIs can integrate with it through standard HTTP calls.
- If no OpenAI key is configured, a safe local stub generates structured test-case output.

## Notes

- The service is designed as a reusable connector. External UIs can integrate with it through standard HTTP calls.
- If no OpenAI key is configured, a safe local stub generates structured test-case output.
