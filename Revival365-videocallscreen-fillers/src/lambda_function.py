import json
import logging
from get_description import get_patient_medical_description
from get_health_data import get_health_data
from get_medical_condition import get_medical_condition
from get_progress_summary import get_progress 
from get_report_summary import get_report_summary
from get_variant import get_variant
from recommendations import get_recommendations


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event: dict, context) -> dict:
    logger.info("Lambda function started.")
    
    # Extract the mobile number from the query string parameters
    mobile_number = event.get('queryStringParameters', {}).get('mobile_number')
 
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
        if path == '/get_description':
             trend_data = get_patient_medical_description(mobile_number)
        elif path == '/get_health_data':
             trend_data = get_health_data(mobile_number)
        elif path == '/get_medical_condition':
             trend_data = get_medical_condition(mobile_number)   
        elif path == '/get_progress':
             trend_data = get_progress(mobile_number)
        elif path == '/get_report_summary':
             trend_data = get_report_summary(mobile_number)   
        elif path == '/get_variant':
             trend_data = get_variant(mobile_number) 
        elif path == '/get_recommendations':
             trend_data = get_recommendations(mobile_number)
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
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
        }
    }
     

     
