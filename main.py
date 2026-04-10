import shutil
import tempfile
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request

from agent import generate_testcases as generate_testcases_from_source
from excel_processor import parse_excel
from github_client import clone_repo
from validator import load_validator_config

app = Flask(__name__)

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
        github_repo_url = request.form.get("github_repo_url")
        validator_path = request.form.get("validator_path", "validator.yaml")
        testcase_output_path = request.form.get("testcase_output_path", "generated_testcases.md")
        github_token = request.form.get("github_token")
        excel_file = request.files.get("excel_file")
        requirements_text = request.form.get("requirements_text", "").strip()

        if not github_repo_url:
            return """
            <html>
            <head><title>Error</title>
            <style>body { font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }</style>
            </head>
            <body><h1>Error: GitHub repo URL is required</h1><a href='/ui'>Back</a></body>
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
            repo_dir = temp_dir / "repo"
            repo_dir.mkdir(parents=True, exist_ok=True)

            clone_repo(github_repo_url, github_token, repo_dir)
            validator_config = load_validator_config(repo_dir / validator_path)

            if excel_file:
                file_bytes = excel_file.read()
                requirements = parse_excel(file_bytes)
            else:
                # Parse requirements_text as simple list
                requirements = [{"description": line.strip()} for line in requirements_text.split("\n") if line.strip()]

            output_text = generate_testcases_from_source(
                requirements=requirements,
                validator_config=validator_config,
                repo_path=repo_dir,
            )

            generated_file = repo_dir / testcase_output_path
            generated_file.parent.mkdir(parents=True, exist_ok=True)
            generated_file.write_text(output_text, encoding="utf-8")

            return f"""
            <html>
            <head><title>Generated Test Cases</title>
            <style>
                body {{ font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }}
                h1, h2 {{ color: #ffffff; }}
                pre {{ background-color: #333; color: #fff; padding: 10px; text-align: left; max-width: 800px; margin: auto; }}
                a {{ color: #007bff; }}
            </style>
            </head>
            <body>
                <h1>Test Cases Generated</h1>
                <p>Status: Success</p>
                <p>Generated path: {generated_file.relative_to(repo_dir)}</p>
                <p>Source rows: {len(requirements)}</p>
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
    return """
    <html>
    <head><title>Generate Test Cases</title>
    <style>
        body { font-family: Arial; font-size: 18px; background-color: #121212; color: #ffffff; text-align: center; margin: 20px; }
        h1 { color: #ffffff; }
        .form-group { margin: 20px 0; max-width: 600px; margin-left: auto; margin-right: auto; text-align: left; }
        label { display: block; margin-bottom: 5px; }
        input, textarea { width: 100%; padding: 8px; font-size: 16px; background-color: #333; color: #fff; border: 1px solid #555; }
        button { padding: 10px 20px; font-size: 18px; background-color: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        small { color: #ccc; }
    </style>
    </head>
    <body>
        <h1>Generate Test Cases</h1>
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label>GitHub Repo URL:</label>
                <small>The URL of the GitHub repository containing the validator config.</small><br>
                <input type="text" name="github_repo_url" required>
            </div>
            <div class="form-group">
                <label>Validator Path (optional):</label>
                <small>Path to the validator config file in the repo (default: validator.yaml).</small><br>
                <input type="text" name="validator_path" value="validator.yaml">
            </div>
            <div class="form-group">
                <label>Testcase Output Path (optional):</label>
                <small>Path where generated test cases will be saved in the repo (default: generated_testcases.md).</small><br>
                <input type="text" name="testcase_output_path" value="generated_testcases.md">
            </div>
            <div class="form-group">
                <label>GitHub Token (optional):</label>
                <small>Personal access token for private repos or higher rate limits.</small><br>
                <input type="text" name="github_token">
            </div>
            <div class="form-group">
                <label>Upload Excel File:</label>
                <small>Excel file with requirements (columns will be parsed as key-value pairs).</small><br>
                <input type="file" name="excel_file" accept=".xlsx,.xls">
            </div>
            <div class="form-group">
                <label>Or Enter Requirements (one per line):</label>
                <small>Alternative to Excel: enter requirements manually, one per line.</small><br>
                <textarea name="requirements_text" rows="10" placeholder="Requirement 1&#10;Requirement 2&#10;..."></textarea>
            </div>
            <button type="submit">Generate Test Cases</button>
        </form>
    </body>
    </html>
    """

@app.route("/generate-testcases", methods=["POST"])
def generate_testcases():
    github_repo_url = request.form.get("github_repo_url")
    validator_path = request.form.get("validator_path", "validator.yaml")
    testcase_output_path = request.form.get("testcase_output_path", "generated_testcases.md")
    github_token = request.form.get("github_token")
    excel_file = request.files.get("excel_file")

    if not github_repo_url or excel_file is None:
        return jsonify({"error": "github_repo_url and excel_file are required"}), 400

    temp_dir = Path(tempfile.mkdtemp(prefix="ai-testcase-agent-"))
    try:
        repo_dir = temp_dir / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        clone_repo(github_repo_url, github_token, repo_dir)
        validator_config = load_validator_config(repo_dir / validator_path)

        file_bytes = excel_file.read()
        requirements = parse_excel(file_bytes)

        output_text = generate_testcases_from_source(
            requirements=requirements,
            validator_config=validator_config,
            repo_path=repo_dir,
        )

        generated_file = repo_dir / testcase_output_path
        generated_file.parent.mkdir(parents=True, exist_ok=True)
        generated_file.write_text(output_text, encoding="utf-8")

        return jsonify({
            "status": "success",
            "generated_path": str(generated_file.relative_to(repo_dir)),
            "testcases": output_text,
            "source_rows": len(requirements),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
