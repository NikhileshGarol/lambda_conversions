import pandas as pd
import json
from db.GlucRead import get_glucose_readings_by_mobile_number
from db.UserDet import fetch_user_details, fetch_medication_details
from config.config import config
from datetime import datetime, timedelta
from decimal import Decimal

def convert_value(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()  # Convert Timestamp to ISO 8601 format
    raise TypeError(f'Type {type(obj)} not serializable')

def get_data_as_json(mobile_number):
    # Fetch glucose readings
    df, error = get_glucose_readings_by_mobile_number(mobile_number)
    if df is None or df.empty:
        return {"error": error or "No data found"}

    # Ensure 'timestamp' column is a datetime object
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Find the most recent reading date
    latest_date = df['timestamp'].max().date()

    # Calculate the date range for the last 15 days
    start_date = latest_date - timedelta(days=14)  # 15 days inclusive of the latest date
    df['date'] = df['timestamp'].dt.date
    df_range = df[(df['date'] >= start_date) & (df['date'] <= latest_date)]

    if df_range.empty:
        return {"error": "No data available for the last 15 days"}

    # Round glucose readings in the DataFrame
    df_range['value'] = df_range['value'].astype(int)

    # Convert timestamps in the DataFrame to ISO format for JSON serialization
    df_range['timestamp'] = df_range['timestamp'].apply(lambda x: x.isoformat())

    # Create the JSON with all relevant information
    data_json = {
        "date_range": {
            "start_date": start_date.isoformat(),
            "end_date": latest_date.isoformat()
        },
        "glucose_readings": df_range[['timestamp', 'value']].to_dict(orient='records'),
    }

    # Ensure all values in the data_json are JSON serializable
    return json.loads(json.dumps(data_json, default=convert_value))

def glucose_readings(mobile_no):
    output_json = get_data_as_json(mobile_no)
    return output_json

def main():
    # Example inputs
    mobile_number = input("Enter the mobile number: ")

    try:
        # Call glucose_readings with the provided inputs
        result = glucose_readings(mobile_number)
        print(json.dumps(result, indent=4))  # Pretty-print the JSON result
        
        debug_file = "debug_output.json"
        with open(debug_file, "w") as file:
            json.dump(result, file, indent=4)
        print(f"Output saved to {debug_file} for debugging.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

