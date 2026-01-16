from __future__ import annotations
"""
Service layer for the appointment module.

Each function here:
- Builds a minimal API Gateway–like `event` object
- Calls the existing Lambda `lambda_handler`
- Normalises the response into a {status, body} dict for the routers

This keeps behaviour 1:1 with the deployed Lambda without touching its code.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Utility that dynamically loads a Lambda handler from a file path
from app.utils.lambda_loader import load_lambda_handler

# ------------------------------------------------------------------
# Runtime Path Configuration
# ------------------------------------------------------------------
# Resolve the project root directory dynamically
ROOT = Path(__file__).resolve().parents[2]

# Path to the original appointment Lambda source directory
APPOINTMENT_SRC = ROOT / "Revival365ai-appointment-module-1" / "src"

# Inject Lambda source directory into sys.path
# This ensures all internal Lambda imports continue to work
if str(APPOINTMENT_SRC) not in sys.path:
    sys.path.insert(0, str(APPOINTMENT_SRC))

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
APPOINTMENT_LAMBDA_PATH = (
    APPOINTMENT_SRC / "lambda_function.py"
)

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
appointment_lambda_handler = load_lambda_handler(
    lambda_file_path=APPOINTMENT_LAMBDA_PATH,
    module_name="appointment_lambda_module",
)

# ------------------------------------------------------------------
# Internal Lambda Invocation Helper
# ------------------------------------------------------------------


def _call_lambda(path: str, query: Dict[str, Any], body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Internal helper:
    - `path` becomes `rawPath` (used by the Lambda to route)
    - `query` becomes `queryStringParameters`
    - `body` (if provided) is JSON-encoded into the event's `body`
    """
    # Construct a minimal API Gateway–style event
    event: Dict[str, Any] = {
        "rawPath": path,
        "queryStringParameters": query,
    }

    # Serialize body payload if provided
    if body is not None:
        event["body"] = json.dumps(body)

    # Execute the Lambda handler
    result = appointment_lambda_handler(event, context=None)

    # Extract status code (default to 500 for safety)
    status = result.get("statusCode", 500)
    body_raw = result.get("body")

    # Lambda commonly returns JSON as a string;
    # decode it into a Python object for FastAPI
    if isinstance(body_raw, str):
        try:
            body_parsed = json.loads(body_raw)
        except json.JSONDecodeError:
            # Fallback for non-JSON payloads
            body_parsed = {"raw": body_raw}
    else:
        body_parsed = body_raw

    return {"status": status, "body": body_parsed}

# ------------------------------------------------------------------
# Public Service Functions (1:1 with Lambda Routes)
# ------------------------------------------------------------------


def list_doctor_events(calendar_id: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/appointment` – list doctor events for a given calendar/date."""
    return _call_lambda(
        path="/appointment",
        query={"calendar_id": calendar_id, "date": date},
    )


def get_free_slots(calendar_id: str, date: Optional[str], duration: Optional[int]) -> Dict[str, Any]:
    """Mirror `/slots/available` – get free slots for a calendar."""
    query: Dict[str, Any] = {"calendar_id": calendar_id}
    if date is not None:
        query["date"] = date
    if duration is not None:
        query["duration"] = str(duration)

    return _call_lambda(
        path="/slots/available",
        query=query,
    )


def create_calendar(calendar_id: str) -> Dict[str, Any]:
    """Mirror `/calendar` – create a Google Calendar with the given ID."""
    body = {"id": calendar_id}
    return _call_lambda(
        path="/calendar",
        query={},
        body=body,
    )


def create_appointment(calendar_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mirror `/create_appointment` – create an event for a selected slot.
    The `body` should include keys: start, end, title, description, date, patient_id.
    """
    return _call_lambda(
        path="/create_appointment",
        query={"calendar_id": calendar_id},
        body=body,
    )


def delete_appointment(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Mirror `/delete_appointment` – delete an existing appointment."""
    body = {"calendar_id": calendar_id, "event_id": event_id}
    return _call_lambda(
        path="/delete_appointment",
        query={},
        body=body,
    )


def list_patient_events(date: Optional[str], patient_id: Optional[str], calendar_id: Optional[str]) -> Dict[str, Any]:
    """Mirror `/patient_appointment` – list events for a given patient/date."""
    query = {
        "date": date,
        "patient_id": patient_id,
        "calendar_id": calendar_id,
    }
    return _call_lambda(
        path="/patient_appointment",
        query=query,
    )


def get_upcoming_events(hours: int, minutes: int, max_threads: int, count: Optional[int]) -> Dict[str, Any]:
    """Mirror `/upcoming_events` – scheduler endpoint."""
    query: Dict[str, Any] = {
        "hours": str(hours),
        "minutes": str(minutes),
        "max_threads": str(max_threads),
    }
    if count is not None:
        query["count"] = str(count)

    return _call_lambda(
        path="/upcoming_events",
        query=query,
    )


def set_availability(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mirror `/set_availability` – set available/unavailable days for a calendar.
    The body should match the Lambda's expected structure.
    """
    return _call_lambda(
        path="/set_availability",
        query={},
        body=body,
    )
