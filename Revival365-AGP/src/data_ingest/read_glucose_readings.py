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

def get_data_as_json(mobile_number, start_date=None, end_date=None):
    # Fetch glucose readings
    df, error = get_glucose_readings_by_mobile_number(mobile_number)
    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Convert input dates to datetime objects
    if start_date:
        start_date = pd.to_datetime(start_date).date()
    if end_date:
        end_date = pd.to_datetime(end_date).date()

    # Filter the data for the date range
    df['date'] = df['timestamp'].dt.date
    if start_date and end_date:
        df_range = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    elif start_date:
        df_range = df[df['date'] >= start_date]
    elif end_date:
        df_range = df[df['date'] <= end_date]
    else:
        df_range = df

    if df_range.empty:
        return {"error": "No data available for the specified date range"}

    # Calculate average for the date range
    range_average = int(df_range['value'].mean().round(0))
    
    # Round glucose readings in the DataFrame
    df_range['value'] = df_range['value'].astype(int)
    
    # Fetch patient details
    patient = fetch_user_details(mobile_number)
    if patient is None:
        return {"error": "Patient not found"}

    # Fetch medications using the patient ID
    patient_id = patient['id']  # Access the patient ID correctly
    
    # Convert timestamps in the DataFrame to ISO format for JSON serialization
    df_range['timestamp'] = df_range['timestamp'].apply(lambda x: x.isoformat())

    # Create the JSON with all relevant information
    data_json = {
        "glucose_readings": df_range[['timestamp', 'value']].to_dict(orient='records'),
      
    }

    # Ensure all values in the data_json are JSON serializable
    return json.loads(json.dumps(data_json, default=convert_value))

def glucose_readings(mobile_no, start_date=None, end_date=None):
    output_json = get_data_as_json(mobile_no, start_date, end_date)
    return output_json

def main():
    # Example inputs
    mobile_number = "+918521345464"
    start_date = "2025-1-1"
    end_date = "2025-1-7"

    try:
        # Call glucose_readings with the provided inputs
        result = glucose_readings(mobile_number, start_date, end_date)
        print(json.dumps(result, indent=4))  # Pretty-print the JSON result
        debug_file = "debug_output.json"
        with open(debug_file, "w") as file:
            json.dump(result, file, indent=4)
        print(f"Output saved to {debug_file} for debugging.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

