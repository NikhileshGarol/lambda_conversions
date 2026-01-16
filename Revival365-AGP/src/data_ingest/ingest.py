'''
import pandas as pd
from typing import Dict

def fetch_glucose_data() -> pd.DataFrame:
    """
    Fetches glucose data from a hardcoded source for testing purposes.

    :return: pd.DataFrame with columns ['timestamp', 'glucose']
    """
    try:
        # Hardcoded test data
        data: Dict[str, list] = {
  "glucose_readings": [
    {"timestamp": "2025-01-01T00:00:00", "value": 85},
    {"timestamp": "2025-01-01T00:05:00", "value": 90},
    {"timestamp": "2025-01-01T00:10:00", "value": 95},
    {"timestamp": "2025-01-01T00:15:00", "value": 100},
    {"timestamp": "2025-01-01T00:20:00", "value": 105},
    {"timestamp": "2025-01-01T00:25:00", "value": 110},
    {"timestamp": "2025-01-01T00:30:00", "value": 115},
    {"timestamp": "2025-01-01T00:35:00", "value": 120},
    {"timestamp": "2025-01-01T00:40:00", "value": 125},
    {"timestamp": "2025-01-01T00:45:00", "value": 130},
    {"timestamp": "2025-01-01T00:50:00", "value": 135},
    {"timestamp": "2025-01-01T00:55:00", "value": 140},
    {"timestamp": "2025-01-01T06:00:00", "value": 80},
    {"timestamp": "2025-01-01T06:05:00", "value": 85},
    {"timestamp": "2025-01-01T06:10:00", "value": 90},
    {"timestamp": "2025-01-01T06:15:00", "value": 95},
    {"timestamp": "2025-01-01T06:20:00", "value": 100},
    {"timestamp": "2025-01-01T06:25:00", "value": 105},
    {"timestamp": "2025-01-01T06:30:00", "value": 110},
    {"timestamp": "2025-01-01T06:35:00", "value": 115},
    {"timestamp": "2025-01-01T06:40:00", "value": 120},
    {"timestamp": "2025-01-01T06:45:00", "value": 125},
    {"timestamp": "2025-01-01T06:50:00", "value": 130},
    {"timestamp": "2025-01-01T06:55:00", "value": 135},
    {"timestamp": "2025-01-01T12:00:00", "value": 90},
    {"timestamp": "2025-01-01T12:05:00", "value": 95},
    {"timestamp": "2025-01-01T12:10:00", "value": 100},
    {"timestamp": "2025-01-01T12:15:00", "value": 105},
    {"timestamp": "2025-01-01T12:20:00", "value": 110},
    {"timestamp": "2025-01-01T12:25:00", "value": 115},
    {"timestamp": "2025-01-01T12:30:00", "value": 120},
    {"timestamp": "2025-01-01T12:35:00", "value": 125},
    {"timestamp": "2025-01-01T12:40:00", "value": 130},
    {"timestamp": "2025-01-01T12:45:00", "value": 135},
    {"timestamp": "2025-01-01T12:50:00", "value": 140},
    {"timestamp": "2025-01-01T12:55:00", "value": 145},
    {"timestamp": "2025-01-01T18:00:00", "value": 85},
    {"timestamp": "2025-01-01T18:05:00", "value": 90},
    {"timestamp": "2025-01-01T18:10:00", "value": 95},
    {"timestamp": "2025-01-01T18:15:00", "value": 100},
    {"timestamp": "2025-01-01T18:20:00", "value": 105},
    {"timestamp": "2025-01-01T18:25:00", "value": 110},
    {"timestamp": "2025-01-01T18:30:00", "value": 115},
    {"timestamp": "2025-01-01T18:35:00", "value": 120},
    {"timestamp": "2025-01-01T18:40:00", "value": 125},
    {"timestamp": "2025-01-01T18:45:00", "value": 130},
    {"timestamp": "2025-01-01T18:50:00", "value": 135},
    {"timestamp": "2025-01-01T18:55:00", "value": 140}
  ]
}



        # Convert to DataFrame
        readings = pd.DataFrame(data['glucose_readings'])

        # Ensure correct column names
        readings.rename(columns={'value': 'glucose'}, inplace=True)
        readings['timestamp'] = pd.to_datetime(readings['timestamp'])  # Convert timestamps to datetime
        readings['glucose'] = pd.to_numeric(readings['glucose'], errors='coerce')  # Ensure glucose values are numeric

        # Drop rows with invalid data
        readings = readings.dropna(subset=['timestamp', 'glucose'])

        return readings
    except Exception as e:
        raise RuntimeError(f"Error fetching glucose data: {e}")

def ingest_data() -> pd.DataFrame:
    """
    Ingests data by fetching it from a hardcoded source for testing.
    Returns the raw data as a pandas DataFrame.
    """
    raw_data = fetch_glucose_data()
    print(raw_data)  # Displays the first few rows of the data
    return raw_data

# Test the ingest_data function
if __name__ == "__main__":
    ingest_data()
'''
import pandas as pd
from datetime import datetime, timedelta
from data_ingest.read_glucose_readings import glucose_readings  # Import the glucose_readings function

def ingest_data(mobile_number, days=90):
    """
    Ingests glucose data by fetching it dynamically from the database.
    Fetches data for the past `days` (default is 30 days).
    Returns the raw glucose data as a pandas DataFrame.
    """
    # Calculate the start_date and end_date dynamically
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Call the glucose_readings function to fetch actual data
    raw_data = glucose_readings(mobile_number, start_date, end_date)
    
    # Check if there's an error in the response
    if "error" in raw_data:
        print(f"Error: {raw_data['error']}")
        return pd.DataFrame()  # Return an empty DataFrame if there's an error
    
    # Ensure that glucose_readings are in the response
    if 'glucose_readings' not in raw_data:
        print("No glucose readings found in the response.")
        return pd.DataFrame()  # Return an empty DataFrame if no glucose readings are found
    
    # Convert the JSON response to a pandas DataFrame
    glucose_df = pd.DataFrame(raw_data['glucose_readings'])
    
    # Rename the 'value' column to 'glucose' for consistency
    glucose_df.rename(columns={'value': 'glucose'}, inplace=True)
    
    # Ensure proper column types and handle any missing values
    glucose_df['timestamp'] = pd.to_datetime(glucose_df['timestamp'])
    glucose_df['glucose'] = pd.to_numeric(glucose_df['glucose'], errors='coerce')
    
    # Drop rows with invalid data
    glucose_df = glucose_df.dropna(subset=['timestamp', 'glucose'])
    
    print(glucose_df)  # Print the data for inspection
    return glucose_df

# Example call to test the ingest_data function
if __name__ == "__main__":
    mobile_number = "+918521345464"
    days = 30  # Default to the past 30 days
    
    # Test the ingest_data function
    ingest_data(mobile_number, days)
