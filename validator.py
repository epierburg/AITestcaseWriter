import json
from pathlib import Path
from typing import Any, Dict

import yaml


def load_validator_config(filepath: Path) -> Dict[str, Any]:
    if not filepath.exists():
        raise FileNotFoundError(f"Validator file not found: {filepath}")

    text = filepath.read_text(encoding="utf-8")
    if filepath.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if filepath.suffix.lower() == ".json":
        return json.loads(text)

    raise ValueError("Validator file must be YAML or JSON")
