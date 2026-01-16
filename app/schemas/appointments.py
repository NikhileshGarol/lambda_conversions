from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class CreateCalendarRequest(BaseModel):
    """Request body for creating a Google Calendar with a given ID."""

    id: str


class CreateAppointmentBody(BaseModel):
    """Body fields needed to create an appointment from a free slot."""

    start: str
    end: str
    title: str
    description: str
    date: str
    patient_id: Optional[str] = "Unknown"


class DeleteAppointmentRequest(BaseModel):
    """Body for deleting an existing appointment."""

    calendar_id: str
    event_id: str


class AvailabilityDay(BaseModel):
    """Single day's availability definition."""

    date: str
    # The original Lambda accepts either a list of slots or the string "not available"
    available_slots: Optional[List[str] | str] = None


class Slot(BaseModel):
    start: str
    end: str
    duration: int

class DayAvailability(BaseModel):
    date: str
    available_slots: List[Slot]

class AvailabilityRequest(BaseModel):
    calendar_id: str
    availability: List[DayAvailability]