from db.db_connection import Session, GlucoseReadings, GlucoseDailySummary  
from db.UserDet import fetch_patient_details  # Existing function name
import pandas as pd
from datetime import datetime, timedelta

def interpolate_data(df, freq='5min'):
    """Interpolate missing glucose readings to ensure regular intervals."""
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').resample(freq).mean().interpolate()  # Resample to given frequency and interpolate
    return df.reset_index()

def fetch_glucose_readings_by_patient_id(user_id,specific_date=None ,interval=None): 
    """Fetch glucose readings for a given user ID (passed as patient_id in queries) and apply interval or specific date filter."""
    print(f"Fetching glucose readings for user_id: {user_id}")
    
    with Session() as session:
        try:
            # Base query to fetch glucose readings
            query = (
                session.query(GlucoseReadings)
                .join(GlucoseDailySummary, GlucoseReadings.glucose_daily_summary_id == GlucoseDailySummary.id)
                .filter(GlucoseDailySummary.patient_id == user_id)  # patient_id actually refers to user_id
                .order_by(GlucoseReadings.timestamp)
            )

            # Handle interval logic
            if interval:
                end_date = datetime.now().date()  # Today's date
                start_date = None
                
                if interval == 1:  # Weekly
                    start_date = end_date - timedelta(days=7)
                elif interval == 2:  # Biweekly
                    start_date = end_date - timedelta(days=14)
                elif interval == 3:  # Monthly
                    start_date = end_date - timedelta(days=30)
                else:
                    raise ValueError(f"Invalid interval: {interval}. Must be 1 (Weekly), 2 (Biweekly), or 3 (Monthly).")

                # Apply the date range filter for the interval
                print(f"Applying date range from {start_date} to {end_date}")
                query = query.filter(GlucoseReadings.timestamp.between(start_date, end_date))

            elif specific_date:  # Filter for a specific date if provided
                specific_date = pd.to_datetime(specific_date).date()
                print(f"Applying filter for specific date: {specific_date}")
                query = query.filter(GlucoseReadings.timestamp.between(specific_date, specific_date + timedelta(days=1)))

            # Fetch the results and convert them to a DataFrame
            readings = query.all()
            if readings:
                df = pd.DataFrame([
                    {'timestamp': r.timestamp, 'value': r.value}
                    for r in readings
                ])

                # Ensure the 'value' column is numeric
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
                df = interpolate_data(df)  # Call to the interpolation function
                return df
            
            print(f"No readings found for user_id: {user_id}")
            return pd.DataFrame()  # Return an empty DataFrame if no readings found
        except Exception as e:
            print(f"An error occurred while fetching glucose readings for user_id {user_id}: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error error

def fetch_glucose_readings(user_id, specific_date, interval,):  # Added interval and specific_date parameters
    return fetch_glucose_readings_by_patient_id(user_id, specific_date ,interval)

def get_glucose_readings_by_mobile_number(mobile_number, specific_date ,interval):  # Added interval and specific_date parameters
    user_id, error = fetch_patient_details(mobile_number)  # `fetch_patient_details` now returns user ID
    if user_id is not None:  # Check if a valid user ID is returned
        df = fetch_glucose_readings(user_id,specific_date, interval)  # Fetch using the retrieved user ID
        return df, None  # Return the DataFrame and no error
    else:
        return None, error  # Return no data and an error message
