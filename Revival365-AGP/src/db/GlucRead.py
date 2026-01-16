from db.db_connection import Session, GlucoseReadings, GlucoseDailySummary  
from db.UserDet import fetch_patient_details  # Existing function name
import pandas as pd
import random
from sqlalchemy import func
from datetime import timedelta


def fetch_glucose_readings_by_patient_id(user_id):
    """Fetch glucose readings for the last 30 days (relative to latest reading) for a given user ID."""
    print(f"Fetching glucose readings for user_id: {user_id}")
    with Session() as session:
        try:
            # Find latest reading timestamp
            latest = (
                session.query(func.max(GlucoseReadings.timestamp))
                .filter(GlucoseReadings.patient_id == user_id)
                .scalar()
            )

            if not latest:
                print(f"No readings found for user_id: {user_id}")
                return pd.DataFrame()

            cutoff = latest - timedelta(days=30)

            # Fetch only readings in the last 30 days from latest reading
            readings = (
                session.query(GlucoseReadings)
                .filter(GlucoseReadings.patient_id == user_id)
                .filter(GlucoseReadings.timestamp >= cutoff)
                .order_by(GlucoseReadings.timestamp)
                .all()
            )

            if readings:
                print(f"Found {len(readings)} readings for user_id: {user_id}")
                df = pd.DataFrame(
                    [{'timestamp': r.timestamp, 'value': r.value} for r in readings]
                )

                # Ensure the 'value' column is numeric
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df[df['value'] >= 30]  # keep only valid glucose values
                return df

            print(f"No readings found for user_id: {user_id} in last 30 days window")
            return pd.DataFrame()

        except Exception as e:
            print(f"An error occurred while fetching glucose readings for user_id {user_id}: {e}")
            return pd.DataFrame()


def fetch_glucose_readings(user_id):
    return fetch_glucose_readings_by_patient_id(user_id)


def get_glucose_readings_by_mobile_number(mobile_number):
    """Fetch glucose readings using mobile number → resolves user_id first."""
    user_id, error = fetch_patient_details(mobile_number)  
    print(user_id)
    if user_id is not None:
        df = fetch_glucose_readings(user_id)
        return df, None
    else:
        return None, error
