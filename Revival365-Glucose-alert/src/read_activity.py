import json
from db.activity_readings2 import fetch_activity_readings_for_specific_day  # Assuming this function exists
from db.UserDet import fetch_patient_details

def get_activity_data_as_json(mobile_number, specific_date=None,interval=None):
    # Fetch activity readings for the given mobile number and specific date
    df, error = fetch_activity_readings_for_specific_day(mobile_number, specific_date,interval)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Calculate daily totals and round them
    daily_totals = {
        "total_exercise_duration": round(df['total_exercise_duration'].sum(), 2),
        "total_calories_burned": round(df['total_calories_burned'].sum(), 2),
        "total_distance": round(df['total_distance'].sum(), 2),
        "total_steps": int(df['total_step'].sum())
    }

    # Fetch patient details using the mobile number
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"error": patient_error}

    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601 and prepare the activity data
    df['date'] = df['date'].astype(str)  # Ensure the date is in string format

    activity_data = df[['date', 'activity_type', 'total_exercise_duration', 
                        'total_calories_burned', 'total_distance', 'total_step']].to_dict(orient='records')

    # Construct the JSON output with activity readings and patient details
    data_json = {
        "activity_readings": activity_data,
        "daily_totals": daily_totals,
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
            'date': '2025-01-9'
        }
    }
    context = None  # You can leave this as None if not testing specific context

    # Extract parameters from the event object
    mobile_number = event['queryStringParameters'].get('mobile_number')
    specific_date = event['queryStringParameters'].get('date', None)  # Default to None if no date is provided

    response = get_activity_data_as_json(mobile_number, specific_date)
    print("Lambda Response:", response)
