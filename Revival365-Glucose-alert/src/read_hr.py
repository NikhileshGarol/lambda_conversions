import json
from db.heart_rate_readings2 import fetch_heart_rate_readings_for_specific_day
from db.UserDet import fetch_patient_details

def get_heart_rate_data_as_json(mobile_number, specific_date=None,interval=None):
    # Fetch heart rate readings for the given mobile number and specific date
    df, error = fetch_heart_rate_readings_for_specific_day(mobile_number, specific_date,interval)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Calculate daily average and round it
    daily_average = round(df['value'].mean(), 2)

    # Convert values to integers
    df['value'] = df['value'].astype(int)

    # Fetch patient details using the mobile number
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"error": patient_error}
    
    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Construct the JSON output with heart rate readings and patient details
    data_json = {
        "heart_rate_readings": df[['timestamp', 'value']].to_dict(orient='records'),
        "daily_average": daily_average,
        "patient_details": {
            "userid": patient,
            "mobile_number": mobile_number,
        },
    }

    return data_json

 
