from db.db_connection import Session, BloodPressureReadings, BleSummary
from db.UserDet import fetch_patient_details  # This function fetches user_id directly
import pandas as pd
from datetime import datetime, timedelta

def fetch_blood_pressure_readings_for_specific_day(mobile_number, specific_date=None, interval=None):
    """
    Fetch blood pressure readings for a specific day or a range of days based on the interval.
    
    Args:
        mobile_number (str): User's mobile number to fetch details.
        specific_date (str): (Optional) Specific date in 'YYYY-MM-DD' format.
        interval (int): (Optional) Interval for fetching data:
                        1 - Last 7 days (Weekly),
                        2 - Last 14 days (Biweekly),
                        3 - Last 30 days (Monthly).
    
    Returns:
        tuple: A DataFrame of blood pressure readings and an error message (if any).
    """
    # Fetch user_id based on mobile number
    user_id, error = fetch_patient_details(mobile_number)
    
    if not user_id:  # If there's an error or no user found
        print(f"Error fetching user details for mobile number {mobile_number}: {error}")
        return None, error

    print(f"User found: {user_id} for mobile number: {mobile_number}")

    with Session() as session:
        try:
            # Base query to fetch Blood Pressure readings
            query = (
                session.query(BloodPressureReadings)
                .join(BleSummary, BloodPressureReadings.ble_summary_id == BleSummary.id)
                .filter(BleSummary.patient_id == user_id)  # `patient_id` in BleSummary stores user_id
            )

            # Calculate date range if interval is provided
            if interval:
                end_date = datetime.now().date()  # Today's date
                if interval == 1:  # Weekly
                    start_date = end_date - timedelta(days=7)
                elif interval == 2:  # Biweekly
                    start_date = end_date - timedelta(days=14)
                elif interval == 3:  # Monthly
                    start_date = end_date - timedelta(days=30)
                else:
                    raise ValueError(f"Invalid interval: {interval}. Must be 1 (Weekly), 2 (Biweekly), or 3 (Monthly).")
                
                query = query.filter(BloodPressureReadings.timestamp.between(start_date, end_date))
            elif specific_date:  # Filter for a specific date if provided
                specific_date = pd.to_datetime(specific_date).date()
                query = query.filter(BloodPressureReadings.timestamp.between(specific_date, specific_date + timedelta(days=1)))

            # Fetch the results and convert them to a DataFrame
            readings = query.order_by(BloodPressureReadings.timestamp).all()
            if readings:
                df = pd.DataFrame([
                    {
                        'timestamp': r.timestamp,
                        'systolic': r.systolic,
                        'diastolic': r.diastolic
                    }
                    for r in readings
                ])

                # Ensure the 'systolic' and 'diastolic' columns are numeric
                df['systolic'] = pd.to_numeric(df['systolic'], errors='coerce')
                df['diastolic'] = pd.to_numeric(df['diastolic'], errors='coerce')

                return df, None  # Return the DataFrame and no error
            else:
                print(f"No Blood Pressure readings found for user_id: {user_id}")
                return pd.DataFrame(), None  # Return an empty DataFrame if no readings found

        except Exception as e:
            print(f"Error while fetching Blood Pressure readings for user_id {user_id}: {e}")
            return pd.DataFrame(), str(e)  # Return an empty DataFrame on error
