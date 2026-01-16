import pandas as pd
import json  # Importing the json library
from db.GlucRead import get_glucose_readings_by_mobile_number
from db.UserDet import fetch_patient_details, fetch_user_details ,fetch_medication_details # Import the new function
from config.config import config
from datetime import datetime
from decimal import Decimal  # Import Decimal

def convert_value(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()  # Convert Timestamp to ISO 8601 format
    raise TypeError(f'Type {type(obj)} not serializable')

def get_data_as_json(mobile_number, selected_date=None):
    # Fetch glucose readings
    df, error = get_glucose_readings_by_mobile_number(mobile_number)
    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Filter the data for the selected date
    selected_date = pd.to_datetime(selected_date).date() if selected_date else datetime.today().date()
    df['date'] = df['timestamp'].dt.date
    df_day = df[df['date'] == selected_date]

    if df_day.empty:
        return {"error": "No data available for this date"}

    # Calculate daily average
    #daily_average = df_day['value'].mean().round(0).astype(int)  # Round to 2 decimal places
    daily_average = int(df_day['value'].mean().round(0))
    # Round glucose readings in the DataFrame
    df_day['value'] = df_day['value'].astype(int)
    # Get day/night start times from config
    day_night = config.get_time_classification()
    night_start = day_night['night_start']
    night_end = day_night['night_end']

    # Get glucose thresholds
    thresholds = config.get_glucose_thresholds()
    low_threshold = thresholds['low_threshold']
    high_threshold = thresholds['high_threshold']

    # Fetch patient details
    patient = fetch_user_details(mobile_number)
    if patient is None:
        return {"error": "Patient not found"}

    # Fetch medications using the patient ID
    patient_id = patient['id']  # Access the patient ID correctly
    # Fetch medications using the patient ID
    medications, med_error = fetch_medication_details(patient_id)  # Fetch medications here
    if med_error:
        return {"error": med_error}

    # Convert timestamps in the DataFrame to ISO format for JSON serialization
    df_day['timestamp'] = df_day['timestamp'].apply(lambda x: x.isoformat())

    # Create the JSON with all relevant information
    data_json = {
        "glucose_readings": df_day[['timestamp', 'value']].to_dict(orient='records'),
         
        "patient_details": patient,  # Include all patient details directly
    }

    # Ensure all values in the data_json are JSON serializable
    return json.loads(json.dumps(data_json, default=convert_value))

def glucose_readings(mobile_no, selected_date=None):
    output_json = get_data_as_json(mobile_no, selected_date)
    return output_json
    

def main():
    # Sample usage with a mobile number and optional parameters
    mobile_no = "+918855478888"  # You can replace this with an actual mobile number
    selected_date = ""  # Optional: Pass the date to filter data
    interval = 2  # Optional: Pass interval if needed
    
    data = glucose_readings(mobile_no )
    print(json.dumps(data, indent=4))
    with open("glucose_readings_output.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
if __name__ == "__main__":
    main()
