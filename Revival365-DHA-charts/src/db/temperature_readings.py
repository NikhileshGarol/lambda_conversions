# db/body_temperature.py
from db.db_connection import Session, BodyTemperatureReadings, BleSummary
from db.UserDet import fetch_patient_details
import pandas as pd

def fetch_body_temperature_readings_for_specific_day(mobile_number, specific_date=None):
    # Fetch patient details using mobile number
    user_id, error = fetch_patient_details(mobile_number)
    
    if not user_id:  # If there's an error or no patient found
        print(f"Error fetching patient details for mobile number {mobile_number}: {error}")
        return None, error

 
    with Session() as session:
        try:
            # Query to fetch Body Temperature readings based on patient_id
            readings = (
                session.query(BodyTemperatureReadings)
                .join(BleSummary, BodyTemperatureReadings.ble_summary_id == BleSummary.id)
                .filter(BleSummary.patient_id == user_id)
                .order_by(BodyTemperatureReadings.timestamp)
                .all()
            )

            if readings:
                df = pd.DataFrame([{'timestamp': r.timestamp, 'temperature': r.temperature} for r in readings])
                
                # Ensure the 'temperature' column is numeric
                df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')

                # If a specific date is provided, filter the DataFrame
                if specific_date:
                    specific_date = pd.to_datetime(specific_date).date()  # Ensure it's a date
                    df['date'] = pd.to_datetime(df['timestamp']).dt.date
                    df = df[df['date'] == specific_date].drop(columns=['date'])  # Filter for the selected date

                return df, None  # Return the DataFrame and no error
            else:
                print(f"No Body Temperature readings found for patient_id: {user_id}")
                return pd.DataFrame(), None  # Return an empty DataFrame if no readings found

        except Exception as e:
            print(f"Error while fetching Body Temperature readings for patient_id {user_id}: {e}")
            return pd.DataFrame(), str(e)  # Return an empty DataFrame on error
