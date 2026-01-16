# Ensure environment variables from .env are loaded
# before importing modules that depend on configuration
from dotenv import load_dotenv
load_dotenv()

import json
import logging
from tir import tir_Trends  # Import the tir_Trends function
from fbg import fbg_trends
from mean_gluc import glucose_trends
from meal_spike import analyze_glucose_spikes
from nAUC import nAUC_Trends
from no_of_dips_day import analyze_glucose_dips_day
from no_of_dips_night import analyze_glucose_dips_night
from no_of_Spikes_day import analyze_glucose_spikes_day
from no_of_Spikes_night import analyze_glucose_spikes_night

from read_glucose_readings import glucose_readings
from master_glucose_config import get_glucose_master_configuration_as_json
from read_body_temperature import get_body_temperature_data_as_json
from read_bp import get_blood_pressure_data_as_json
from read_hr import get_heart_rate_data_as_json
from read_spo2 import get_spo2_data_as_json


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event: dict, context) -> dict:
    
    logger.info("Lambda function started.")
    
    
    path = event.get('rawPath', '')
    
    if path != '/master_glucose_config':
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
 


  

    try:
        # Handle different paths for function calls
        if path == '/tir':
             trend_data = tir_Trends(mobile_number,specific_date)
        elif path == '/fbs':
             trend_data = fbg_trends(mobile_number,specific_date)
        elif path == '/mean_gluc':
             trend_data = glucose_trends(mobile_number,specific_date)
        elif path == '/meal_spikes':
             trend_data = analyze_glucose_spikes(mobile_number,specific_date)
        elif path == '/nauc':
             trend_data = nAUC_Trends(mobile_number,specific_date)
        elif path == '/dips_day':
             trend_data = analyze_glucose_dips_day(mobile_number,specific_date)
        elif path == '/dips_night':
             trend_data = analyze_glucose_dips_night(mobile_number,specific_date)
        elif path == '/spikes_day':
             trend_data = analyze_glucose_spikes_day(mobile_number,specific_date)
        elif path == '/spikes_night':
             trend_data = analyze_glucose_spikes_night(mobile_number,specific_date)  
        elif path == '/hr_readings':
             trend_data = get_heart_rate_data_as_json(mobile_number,specific_date) 
        elif path == '/spo2_readings':
             trend_data = get_spo2_data_as_json(mobile_number,specific_date) 
        elif path == '/bt_readings':
             trend_data = get_body_temperature_data_as_json(mobile_number,specific_date) 
        elif path == '/bp_readings':
             trend_data = get_blood_pressure_data_as_json(mobile_number,specific_date) 
        elif path == '/glucose-readings':
             trend_data = glucose_readings(mobile_number,specific_date) 
        elif path == '/master_glucose_config':  # New route for glucose master configuration
            trend_data = get_glucose_master_configuration_as_json()
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
     