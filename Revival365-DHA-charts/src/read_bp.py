from db.bp_readings import fetch_blood_pressure_readings_for_specific_day
from db.UserDet import fetch_patient_details
import json

def get_blood_pressure_data_as_json(mobile_number, specific_date=None):
    df, error = fetch_blood_pressure_readings_for_specific_day(mobile_number, specific_date)

    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Fetch patient details
    patient, patient_error = fetch_patient_details(mobile_number)
    if patient_error:
        return {"error": patient_error}
    
    print("Patient details fetched successfully:", patient)

    # Format timestamps to ISO 8601
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Calculate daily averages
    systolic_avg = df['systolic'].mean()
    diastolic_avg = df['diastolic'].mean()

    # Create the JSON with all relevant information
    data_json = {
       # "blood_pressure_readings": df[['timestamp', 'systolic', 'diastolic']].to_dict(orient='records'),
        "patient_details": {
            "userid": patient,
            "mobile_number": mobile_number,
        },
        "daily_average": {
            "systolic_avg": round(systolic_avg, 2),
            "diastolic_avg": round(diastolic_avg, 2)
        }
    }

    return data_json
