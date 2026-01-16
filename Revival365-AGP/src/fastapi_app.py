from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import logging

# Import the existing core logic
from main import get_glucose_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to match Lambda's behavior
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgpRequest(BaseModel):
    mobile_number: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.post("/agp_profile")
async def get_agp_profile(data: AgpRequest):
    """
    Endpoint to fetch glucose data, mirroring the functionality of the Lambda function.
    """
    logger.info(f"Received request for mobile_number: {data.mobile_number}")

    if not data.mobile_number:
        raise HTTPException(status_code=400, detail="mobile_number is required")

    try:
        # Call the existing logic
        # get_glucose_data returns a JSON string
        glucose_json = get_glucose_data(
            mobile_number=data.mobile_number,
            start_date=data.start_date,
            end_date=data.end_date
        )
        
        # Return as raw JSON response to avoid double serialization/deserialization overhead
        # logic: get_glucose_data -> str(json) -> Response
        return Response(content=glucose_json, media_type="application/json")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Revival365 AGP API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
