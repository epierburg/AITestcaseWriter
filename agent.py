import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import openai
except ImportError:
    openai = None


def _build_prompt(requirements: List[Dict[str, Any]], validator_config: Dict[str, Any], repo_path: Path) -> str:
    prompt_lines = [
        "You are an AI assistant that writes structured test cases.",
        "Use the following requirements from the Excel file and validator settings to generate test cases.",
        "",
        "Validator configuration:",
        str(validator_config),
        "",
        "Repository location:",
        str(repo_path),
        "",
        "Requirements:",
    ]

    for index, requirement in enumerate(requirements, start=1):
        prompt_lines.append(f"{index}. {requirement}")

    prompt_lines.append("")
    prompt_lines.append("Generate executable or markdown-formatted test cases clearly labeled and organized.")
    return "\n".join(prompt_lines)


def _openai_generate(prompt: str) -> str:
    if openai is None:
        raise RuntimeError("OpenAI package is not installed. Install 'openai' or omit OPENAI_API_KEY to use the local stub.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You generate software test cases."}, {"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _local_stub(requirements: List[Dict[str, Any]], validator_config: Dict[str, Any]) -> str:
    lines = ["# Generated Test Cases", ""]
    for index, requirement in enumerate(requirements, start=1):
        lines.append(f"## Test Case {index}")
        lines.append(f"- Requirement: {requirement}")
        lines.append("- Expected result: TBD")
        lines.append("- Validation rules: ")
        lines.append(f"  - {validator_config}")
        lines.append("")
    return "\n".join(lines)


def generate_testcases(requirements: List[Dict[str, Any]], validator_config: Dict[str, Any], repo_path: Path) -> str:
    prompt = _build_prompt(requirements, validator_config, repo_path)
    if os.environ.get("OPENAI_API_KEY") and openai is not None:
        try:
            return _openai_generate(prompt)
        except Exception:
            return _local_stub(requirements, validator_config)

    return _local_stub(requirements, validator_config)
