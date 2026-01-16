"""
FastAPI router mirroring Revival365-clinical-report-summary Lambda.

This module exposes an HTTP endpoint that behaves identically
to the existing clinical-report-summary Lambda function. It acts as a compatibility
layer during migration from AWS Lambda to FastAPI.
"""
from __future__ import annotations
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# Service-layer function that encapsulates the AGP business logic
# (currently aligned with Lambda behavior)
from app.services.clinical_report_summary import get_clinical_report_summary

# Initialize a FastAPI router
# - prefix="" means the route is exposed at the root level
# - tags=["AGP"] enables logical grouping in Swagger/OpenAPI docs
router = APIRouter(prefix="", tags=["Clinical Report Summary"])


@router.get("/clinical_report")
async def get_clinical_report(url: str) -> Dict[str, Any]:
    """
    This endpoint wraps the existing Clinical report summary Lambda logic to ensure
    functional parity. It accepts a validated Clinical report summary Request payload
    and returns the Clinical report summary profile data.
    """

    # Validate required feilds
    if url is None:
        raise HTTPException(
            status_code=400, detail="URL is required."
        )
    try:
        result = get_clinical_report_summary(url)
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
