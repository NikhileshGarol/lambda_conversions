"""
FastAPI router for the DEV-Revival365-appointment-module-2 Lambda.

Each endpoint here mirrors one of the Lambda routes:
- /appointment
- /date_schedule
- /week_schedule
- /edit_availability
- /year_schedule
- /empty_calender

The actual business logic still lives in the original Lambda module; we reuse it
via the service layer so behaviour stays identical.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from fastapi import APIRouter, HTTPException, Query

# Request schemas used for payload validation and typing
from app.schemas.appointments2 import (
    AvailableSlotsRequest,
    UpdateAvailabilityRequest,
    YearlyAvailibilityRequest
)

# Service-layer functions that wrap the original Lambda handlers
from app.services.appointments2 import (
    get_appointment,
    get_slots_available,
    get_weekly_availability,
    update_availability,
    set_yearly_availability,
    empty_calendar
)

# Router configuration
# - prefix="" exposes routes at the root level
# - tags=["appointments"] groups endpoints in API documentation
router = APIRouter(prefix="", tags=["Appointments 2"])


@router.get("/appointment2")
async def get_all_appointment(
    calendar_id: str = Query(...,
                             description="Google Calendar ID for the doctor"),
    date: Optional[str] = Query(
        None, description="Filter events by date (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """Mirror the `/appointment` Lambda route – list events for a doctor."""
    result = get_appointment(calendar_id=calendar_id, date=date)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/date_schedule")
async def get_date_schedule_slots(calendar_id: str = Query(..., description="Google calendar ID for the doctor"),
                                  start_date: str = Query(
                                  ..., description="Get solts by given date range"),
                                  end_date: str = Query(..., description="Get solts by given date range")) -> Dict[str, Any]:
    """Mirror the /date_schedule Lambda route - available slots for appointements"""
    result = get_slots_available(
        calendar_id=calendar_id, start_date=start_date, end_date=end_date)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/weekly_available", response_model=List[Any])
async def weekly_available_slots(calendar_id: str = Query(..., description="Google calendar ID for the doctor")) -> Dict[str, Any]:
    """Mirror the /week_schedule Lambda route - Get weekly slots available """
    result = get_weekly_availability(calendar_id=calendar_id)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/upsert_availablity")
async def edit_availability_slots(payload: UpdateAvailabilityRequest) -> Dict[str, Any]:
    """Mirror the /edit_availability Lambda route - Upsert availability slots"""
    result = update_availability(body=payload.model_dump())
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.post("/year_schedule")
async def year_availability_slots(payload: YearlyAvailibilityRequest) -> Dict[str, Any]:
    """Mirror the /year_schedule Lambda route - Post availability slots yearly"""
    result = set_yearly_availability(body=payload.model_dump())
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.delete("/empty_calendar")
async def empty_all_events(calendar_id: str = Query(..., description="Google calendar ID for the doctor")) -> Dict[str, Any]:
    """Mirror the /empty_calender Lambda route - Delete all scheduled events"""
    result = empty_calendar(calendar_id=calendar_id)
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body
