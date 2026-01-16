from __future__ import annotations
"""
Service layer for the appointment module-2.

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
APPOINTMENT_SRC = ROOT / "Revival365-appointment-module2" / "src"

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
    module_name="appointment2_lambda_module",
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


def get_appointment(calendar_id: str, date: Optional[str]) -> Dict[str, Any]:
    return _call_lambda(
        path="/appointment",
        query={"calendar_id": calendar_id, "date": date} if date else {
            "calendar_id": calendar_id},
    )


def get_slots_available(calendar_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    return _call_lambda(
        path="/date_schedule",
        query={"calendar_id": calendar_id,
               "start_date": start_date, "end_date": end_date}
    )


def get_weekly_availability(calendar_id: str) -> Dict[str, Any]:
    return _call_lambda(
        path="/week_schedule",
        query={"calendar_id": calendar_id}
    )


def update_availability(body: Dict[str, Any]) -> Dict[str, Any]:
    return _call_lambda(
        path="/edit_availability",
        query={},
        body=body
    )


def set_yearly_availability(body: Dict[str, Any]) -> Dict[str, Any]:
    return _call_lambda(
        path="/year_schedule",
        query={},
        body=body
    )


def empty_calendar(calendar_id: str) -> Dict[str, Any]:
    return _call_lambda(
        path="/empty_calender",
        query={"calendar_id": calendar_id}
    )
