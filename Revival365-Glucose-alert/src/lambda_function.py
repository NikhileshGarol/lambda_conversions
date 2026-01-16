# Ensure environment variables from .env are loaded
# before importing modules that depend on configuration
from dotenv import load_dotenv
load_dotenv()

import json
import logging
from process_glucose import process_glucose_readings  # Assuming the function is in a module named process_glucose

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event: dict, context) -> dict:
    logger.info("Lambda function started.")
    
    # Extract the mobile number from the query string parameters
    mobile_number = event.get('queryStringParameters', {}).get('mobile_number')
    specific_date = event.get('queryStringParameters', {}).get('date')

   # Validate the mobile number
    if not mobile_number or not isinstance(mobile_number, str):
        logger.error("Invalid or missing mobile number.")
        return build_response(400, {'error': 'Invalid or missing mobile_number'})

    elif not (10 <= len(mobile_number) <= 15):
        logger.error("Mobile number length out of bounds.")
        return build_response(400, {'error': 'Mobile number length out of bounds'})
    elif not (mobile_number.startswith('+') and mobile_number[1:].isdigit()) and not mobile_number.isdigit():
        logger.error("Invalid mobile number format.")
        return build_response(400, {'error': 'Invalid mobile_number format'})
# Proceed with further logic if valid



    # Use rawPath for the API Gateway path
    path = event.get('rawPath', '')
    logger.info(f"Request path: {path}")

    try:
        # Handle different paths for function calls
        if path == '/CGM_alert':
            logger.info(f"Processing glucose readings for mobile number: {mobile_number}")
            process_glucose_readings(mobile_number)
            return build_response(200, {'message': 'Glucose readings processed successfully'})
        else:
            logger.error(f"Invalid path requested: {path}")
            return build_response(404, {'error': 'Not Found'})

        # Check if data is returned from the trends functions
        if trend_data is None:
            logger.warning("No data found for the given mobile number.")
            return build_response(404, {'error': 'No data found for the given mobile number'})

        return build_response(200, trend_data)

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return build_response(500, {'error': 'An internal error occurred', 'details': str(e)})

def build_response(status_code: int, body: dict) -> dict:
    
    status_message = 'OK' if status_code == 200 else 'Error'

    # Add the status code to the body
    body_with_status = {
        'status': status_code,
        'statusMessage': status_message,
        **body  # Include the original body content
    }

    
    return {
        'statusCode': status_code,
        'body': json.dumps(body_with_status),  # Include status code and message in body
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
        }
    }
     