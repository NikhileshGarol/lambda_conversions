"""
FastAPI router mirroring Revival365-glucose-alert Lambda.

This module exposes an HTTP endpoint that behaves identically
to the existing glucose-alert Lambda function. It acts as a compatibility
layer during migration from AWS Lambda to FastAPI.
"""
from __future__ import annotations
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# Service-layer function that encapsulates the AGP business logic
# (currently aligned with Lambda behavior)
from app.services.glucose_alert import get_glucose_alert

# Initialize a FastAPI router
# - prefix="" means the route is exposed at the root level
# - tags=["AGP"] enables logical grouping in Swagger/OpenAPI docs
router = APIRouter(prefix="", tags=["CGM Alert"])

@router.get("/CGM_alert")
async def get_CGM_alert(mobile_number: str) -> Dict[str, Any]:
    """
    This endpoint wraps the existing CGM alert Lambda logic to ensure
    functional parity. It accepts a validated CGM alert Request payload
    and returns the CGM alert profile data.
    """

    # Validate required feilds
    if mobile_number is None:
        raise HTTPException(
            status_code=400, detail="Mobile number is required."
        )
    try:
        result = get_glucose_alert(mobile_number)
        status = result["status"]
        body = result["body"]

        # Translate Lambda error responses into HTTP exceptions
        if status >= 400:
            raise HTTPException(status_code=status, detail=body)
        # Successful response
        return body
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        # Catch-all safeguard for unexpected failures
        raise HTTPException(
            status_code=500,
            detail={"error": "An internal error occurred",
                    "details": str(exc)},
        ) from exc
