from __future__ import annotations
"""
Service layer for the clinical report summary module.

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
CLINICAL_REPORT_SRC = ROOT / "Revival365-clinical-report-summary" / "src"

# Inject Lambda source directory into sys.path
# This ensures all internal Lambda imports continue to work
if str(CLINICAL_REPORT_SRC) not in sys.path:
    sys.path.insert(0, str(CLINICAL_REPORT_SRC))

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
CLINICAL_REPORT_LAMBDA_PATH = (
    CLINICAL_REPORT_SRC / "lambda_function.py"
)

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
clinical_report_lambda_handler = load_lambda_handler(
    lambda_file_path=CLINICAL_REPORT_LAMBDA_PATH,
    module_name="clinical_report_lambda_module",
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
    result = clinical_report_lambda_handler(event, context=None)

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

def get_clinical_report_summary(url: str) -> Dict[str, Any]:
    """Mirror `/clinical_report` – Processes the patient lab report."""
    return _call_lambda(
        path="/clinical_report",
        query={"url": url}
    )
