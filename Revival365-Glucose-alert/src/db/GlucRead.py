from db.db_connection import Session, GlucoseReadings, GlucoseDailySummary  
from db.UserDet import fetch_patient_details  # Existing function name
import pandas as pd
import random

def interpolate_data(df, freq='5min'):
    """Interpolate missing glucose readings to ensure regular intervals."""
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').resample(freq).mean().interpolate()  # Resample to given frequency and interpolate
    return df.reset_index()

def fetch_glucose_readings_by_patient_id(user_id):  # Function name unchanged
    """Fetch glucose readings for a given user ID (passed as patient_id in queries)."""
    print(f"Fetching glucose readings for user_id: {user_id}")
    with Session() as session:
        try:
            readings = (
                session.query(GlucoseReadings)
                 
                .filter(GlucoseReadings.patient_id == user_id)
                .order_by(GlucoseReadings.timestamp)
                .all()
            )

            if readings:
                print(f"Found {len(readings)} readings for user_id: {user_id}")
                df = pd.DataFrame([{'timestamp': r.timestamp, 'value': r.value} for r in readings])
                
                # Ensure the 'value' column is numeric
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
               # df = interpolate_data(df)  # Call to the interpolation function
                return df
            
            print(f"No readings found for user_id: {user_id}")
            return pd.DataFrame()  # Return an empty DataFrame if no readings found
        except Exception as e:
            print(f"An error occurred while fetching glucose readings for user_id {user_id}: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

def fetch_glucose_readings(user_id):  # Function name unchanged
    return fetch_glucose_readings_by_patient_id(user_id)
    
def get_glucose_readings_by_mobile_number(mobile_number):  # Function name unchanged
    user_id, error = fetch_patient_details(mobile_number)  # `fetch_patient_details` now returns user ID
    print(user_id)
    if user_id is not None:  # Check if a valid user ID is returned
        df = fetch_glucose_readings(user_id)  # Fetch using the retrieved user ID
        return df, None  # Return the DataFrame and no error
    else:
        return None, error  # Return no data and an error message
