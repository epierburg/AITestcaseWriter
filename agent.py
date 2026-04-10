import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import openai
except ImportError:
    openai = None


def _build_prompt(requirements: List[Dict[str, Any]], validator_config: Dict[str, Any], repo_path: Path, example_repo_path: Optional[Path], excel_directive: str, single_prompt: str) -> str:
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
    ]

    if example_repo_path:
        prompt_lines.append("Example Framework Repository:")
        prompt_lines.append(str(example_repo_path))
        prompt_lines.append("Use the working test cases in this repo as reference for viable test case structures.")
        prompt_lines.append("")

    if excel_directive:
        prompt_lines.append("Excel Directive:")
        prompt_lines.append(excel_directive)
        prompt_lines.append("")

    if single_prompt:
        prompt_lines.append("Additional Instructions:")
        prompt_lines.append(single_prompt)
        prompt_lines.append("")

    prompt_lines.append("Requirements:")

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
        request_timeout=60,
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


def is_openai_enabled() -> bool:
    return os.environ.get("OPENAI_API_KEY") is not None and openai is not None


def generate_testcases(requirements: List[Dict[str, Any]], validator_config: Dict[str, Any], repo_path: Path, example_repo_path: Optional[Path] = None, excel_directive: str = "", single_prompt: str = "") -> str:
    prompt = _build_prompt(requirements, validator_config, repo_path, example_repo_path, excel_directive, single_prompt)
    if os.environ.get("OPENAI_API_KEY") and openai is not None:
        try:
            print("Using OpenAI for test case generation.")
            return _openai_generate(prompt)
        except Exception as exc:
            print("OpenAI failed, falling back to local stub:", exc)
            return _local_stub(requirements, validator_config)

    if os.environ.get("OPENAI_API_KEY") and openai is None:
        print("OPENAI_API_KEY is set, but openai package is not installed. Using local stub.")
    else:
        print("Using local stub for test case generation.")
    return _local_stub(requirements, validator_config)
