"""
FastAPI router mirroring DEV-Revival365-AGP Lambda.

This module exposes an HTTP endpoint that behaves identically
to the existing AGP Lambda function. It acts as a compatibility
layer during migration from AWS Lambda to FastAPI.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# Pydantic schema used to validate and parse incoming request payloads
from app.schemas.agp import AgpRequest

# Service-layer function that encapsulates the AGP business logic
# (currently aligned with Lambda behavior)
from app.services.agp import fetch_agp_profile

# Initialize a FastAPI router
# - prefix="" means the route is exposed at the root level
# - tags=["AGP"] enables logical grouping in Swagger/OpenAPI docs
router = APIRouter(prefix="", tags=["AGP"])


@router.post("/agp_profile")
async def get_agp(payload: AgpRequest) -> Dict[str, Any]:
    """
    This endpoint wraps the existing AGP Lambda logic to ensure
    functional parity. It accepts a validated AgpRequest payload
    and returns the AGP profile data.
    """
    # Validate required feilds
    if payload.mobile_number is None:
        raise HTTPException(
            status_code=400, detail="mobile_number is required")

    try:
        # Call the service-layer function to fetch AGP profile data
        result = fetch_agp_profile(
            mobile_number=payload.mobile_number,
            # start_date=payload.start_date,
            # end_date=payload.end_date,
        )
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
