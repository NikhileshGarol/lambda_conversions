import json
from db.spo2_readings import fetch_spo2_readings_for_specific_day
from db.UserDet import fetch_patient_details

def get_spo2_data_as_json(mobile_number, specific_date=None):
    df, error = fetch_spo2_readings_for_specific_day(mobile_number, specific_date)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Calculate daily average and round it
    daily_average = round(df['value'].mean(), 2)

    # Convert values to integers
    df['value'] = df['value'].astype(int)

    # Fetch patient details
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"error": patient_error}
    
    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Create the JSON with all relevant information
    data_json = {
       #s "spo2_readings": df[['timestamp', 'value']].to_dict(orient='records'),
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
    specific_date = '2024-10-11'  # Specify the date in YYYY-MM-DD format
    data = get_spo2_data_as_json(mobile_number, specific_date)
    print(json.dumps(data, indent=4))  # Pretty print the JSON
'''