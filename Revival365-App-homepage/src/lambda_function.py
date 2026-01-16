import json
import logging
import traceback
import os
import time
import datetime
from new_final import generate_health_json  # Import function

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# ✅ Set timezone to IST (Asia/Kolkata)
os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda handler for fetching glucose data.
    """
    logger.info("Lambda function started.")

    # ✅ Debug log: Current IST time in Lambda
    current_time_ist = datetime.datetime.now()
    logger.info(f"🛠 DEBUG: Current IST Time in Lambda: {current_time_ist}")

    try:
        # Extract the path from the event
        path = event.get('rawPath', '')
        logger.info(f"Request path: {path}")

        # Extract query parameters and body data
        query_params = event.get('queryStringParameters', {}) or {}
        body = event.get('body', None)

        # Default value
        patient_id = query_params.get('patient_id')

        # Parse body if provided
        if body:
            try:
                body_data = json.loads(body)
                patient_id = body_data.get('patient_id', patient_id)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in request body")
                return build_response(400, {'error': 'Invalid JSON format in request body'})

        # Validate required parameter
        if not patient_id:
            return build_response(400, {'error': 'patient_id is required'})

        # Handle the specific path
        if path == '/home_page':
            logger.info(f"Fetching glucose data for patient_id: {patient_id}")
            glucose_json = generate_health_json(user_id=patient_id)

            # Log response size (not actual data)
            return build_response(200, glucose_json)

        else:
            logger.error(f"Invalid path requested: {path}")
            return build_response(404, {'error': 'Not Found'})

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        logger.error(traceback.format_exc())  # Log full traceback
        return build_response(500, {'error': 'An internal error occurred', 'details': str(e)})

def build_response(status_code: int, body: dict) -> dict:
    """
    Helper function to build API Gateway compatible responses.
    """
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
        }
    }
