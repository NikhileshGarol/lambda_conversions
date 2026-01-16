from db.db_connection import Session, PatientGlucoseMonitorConfigSetting
from db.UserDet import fetch_patient_details
import pandas as pd
import json
from decimal import Decimal
from datetime import time
from sqlalchemy import nullsfirst


def fetch_glucose_configuration(user_id):
    """
    Fetch the latest glucose configuration for a patient using their user ID.
    
    Args:
        user_id (int): The user ID of the patient.
    
    Returns:
        tuple: A DataFrame with the latest glucose configuration and an error message (if any).
    """
    with Session() as session:
        try:
            # Query to fetch the latest glucose configuration for the patient
            latest_config = (
                session.query(PatientGlucoseMonitorConfigSetting)
                .filter(PatientGlucoseMonitorConfigSetting.patient_id == user_id)
                .order_by(
                    # Handle NULL values in 'to_date' by converting them to a date far in the future
                    (PatientGlucoseMonitorConfigSetting.to_date.is_(None)).desc(),
                    PatientGlucoseMonitorConfigSetting.to_date.desc(), 
                    PatientGlucoseMonitorConfigSetting.id.desc()  # Ensure the latest entry by ID
                )
                .first()  # Fetch the most recent record
            )

            if latest_config:
                # Convert the latest configuration to a dictionary
                config_data = {
                    'fasting_end_time': str(latest_config.fasting_end_time) if latest_config.fasting_end_time else None,
                    'breakfast_start': str(latest_config.breakfast_start) if latest_config.breakfast_start else None,
                    'breakfast_end': str(latest_config.breakfast_end) if latest_config.breakfast_end else None,
                    'lunch_start': str(latest_config.lunch_start) if latest_config.lunch_start else None,
                    'lunch_end': str(latest_config.lunch_end) if latest_config.lunch_end else None,
                    'dinner_start': str(latest_config.dinner_start) if latest_config.dinner_start else None,
                    'dinner_end': str(latest_config.dinner_end) if latest_config.dinner_end else None,
                    'dip_threshold_day': float(latest_config.dip_threshold_day) if isinstance(latest_config.dip_threshold_day, Decimal) else latest_config.dip_threshold_day,
                    'dip_threshold_night': float(latest_config.dip_threshold_night) if isinstance(latest_config.dip_threshold_night, Decimal) else latest_config.dip_threshold_night,
                    'spike_threshold_day': float(latest_config.spike_threshold_day) if isinstance(latest_config.spike_threshold_day, Decimal) else latest_config.spike_threshold_day,
                    'spike_threshold_night': float(latest_config.spike_threshold_night) if isinstance(latest_config.spike_threshold_night, Decimal) else latest_config.spike_threshold_night,
                    'time_after_spike_day': str(latest_config.time_after_spike_day) if latest_config.time_after_spike_day else None,
                    'day_start': str(latest_config.day_start) if latest_config.day_start else None,
                    'day_end': str(latest_config.day_end) if latest_config.day_end else None,
                    'night_start': str(latest_config.night_start) if latest_config.night_start else None,
                    'night_end': str(latest_config.night_end) if latest_config.night_end else None,
                    'spike_threshold_breakfast': float(latest_config.spike_threshold_breakfast) if isinstance(latest_config.spike_threshold_breakfast, Decimal) else latest_config.spike_threshold_breakfast,
                    'spike_threshold_lunch': float(latest_config.spike_threshold_lunch) if isinstance(latest_config.spike_threshold_lunch, Decimal) else latest_config.spike_threshold_lunch,
                    'spike_threshold_dinner': float(latest_config.spike_threshold_dinner) if isinstance(latest_config.spike_threshold_dinner, Decimal) else latest_config.spike_threshold_dinner,
                    'spike_threshold_snack': float(latest_config.spike_threshold_snack) if isinstance(latest_config.spike_threshold_snack, Decimal) else latest_config.spike_threshold_snack,
                    'from_date': str(latest_config.from_date) if latest_config.from_date else None,
                    'to_date': str(latest_config.to_date) if latest_config.to_date else None,
                }

                # Convert the dictionary to a DataFrame
                df = pd.DataFrame([config_data])
                return df, None  # Return the DataFrame and no error
            else:
                print(f"No glucose configuration found for patient_id: {user_id}")
                return pd.DataFrame(), None  # Return an empty DataFrame if no configuration found

        except Exception as e:
            print(f"Error while fetching glucose configuration for patient_id {user_id}: {e}")
            return pd.DataFrame(), str(e)  # Return an empty DataFrame on error


def get_glucose_configuration_as_json(mobile_number):
    """A
    Fetch the latest glucose configuration details for a patient and return as JSON.
    """
    # Fetch the patient's ID based on mobile number
    patient_id, error = fetch_patient_details(mobile_number)
    if error or not patient_id:
        return {"error": error or "Patient not found"}

    print("Patient details fetched successfully:", patient_id)

    # Fetch the glucose configuration for the patient
    config_data, config_error = fetch_glucose_configuration(patient_id)
    if config_error:
        return {"error": config_error}

    # Prepare the JSON response
    data_json = {
        "patient_id": patient_id,
        "mobile_number": mobile_number,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }

    return data_json


def main():
    """
    Main function to fetch and display glucose configuration details for a given patient.
    """
 
    mobile_number = "+918108887421"

    # Fetch the glucose configuration data
    result = get_glucose_configuration_as_json(mobile_number)

    # Check for errors and display the data
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nGlucose Configuration Data:")
        print(json.dumps(result, indent=4))  # Pretty print the JSON data


if __name__ == "__main__":
    main()
