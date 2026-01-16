from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Utility responsible for dynamically loading a Lambda handler
from app.utils.lambda_loader import load_lambda_handler

# ------------------------------------------------------------------
# Runtime Path Configuration
# ------------------------------------------------------------------
# Determine the project root directory dynamically.
# parents[2] assumes this file lives under:
# app/services/agp/<this_file>.py
# Add Lambda source to sys.path
ROOT = Path(__file__).resolve().parents[2]

# Path to the original AGP Lambda source directory
AGP_SRC = ROOT / "Revival365-AGP" / "src"

# Inject Lambda source directory into sys.path
# This ensures all internal Lambda imports continue to work
if str(AGP_SRC) not in sys.path:
    sys.path.insert(0, str(AGP_SRC))

# ------------------------------------------------------------------
# Lambda Handler Loading
# ------------------------------------------------------------------
# Absolute path to the Lambda entry file
AGP_LAMBDA_PATH = (
    ROOT / "Revival365-AGP" / "src" / "lambda_function.py"
)

# Dynamically load the lambda_handler function from the file
# - module_name prevents naming collisions
# - handler is cached after initial load
agp_lambda_handler = load_lambda_handler(
    lambda_file_path=AGP_LAMBDA_PATH,
    module_name="agp_lambda_module",
)

# ------------------------------------------------------------------
# Service Function (FastAPI-facing)
# ------------------------------------------------------------------


def fetch_agp_profile(
    mobile_number: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Reuse the existing Lambda handler by reconstructing the API Gateway event
    it expects. This keeps behavior identical without refactoring business code.
    """
    event = {
        "rawPath": "/agp_profile",
        "queryStringParameters": {
            "mobile_number": mobile_number,
            # "start_date": start_date,
            # "end_date": end_date,
        },
        "body": json.dumps(
            {
                "mobile_number": mobile_number,
                # "start_date": start_date,
                # "end_date": end_date,
            }
        ),
    }

    result = agp_lambda_handler(event, context=None)
    status = result.get("statusCode", 200)
    body = result.get("body")

    # Lambda responses often serialize the body as JSON string
    # Normalize it into a Python dictionary
    if isinstance(body, str):
        body = json.loads(body)

    # Standardized service-layer response
    return {"status": status, "body": body}
