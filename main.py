import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request

from agent import generate_testcases as generate_testcases_from_source, is_openai_enabled
from excel_processor import parse_excel
from github_client import clone_repo
from validator import load_validator_config

app = Flask(__name__)

def _sanitize_path_value(value: str | None, default: str) -> str:
    if not value:
        return default

    cleaned = value.strip().replace("\\", "/")
    cleaned = cleaned.replace("\r", "").replace("\n", "")
    cleaned = re.sub(r"/{2,}", "/", cleaned)

    match = re.match(r"^(.+?\.(?:ya?ml|json))", cleaned, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    return cleaned or default

@app.route("/", methods=["GET"])
def index():
    return """
    <html>
    <head><title>AI Testcase Agent Connector</title></head>
    <body>
        <h1>AI Testcase Agent Connector</h1>
        <p>Available endpoints:</p>
        <ul>
            <li><a href="/health">GET /health</a> - Health check</li>
            <li><a href="/ui">GET /ui</a> - Web interface for generating test cases</li>
            <li>POST /generate-testcases - Generate test cases (requires form data)</li>
        </ul>
        <p>Use a tool like Postman or curl to test the POST endpoint with:</p>
        <ul>
            <li>github_repo_url (string)</li>
            <li>validator_path (optional, default: validator.yaml)</li>
            <li>testcase_output_path (optional, default: generated_testcases.md)</li>
            <li>github_token (optional)</li>
            <li>excel_file (file upload)</li>
        </ul>
    </body>
    </html>
    """

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "service": "ai-testcase-agent"})

