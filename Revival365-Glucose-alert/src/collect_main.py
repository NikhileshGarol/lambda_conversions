import json
import logging
'''
from tir import tir_Trends
from fbg import fbg_trends
from mean_gluc import glucose_trends
from meal_spike import analyze_glucose_spikes
from nAUC import nAUC_Trends
from no_of_dips_day import analyze_glucose_dips_day
from no_of_dips_night import analyze_glucose_dips_night
from no_of_Spikes_day import analyze_glucose_spikes_day
from no_of_Spikes_night import analyze_glucose_spikes_night
'''
from read_hr import get_heart_rate_data_as_json
from read_spo2 import get_spo2_data_as_json
from read_body_temperature import get_body_temperature_data_as_json
from read_bp import get_blood_pressure_data_as_json
from read_glucose_readings import glucose_readings
from read_stress import get_stress_data_as_json
from read_activity import get_activity_data_as_json
from read_sleep import get_sleep_data_as_json
from read_hrv import get_hrv_data_as_json
 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event: dict, context) -> dict:
    logger.info("Lambda function started.")
    
    # Hardcoded mobile number for testing
    mobile_number = "+918521345464"  # Replace with your desired phone number for testing
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

    # Proceed with calling all functions
    try:
        combined_data = {}

        # Call all trend functions and collect the data
      
        #combined_data['heart_rate_readings'] = get_heart_rate_data_as_json(mobile_number, interval=2)
       # combined_data['spo2_readings'] = get_spo2_data_as_json(mobile_number, interval=2)
        #combined_data['body_temperature_readings'] = get_body_temperature_data_as_json(mobile_number, interval=2)
        combined_data['blood_pressure_readings'] = get_blood_pressure_data_as_json(mobile_number, interval=2)
       # combined_data['glucose_readings'] = glucose_readings(mobile_number,interval=1)
        #combined_data['stress_readings'] = get_stress_data_as_json(mobile_number, interval=2)
        #combined_data['hrv_readings'] = get_hrv_data_as_json(mobile_number, interval=2)
       # combined_data['sleep_readings'] = get_sleep_data_as_json(mobile_number, interval=1)
        #combined_data['activity_readings'] = get_activity_data_as_json(mobile_number, interval=3)

        # Check if any data is missing or None
        if not any(combined_data.values()):
            logger.warning("No data found for the given mobile number.")
            return build_response(404, {'error': 'No data found for the given mobile number'})

        return build_response(200, combined_data)

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
    
    
    
# For local testing, provide a mock event and context
if __name__ == "__main__":
    event = {
        'queryStringParameters': {
            'mobile_number': '+918521345464',  # Hardcoded number for testing
            'date': '2025-01-12'
        }
    }
    context = None  # You can leave this as None if not testing specific context
    response = lambda_handler(event, context)
    print("Lambda Response:", response)

