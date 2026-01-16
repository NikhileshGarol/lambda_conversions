from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

class DhaChartRequest(BaseModel):
    mobile_number: str
    date: Optional[str] = None