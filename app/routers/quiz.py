"""
FastAPI router mirroring Revival365-quiz Lambda.

This module exposes an HTTP endpoint that behaves identically
to the existing quiz Lambda function. It acts as a compatibility
layer during migration from AWS Lambda to FastAPI.
"""
from __future__ import annotations
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# Service-layer function that encapsulates the AGP business logic
# (currently aligned with Lambda behavior)
from app.services.quiz import get_quiz

# Initialize a FastAPI router
# - prefix="" means the route is exposed at the root level
# - tags=["AGP"] enables logical grouping in Swagger/OpenAPI docs
router = APIRouter(prefix="", tags=["Quiz"])


@router.get("/quiz")
async def get_quiz_details(patientId: str) -> Dict[str, Any]:
    """
    This endpoint wraps the existing Quiz Lambda logic to ensure
    functional parity. It accepts a validated Quiz Request payload
    and returns the Quiz profile data.
    """

    # Validate required feilds
    if patientId is None:
        raise HTTPException(
            status_code=400, detail="Patient ID is required."
        )
    try:
        result = get_quiz(patientId)
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
