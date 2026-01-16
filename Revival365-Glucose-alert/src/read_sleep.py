import json
from db.sleep_readings2 import fetch_sleep_readings_for_specific_day
from db.UserDet import fetch_patient_details

def get_sleep_data_as_json(mobile_number, specific_date=None,interval=None):
    # Fetch sleep readings for the given mobile number and specific date
    df, error = fetch_sleep_readings_for_specific_day(mobile_number, specific_date,interval)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Calculate daily average (if applicable) and round it
    daily_average = round(df['value'].mean(), 2)
    df = df.drop_duplicates(subset=['date'])
    # Ensure 'value' column is integer type
    df['value'] = df['value'].astype(int)
# Remove duplicates based on the 'date' column


    # Fetch patient details using the mobile number
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"error": patient_error}
    
    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601
    df['date'] = df['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Construct the JSON output with sleep readings and patient details
    data_json = {
        "sleep_readings": df[['date', 'value', 'level', 'sleep_type']].to_dict(orient='records'),
        "daily_average": daily_average,
        "patient_details": {
            "userid": patient,
            "mobile_number": mobile_number,
        },
    }

    return data_json

if __name__ == "__main__":
    event = {
        'queryStringParameters': {
            'mobile_number': '+918521345464',  # Hardcoded number for testing
            'date': '2025-01-8'
        }
    }
    context = None  # You can leave this as None if not testing specific context

    # Extract parameters from the event object
    mobile_number = event['queryStringParameters'].get('mobile_number')
    specific_date = event['queryStringParameters'].get('date', None)  # Default to None if no date is provided

    response = get_sleep_data_as_json(mobile_number, specific_date)
    print("Lambda Response:", response)

