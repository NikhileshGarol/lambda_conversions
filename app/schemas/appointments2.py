
from typing import List, Optional
from pydantic import BaseModel


class AvailableSlotsRequest(BaseModel):
    calendar_id: str
    start_date: str
    end_date: str


class Slot(BaseModel):
    start: str
    end: str
    duration: int


class DateAvailability(BaseModel):
    date: str
    available_slots: List[Slot]


class UpdateAvailabilityRequest(BaseModel):
    calendar_id: str
    availability_data: List[DateAvailability]


class YearlySlot(BaseModel):
    start: str
    end: str


class DayAvailability(BaseModel):
    day: str
    available_slots: List[YearlySlot]


class YearlyAvailibilityRequest(BaseModel):
    calendar_id: str
    availability_data: List[DayAvailability]
