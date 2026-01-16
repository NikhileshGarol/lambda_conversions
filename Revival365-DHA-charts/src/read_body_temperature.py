# db/body_temperature_json.py
from db.temperature_readings import fetch_body_temperature_readings_for_specific_day
from db.UserDet import fetch_patient_details
import json

def get_body_temperature_data_as_json(mobile_number, specific_date=None):
    df, error = fetch_body_temperature_readings_for_specific_day(mobile_number, specific_date)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Calculate daily average and round it
    daily_average = round(df['temperature'].mean(), 2)

    # Convert temperatures to integers
    df['temperature'] = df['temperature'].astype(int)

    # Fetch patient details
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"errorP": patient_error}
    
    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Create the JSON with all relevant information
    data_json = {
        #"body_temperature_readings": df[['timestamp', 'temperature']].to_dict(orient='records'),
        "daily_average": daily_average,
        "patient_details": {
            "userid": patient,
            "mobile_number": mobile_number,
        },
    }

    return data_json

'''
if __name__ == "__main__":
    mobile_number = 9945726507  # Replace with the actual mobile number
    specific_date = '2024-10-01'  # Specify the date in YYYY-MM-DD format
    data = get_body_temperature_data_as_json(mobile_number, specific_date)
    print(json.dumps(data, indent=4))  # Pretty print the JSON
    '''