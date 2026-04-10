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

3. Call the API from any UI:

- POST `/generate-testcases`
- Send `github_repo_url`, `validator_path`, `testcase_output_path`, and file upload `excel_file`

## Environment Variables

- `OPENAI_API_KEY` — optional, used for real AI generation when available

## Optional AI Integration

- Install the OpenAI client when you want real LLM-generated test cases:

```powershell
pip install openai
```

- Then set `OPENAI_API_KEY` before starting the service.

## Example Request

Use a form-based upload to send an Excel file and GitHub repository URL.

## Notes

- The service is designed as a reusable connector. External UIs can integrate with it through standard HTTP calls.
- If no OpenAI key is configured, a safe local stub generates structured test-case output.
