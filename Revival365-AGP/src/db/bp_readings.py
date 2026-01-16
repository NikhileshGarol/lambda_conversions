# db/blood_pressure.py
from db.db_connection import Session, BloodPressureReadings, BleSummary
from db.UserDet import fetch_patient_details  # This function fetches user_id directly
import pandas as pd

def fetch_blood_pressure_readings_for_specific_day(mobile_number, specific_date=None):
    # Fetch user_id based on mobile number
    user_id, error = fetch_patient_details(mobile_number)
    
    if not user_id:  # If there's an error or no user found
        print(f"Error fetching user details for mobile number {mobile_number}: {error}")
        return None, error

    print(f"User found: {user_id} for mobile number: {mobile_number}")

    with Session() as session:
        try:
            # Query to fetch Blood Pressure readings based on user_id (previously patient_id)
            readings = (
                session.query(BloodPressureReadings)
                .join(BleSummary, BloodPressureReadings.ble_summary_id == BleSummary.id)
                .filter(BleSummary.patient_id == user_id)  # `patient_id` in BleSummary actually stores user_id
                .order_by(BloodPressureReadings.timestamp)
                .all()
            )

            if readings:
                # Convert readings to a DataFrame
                df = pd.DataFrame([{'timestamp': r.timestamp, 'systolic': r.systolic, 'diastolic': r.diastolic} for r in readings])
                
                # Ensure the 'systolic' and 'diastolic' columns are numeric
                df['systolic'] = pd.to_numeric(df['systolic'], errors='coerce')
                df['diastolic'] = pd.to_numeric(df['diastolic'], errors='coerce')

                # If a specific date is provided, filter the DataFrame
                if specific_date:
                    specific_date = pd.to_datetime(specific_date).date()  # Ensure it's a date
                    df['date'] = pd.to_datetime(df['timestamp']).dt.date
                    df = df[df['date'] == specific_date].drop(columns=['date'])  # Filter for the selected date

                return df, None  # Return the DataFrame and no error
            else:
                print(f"No Blood Pressure readings found for user_id: {user_id}")
                return pd.DataFrame(), None  # Return an empty DataFrame if no readings found

        except Exception as e:
            print(f"Error while fetching Blood Pressure readings for user_id {user_id}: {e}")
            return pd.DataFrame(), str(e)  # Return an empty DataFrame on error
