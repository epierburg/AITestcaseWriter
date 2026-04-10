from excel_processor import parse_excel
from validator import load_validator_config
from agent import generate_testcases


def test_parse_excel(tmp_path):
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["id", "description"])
    sheet.append([1, "Verify login"])
    sheet.append([2, "Verify logout"])

    file_path = tmp_path / "cases.xlsx"
    workbook.save(file_path)

    parsed = parse_excel(file_path.read_bytes())
    assert len(parsed) == 2
    assert parsed[0]["description"] == "Verify login"


def test_load_validator_config(tmp_path):
    validator_path = tmp_path / "validator.yaml"
    validator_path.write_text("rules:\n  - login_required: true\n")

    config = load_validator_config(validator_path)
    assert config["rules"][0]["login_required"] is True


def test_agent_local_stub(tmp_path):
    requirements = [{"id": 1, "description": "Verify login"}]
    validator_config = {"rules": [{"login_required": True}]}
    result = generate_testcases(requirements, validator_config, tmp_path)
    assert "Generated Test Cases" in result
    assert "Verify login" in result
