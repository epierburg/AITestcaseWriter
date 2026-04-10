from typing import Dict, List, Optional

from pydantic import BaseModel


class GenerateTestcasesResponse(BaseModel):
    status: str
    generated_path: str
    testcases: str
    source_rows: int
