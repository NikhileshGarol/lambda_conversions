import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Load the JSON file once at startup to avoid repeated file reads
try:
    with open("null_first_page.json", "r") as file:
        json_data = json.load(file)
except Exception as e:
    logger.error(f"Error loading JSON file: {e}")
    json_data = {"error": "Could not load JSON file"}

def lambda_handler(event: dict, context) -> dict:
    logger.info("Lambda function started.")

    # Extract rawPath from the event
    raw_path = event.get('rawPath', '')

    # Extract query parameters (for API Gateway requests)
    query_string_parameters = event.get('queryStringParameters', {}) or {}
    patient_id = query_string_parameters.get('patient_id')

    if raw_path == '/home_page':
        # Validate patient_id
        if not patient_id:
            logger.error("Missing patient_id in request")
            return build_response(400, {"error": "patient_id is required"})

        if not patient_id.isdigit():
            logger.error(f"Invalid patient_id: {patient_id}")
            return build_response(400, {"error": "patient_id must be a numeric value"})

        response_data = json_data.copy()  # Avoid modifying the original JSON data
 
        return build_response(200, response_data)

    logger.error(f"Invalid path requested: {raw_path}")
    return build_response(404, {'error': 'Not Found', 'path': raw_path})

def build_response(status_code: int, body: dict) -> dict:
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
        }
    }
