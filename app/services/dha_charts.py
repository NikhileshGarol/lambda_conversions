from __future__ import annotations
"""
Service layer for the DHA Charts module.

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
DHA_CHARTS_SRC = ROOT / "Revival365-DHA-charts" / "src"

# Inject Lambda source directory into sys.path
# This ensures all internal Lambda imports continue to work
if str(DHA_CHARTS_SRC) not in sys.path:
    sys.path.insert(0, str(DHA_CHARTS_SRC))

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
DHA_CHARTS_LAMBDA_PATH = (
    DHA_CHARTS_SRC / "lambda_function.py"
)

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
dha_charts_lambda_handler = load_lambda_handler(
    lambda_file_path=DHA_CHARTS_LAMBDA_PATH,
    module_name="dha_charts_lambda_module",
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
    result = dha_charts_lambda_handler(event, context=None)

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


def get_tir_trends(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/tir` – Fetching and processing of glucose data."""
    return _call_lambda(
        path="/tir",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_fbg_trends(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/fbs` – Fetching and processing of fbs data."""
    return _call_lambda(
        path="/fbs",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_mean_gluc_trends(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/mean_gluc` – Fetching and processing of mean_gluc data."""
    return _call_lambda(
        path="/mean_gluc",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_meal_spikes_trends(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/meal_spikes` – Fetching and processing of meal_spikes data."""
    return _call_lambda(
        path="/meal_spikes",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_nauc_trends(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/nauc` – Fetching and processing of nauc data."""
    return _call_lambda(
        path="/nauc",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_dips_day(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/dips_day` – Fetching and processing of dips_day data."""
    return _call_lambda(
        path="/dips_day",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_dips_night(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/dips_night` – Fetching and processing of dips_night data."""
    return _call_lambda(
        path="/dips_night",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_spikes_day(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/spikes_day` – Fetching and processing of spikes_day data."""
    return _call_lambda(
        path="/spikes_day",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_spikes_night(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/spikes_night` – Fetching and processing of spikes_night data."""
    return _call_lambda(
        path="/spikes_night",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_hr_readings(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/hr_readings` – Fetching and processing of hr_readings data."""
    return _call_lambda(
        path="/hr_readings",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_spo2_readings(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/spo2_readings` – Fetching and processing of spo2_readings data."""
    return _call_lambda(
        path="/spo2_readings",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_bt_readings(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/bt_readings` – Fetching and processing of bt_readings data."""
    return _call_lambda(
        path="/bt_readings",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_bp_readings(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/bp_readings` – Fetching and processing of bp_readings data."""
    return _call_lambda(
        path="/bp_readings",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_glucose_readings(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/glucose-readings` – Fetching and processing of glucose-readings data."""
    return _call_lambda(
        path="/glucose-readings",
        query={"mobile_number": mobile_number, "date": date}
    )

def get_master_glucose_config(mobile_number: str, date: Optional[str]) -> Dict[str, Any]:
    """Mirror `/master_glucose_config` – Fetching and processing of master_glucose_config data."""
    return _call_lambda(
        path="/master_glucose_config",
        query={"mobile_number": mobile_number, "date": date}
    )
