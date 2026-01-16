# Ensure environment variables from .env are loaded
# before importing modules that depend on configuration
from dotenv import load_dotenv
load_dotenv()

import json
import logging
from main import get_glucose_data  # Import the function we created earlier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda handler for fetching glucose data.
    """
    logger.info("Lambda function started.")

    # Extract the path from the event
    path = event.get('rawPath', '')
    logger.info(f"Request path: {path}")

    # Extract the query parameters or body data from the event
    query_params = event.get('queryStringParameters', {})
    body = event.get('body', None)

    # Default values for parameters
    mobile_number = query_params.get('mobile_number', None)
    start_date = query_params.get('start_date', None)
    end_date = query_params.get('end_date', None)

    # If the body is provided and contains relevant data, use it
    if body:
        body_data = json.loads(body)
        mobile_number = body_data.get('mobile_number', mobile_number)
        start_date = body_data.get('start_date', start_date)
        end_date = body_data.get('end_date', end_date)

    # Validate the required parameters
    if not mobile_number:
        return build_response(400, {'error': 'mobile_number is required'})

    try:
        # Handle the specific path for the `get_glucose_data` function
        if path == '/agp_profile':
            # Call `get_glucose_data` with the extracted parameters
            glucose_json = get_glucose_data(mobile_number=mobile_number)

            # Return the data as a response
            return build_response(200, json.loads(glucose_json))

        else:
            logger.error(f"Invalid path requested: {path}")
            return build_response(404, {'error': 'Not Found'})

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
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
