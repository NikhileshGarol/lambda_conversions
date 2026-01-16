"""
FastAPI router for the DEV-Revival365-appointment-module-1 Lambda.

Each endpoint here mirrors one of the Lambda routes:
- /appointment
- /calendar
- /slots/available
- /create_appointment
- /delete_appointment
- /patient_appointment
- /upcoming_events
- /set_availability

The actual business logic still lives in the original Lambda module; we reuse it
via the service layer so behaviour stays identical.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

# Request schemas used for payload validation and typing
from app.schemas.appointments import (
    CreateAppointmentBody,
    CreateCalendarRequest,
    DeleteAppointmentRequest,
    AvailabilityRequest,
)

# Service-layer functions that wrap the original Lambda handlers
from app.services.appointments import (
    create_appointment,
    create_calendar,
    delete_appointment,
    get_free_slots,
    get_upcoming_events,
    list_doctor_events,
    list_patient_events,
    set_availability,
)

# Router configuration
# - prefix="" exposes routes at the root level
# - tags=["appointments"] groups endpoints in API documentation
router = APIRouter(prefix="", tags=["Appointments"])


@router.get("/appointment")
async def get_doctor_events(
    calendar_id: str = Query(...,
                             description="Google Calendar ID for the doctor"),
    date: Optional[str] = Query(
        None, description="Filter events by date (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """Mirror the `/appointment` Lambda route – list events for a doctor."""
    result = list_doctor_events(calendar_id=calendar_id, date=date)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/slots/available")
async def get_slots_available(
    calendar_id: str = Query(...,
                             description="Calendar ID to check free slots for"),
    date: Optional[str] = Query(
        None, description="Date to check (YYYY-MM-DD); defaults to next 7 days in Lambda"),
    duration: Optional[int] = Query(
        None, description="Slot duration in minutes; defaults to 60 in Lambda"),
) -> Dict[str, Any]:
    """Mirror `/slots/available` – get free slots grouped by day."""
    result = get_free_slots(calendar_id=calendar_id,
                            date=date, duration=duration)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/calendar")
async def post_create_calendar(payload: CreateCalendarRequest) -> Dict[str, Any]:
    """Mirror `/calendar` – create a Google Calendar with given ID."""
    result = create_calendar(calendar_id=payload.id)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/create_appointment")
async def post_create_appointment(
    payload: CreateAppointmentBody,
    calendar_id: str = Query(...,
                             description="Calendar ID in which to create the appointment"),
) -> Dict[str, Any]:
    """Mirror `/create_appointment` – create an event from a chosen free slot."""
    result = create_appointment(
        calendar_id=calendar_id, body=payload.model_dump())
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/delete_appointment")
async def post_delete_appointment(payload: DeleteAppointmentRequest) -> Dict[str, Any]:
    """Mirror `/delete_appointment` – delete an existing event."""
    result = delete_appointment(
        calendar_id=payload.calendar_id, event_id=payload.event_id)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/patient_appointment")
async def get_patient_appointment(
    date: Optional[str] = Query(
        None, description="Date of the appointment (YYYY-MM-DD)"),
    patient_id: Optional[str] = Query(None, description="Patient identifier"),
    calendar_id: Optional[str] = Query(
        None, description="Calendar ID associated with the patient"),
) -> Dict[str, Any]:
    """Mirror `/patient_appointment` – list events for a given patient and date."""
    result = list_patient_events(
        date=date, patient_id=patient_id, calendar_id=calendar_id)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/upcoming_events")
async def get_upcoming_events_route(
    hours: int = Query(0, description="Number of hours to look ahead"),
    minutes: int = Query(30, description="Number of minutes to look ahead"),
    max_threads: int = Query(
        30, description="Max parallel threads for scheduler"),
    count: Optional[int] = Query(None, description="Optional count limit"),
) -> Dict[str, Any]:
    """Mirror `/upcoming_events` – run the scheduler and return upcoming events."""
    result = get_upcoming_events(
        hours=hours,
        minutes=minutes,
        max_threads=max_threads,
        count=count,
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/set_availability")
async def post_set_availability(payload: AvailabilityRequest) -> Dict[str, Any]:
    """Mirror `/set_availability` – configure daily availability for a calendar."""
    result = set_availability(body=payload.model_dump())
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body
