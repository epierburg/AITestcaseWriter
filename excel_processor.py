from io import BytesIO
from typing import Any, Dict, List

import openpyxl


def parse_excel(excel_bytes: bytes) -> List[Dict[str, Any]]:
    workbook = openpyxl.load_workbook(BytesIO(excel_bytes), data_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(cell).strip() if cell is not None else f"column_{idx + 1}" for idx, cell in enumerate(rows[0])]
    parsed = []

    for row in rows[1:]:
        if not any(cell is not None for cell in row):
            continue
        item = {headers[idx]: row[idx] for idx in range(len(headers)) if headers[idx]}
        parsed.append(item)

    return parsed