@app.route("/ui", methods=["GET", "POST"])
def ui():
    if request.method == "POST":
        print("/ui POST received")
        example_repo_url = request.form.get("example_repo_url")
        validator_repo_url = request.form.get("validator_repo_url")
        validator_config_file = _sanitize_path_value(request.form.get("validator_config_file"), "validator.yaml")
        output_location = _sanitize_path_value(request.form.get("output_location"), "generated_testcases.md")
        github_token = request.form.get("github_token")
        excel_file = request.files.get("excel_file")
        excel_directive = request.form.get("excel_directive", "").strip()
        single_prompt = request.form.get("single_prompt", "").strip()
        requirements_text = request.form.get("requirements_text", "").strip()

        if not validator_repo_url:
            return """
            <html>
            <head><title>Error</title>
            <style>body { font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }</style>
            </head>
            <body><h1>Error: Validator Repo URL is required</h1><a href='/ui'>Back</a></body>
            </html>
            """

        if not excel_file and not requirements_text:
            return """
            <html>
            <head><title>Error</title>
            <style>body { font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }</style>
            </head>
            <body><h1>Error: Either upload an Excel file or enter requirements text</h1><a href='/ui'>Back</a></body>
            </html>
            """

        temp_dir = Path(tempfile.mkdtemp(prefix="ai-testcase-agent-"))
        try:
            # Clone validator repo
            print("Cloning validator repo", validator_repo_url)
            validator_repo_dir = temp_dir / "validator_repo"
            validator_repo_dir.mkdir(parents=True, exist_ok=True)
            clone_repo(
                validator_repo_url,
                github_token,
                validator_repo_dir,
                sparse_paths=[validator_config_file],
            )
            print("Validator repo cloned to", validator_repo_dir)
            validator_config = load_validator_config(validator_repo_dir / validator_config_file)
            print("Loaded validator config from", validator_config_file)

            # Clone example repo if provided
            example_repo_dir = None
            if example_repo_url:
                example_repo_dir = temp_dir / "example_repo"
                example_repo_dir.mkdir(parents=True, exist_ok=True)
                clone_repo(example_repo_url, github_token, example_repo_dir, ignore_dirs=["testdata"])

            if excel_file:
                print("Parsing Excel file")
                file_bytes = excel_file.read()
                requirements = parse_excel(file_bytes)
                print(f"Parsed {len(requirements)} requirements from Excel")
            else:
                requirements = [{"description": line.strip()} for line in requirements_text.split("\n") if line.strip()]
                print(f"Parsed {len(requirements)} requirements from text input")

            print("Starting generation")
            output_text = generate_testcases_from_source(
                requirements=requirements,
                validator_config=validator_config,
                repo_path=validator_repo_dir,  # Use validator repo as base
                example_repo_path=example_repo_dir,
                excel_directive=excel_directive,
                single_prompt=single_prompt,
            )
            print("Generation complete: output length", len(output_text))

            lines = output_text.split('\n')
            test_case_lines = [line.strip() for line in lines if line.strip().startswith('# ')]
            num_test_cases = len(test_case_lines)
            test_case_names = [line[2:].strip() for line in test_case_lines]

            generated_file = validator_repo_dir / output_location
            generated_file.parent.mkdir(parents=True, exist_ok=True)
            generated_file.write_text(output_text, encoding="utf-8")

            return f"""
            <html>
            <head><title>Generated Test Cases</title>
            <style>
                body {{ font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: left; margin: 20px; }}
                h1, h2 {{ color: #ffffff; }}
                pre {{ background-color: #333; color: #fff; padding: 10px; text-align: left; max-width: 800px; margin: auto; }}
                a {{ color: #007bff; }}
            </style>
            </head>
            <body>
                <h1 style="text-align: center;">Test Cases Generated</h1>
                <p>Status: Success</p>
                <p>Generated path: {generated_file.relative_to(validator_repo_dir)}</p>
                <p>Source rows: {len(requirements)}</p>
                <p>Number of test cases: {num_test_cases}</p>
                <h2>Test Case Tracker</h2>
                <ul>
                {"".join(f"<li>{name} - Done <span style='color: green;'>✓</span></li>" for name in test_case_names)}
                </ul>
                <h2>Test Cases:</h2>
                <pre>{output_text}</pre>
                <a href='/ui'>Generate More</a>
            </body>
            </html>
            """
        except Exception as exc:
            return f"""
            <html>
            <head><title>Error</title>
            <style>body {{ font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }}</style>
            </head>
            <body><h1>Error: {str(exc)}</h1><a href='/ui'>Back</a></body>
            </html>
            """
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # GET: show form
    openai_status = "enabled" if is_openai_enabled() else "disabled - install openai package and set OPENAI_API_KEY"
    return """
    <html>
    <head><title>Generate Test Cases</title>
    <style>
        body { font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }
        h1 { color: #ffffff; }
        .form-wrapper { max-width: 700px; margin: 0 auto; text-align: left; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; }
        input, textarea { width: 100%%; padding: 8px; font-size: 16px; background-color: #333; color: #fff; border: 1px solid #555; }
        button { padding: 10px 20px; font-size: 18px; background-color: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        small { color: #ccc; }
    </style>
    </head>
    <body>
        <h1 style="text-align: center;">Generate Test Cases</h1>
        <p style="color: #ffcc00; text-align: center;">OpenAI status: %s</p>
        <div id="form-container" class="form-wrapper">
        <form method="post" enctype="multipart/form-data" onsubmit="showLoading()">
            <div class="form-group">
                <label>Example Framework Repo URL (optional):</label>
                <small>GitHub repo with working test cases (functions, classes) for the agent to reference.</small><br>
                <input type="text" name="example_repo_url">
            </div>
            <div class="form-group">
                <label>Testcase Validator Repo URL:</label>
                <small>GitHub repo with general rules for validation and feedback.</small><br>
                <input type="text" name="validator_repo_url" required>
            </div>
            <div class="form-group">
                <label>Validator Config File Path:</label>
                <small>Path to the YAML config file in the validator repo (e.g., rules.yaml or config/rules.yaml).</small><br>
                <input type="text" name="validator_config_file" value="rules.yaml" placeholder="e.g., config/rules.yaml">
            </div>
            <div class="form-group">
                <label>Output Location:</label>
                <small>Path in the validator repo where generated test cases will be saved.</small><br>
                <input type="text" name="output_location" value="generated_testcases.md">
            </div>
            <div class="form-group">
                <label>GitHub Token (optional):</label>
                <small>Personal access token for private repos or higher rate limits.</small><br>
                <input type="text" name="github_token">
            </div>
            <div class="form-group">
                <label>Upload Excel Spec Sheet:</label>
                <small>Excel file with requirements to be read.</small><br>
                <input type="file" name="excel_file" accept=".xlsx,.xls">
                <br><small>Directive for using the Excel sheet:</small><br>
                <input type="text" name="excel_directive" placeholder="e.g., Use column 'Description' for requirements">
            </div>
            <div class="form-group">
                <label>Single Prompt Input:</label>
                <small>Additional prompt to guide the test case generation.</small><br>
                <textarea name="single_prompt" rows="3" placeholder="Enter specific instructions..."></textarea>
            </div>
            <div class="form-group">
                <label>Or Enter Requirements (one per line):</label>
                <small>Alternative to Excel: enter requirements manually.</small><br>
                <textarea name="requirements_text" rows="10" placeholder="Requirement 1&#10;Requirement 2&#10;..."></textarea>
            </div>
            <button type="submit">Generate Test Cases</button>
        </form>
        </div>
        <div id="loading" style="display: none; text-align: center; color: #ffffff;">
            <h2>Generating Test Cases...</h2>
            <p>This may take a few moments depending on the repository size and AI processing.</p>
        </div>
        <script>
            function showLoading() {
                document.getElementById('form-container').style.display = 'none';
                document.getElementById('loading').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """ % openai_status

