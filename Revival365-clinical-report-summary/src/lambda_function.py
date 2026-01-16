import json
import logging
from summary_detail_clinical import process_lab_report  # Import the process_lab_report function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event: dict, context) -> dict:
    logger.info("Lambda function started.")

    # Extract the HTTP method from the request
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET').upper()
    path = event.get('rawPath', '')
    url = None

    # Get the URL either from query parameters (GET) or from the body (POST)
    if http_method == 'GET':
        url = event.get('queryStringParameters', {}).get('url')
    elif http_method == 'POST':
        body = json.loads(event.get('body', '{}'))
        url = body.get('url')

    if not url:
        logger.error("Missing url in query parameters or body.")
        return build_response(400, {'error': 'Missing url in query parameters or body'})

    try:
        # Handle different paths for function calls
        if path == '/clinical_report':
            trend_data = process_lab_report(url)
        else:
            logger.error(f"Invalid path requested: {path}")
            return build_response(404, {'error': 'Not Found'})

        # Check if data is returned from process_lab_report
        if trend_data is None:
            logger.warning("No data found for the given URL.")
            return build_response(404, {'error': 'No data found for the given URL'})

        # If trend_data exists, return success response
        return build_response(200, trend_data)


    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return build_response(500, {'error': 'Internal Server Error', 'message': str(e)})

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