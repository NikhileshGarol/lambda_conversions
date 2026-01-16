"""
FastAPI router mirroring Revival365-DHA-charts Lambda.

This module exposes an HTTP endpoint that behaves identically
to the existing DHA-charts Lambda function. It acts as a compatibility
layer during migration from AWS Lambda to FastAPI.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends

# Service-layer function that encapsulates the AGP business logic
# (currently aligned with Lambda behavior)
from app.services.dha_charts import get_tir_trends, get_fbg_trends, get_mean_gluc_trends, get_meal_spikes_trends, get_nauc_trends, get_dips_day, get_dips_night, get_spikes_day, get_bp_readings, get_bt_readings, get_glucose_readings, get_hr_readings, get_spo2_readings, get_master_glucose_config, get_spikes_night

# Schemas user for request validation
from app.schemas.dha import DhaChartRequest

# Initialize a FastAPI router
# - prefix="" means the route is exposed at the root level
# - tags=["AGP"] enables logical grouping in Swagger/OpenAPI docs
router = APIRouter(prefix="", tags=["DHA Charts"])


@router.get("/tir")
async def get_tir(mobile_number: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    This endpoint wraps the existing tri_trends Lambda logic to ensure
    functional parity. It accepts a validated tri_trends Request payload
    and returns the tri_trends profile data.
    """

    # Validate required feilds
    if mobile_number is None:
        raise HTTPException(
            status_code=400, detail="Mobile number is required."
        )
    try:
        result = get_tir_trends(mobile_number=mobile_number, date=date)
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


@router.get("/fbg")
async def get_fbg_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /fbg Lambda route - Get Fasting Blood Glucose details"""
    result = get_fbg_trends(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/mean_gluc")
async def get_mean_gluc_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /mean_gluc Lambda route - Get Mean Glucose details"""
    result = get_mean_gluc_trends(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/meal_spikes")
async def get_fbg_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /meal_spikes Lambda route - Get Meal spikes details"""
    result = get_meal_spikes_trends(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/nauc")
async def get_nauc_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /nauc Lambda route - Get NAUC details"""
    result = get_nauc_trends(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/dips_day")
async def get_dips_day_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /dips_day Lambda route - Get Dips_day details"""
    result = get_dips_day(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/dips_night")
async def get_dips_night_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /dips_night Lambda route - Get Dips_night details"""
    result = get_dips_night(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/spikes_day")
async def get_spikes_day_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /spikes_day Lambda route - Get Spikes_day details"""
    result = get_spikes_day(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/spikes_night")
async def get_spikes_night_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /spikes_night Lambda route - Get Spikes_night details"""
    result = get_spikes_night(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/glucose-readings")
async def get_glucose_readings_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /glucose-readings Lambda route - Get Glucose reading details"""
    result = get_glucose_readings(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body


@router.get("/master_glucose_config")
async def get_master_glucose_config_details(payload: DhaChartRequest = Depends()) -> Dict[str, Any]:
    """Mirror the /master_glucose_config Lambda route - Get Master glucose config details"""
    result = get_master_glucose_config(
        mobile_number=payload.mobile_number,
        date=payload.date
    )
    status = result["status"]
    body = result["body"]
    if status >= 400:
        raise HTTPException(status_code=status, detail=body)
    return body
