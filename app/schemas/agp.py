from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class AgpRequest(BaseModel):
    mobile_number: Optional[str] = None
    # start_date: Optional[str] = None
    # end_date: Optional[str] = None