@app.route("/generate-testcases", methods=["POST"])
def generate_testcases():
    # Support both old and new parameter names for backward compatibility
    validator_repo_url = request.form.get("validator_repo_url") or request.form.get("github_repo_url")
    validator_config_file = _sanitize_path_value(
        request.form.get("validator_config_file") or request.form.get("validator_path"),
        "validator.yaml",
    )
    output_location = _sanitize_path_value(
        request.form.get("output_location") or request.form.get("testcase_output_path"),
        "generated_testcases.md",
    )
    example_repo_url = request.form.get("example_repo_url")
    github_token = request.form.get("github_token")
    excel_file = request.files.get("excel_file")
    excel_directive = request.form.get("excel_directive", "").strip()
    single_prompt = request.form.get("single_prompt", "").strip()
    requirements_text = request.form.get("requirements_text", "").strip()

    if not validator_repo_url:
        return jsonify({"error": "validator_repo_url or github_repo_url is required"}), 400

    if not excel_file and not requirements_text:
        return jsonify({"error": "Either excel_file or requirements_text is required"}), 400

    temp_dir = Path(tempfile.mkdtemp(prefix="ai-testcase-agent-"))
    try:
        # Clone validator repo
        validator_repo_dir = temp_dir / "validator_repo"
        validator_repo_dir.mkdir(parents=True, exist_ok=True)
        clone_repo(
            validator_repo_url,
            github_token,
            validator_repo_dir,
            sparse_paths=[validator_config_file],
        )
        validator_config = load_validator_config(validator_repo_dir / validator_config_file)

        # Clone example repo if provided
        example_repo_dir = None
        if example_repo_url:
            example_repo_dir = temp_dir / "example_repo"
            example_repo_dir.mkdir(parents=True, exist_ok=True)
            clone_repo(example_repo_url, github_token, example_repo_dir, ignore_dirs=["testdata"])

        if excel_file:
            file_bytes = excel_file.read()
            requirements = parse_excel(file_bytes)
        else:
            requirements = [{"description": line.strip()} for line in requirements_text.split("\n") if line.strip()]

        output_text = generate_testcases_from_source(
            requirements=requirements,
            validator_config=validator_config,
            repo_path=validator_repo_dir,
            example_repo_path=example_repo_dir,
            excel_directive=excel_directive,
            single_prompt=single_prompt,
        )

        generated_file = validator_repo_dir / output_location
        generated_file.parent.mkdir(parents=True, exist_ok=True)
        generated_file.write_text(output_text, encoding="utf-8")

        return jsonify({
            "status": "success",
            "generated_path": str(generated_file.relative_to(validator_repo_dir)),
            "testcases": output_text,
            "source_rows": len(requirements),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
