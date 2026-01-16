from db.db_connection import Session, GlucoseMonitorConfigSettingMaster
import pandas as pd
import json
from decimal import Decimal

def fetch_glucose_master_configuration():
    """
    Fetch all glucose configuration data from the master table.
    
    Returns:
        tuple: A DataFrame with the glucose configuration and an error message (if any).
    """
    with Session() as session:
        try:
            # Query to fetch all records from the master table
            config_records = session.query(GlucoseMonitorConfigSettingMaster).all()
            
            if config_records:
                # Convert the records to a list of dictionaries
                config_data = []
                for record in config_records:
                    config_data.append({
                        'fasting_end_time': str(record.fasting_end_time) if record.fasting_end_time else None,
                        'breakfast_start': str(record.breakfast_start) if record.breakfast_start else None,
                        'breakfast_end': str(record.breakfast_end) if record.breakfast_end else None,
                        'lunch_start': str(record.lunch_start) if record.lunch_start else None,
                        'lunch_end': str(record.lunch_end) if record.lunch_end else None,
                        'dinner_start': str(record.dinner_start) if record.dinner_start else None,
                        'dinner_end': str(record.dinner_end) if record.dinner_end else None,
                        'dip_threshold_day': float(record.dip_threshold_day) if isinstance(record.dip_threshold_day, Decimal) else record.dip_threshold_day,
                        'dip_threshold_night': float(record.dip_threshold_night) if isinstance(record.dip_threshold_night, Decimal) else record.dip_threshold_night,
                        'spike_threshold_day': float(record.spike_threshold_day) if isinstance(record.spike_threshold_day, Decimal) else record.spike_threshold_day,
                        'spike_threshold_night': float(record.spike_threshold_night) if isinstance(record.spike_threshold_night, Decimal) else record.spike_threshold_night,
                        'time_after_spike_day': str(record.time_after_spike_day) if record.time_after_spike_day else None,
                        'day_start': str(record.day_start) if record.day_start else None,
                        'day_end': str(record.day_end) if record.day_end else None,
                        'night_start': str(record.night_start) if record.night_start else None,
                        'night_end': str(record.night_end) if record.night_end else None,
                        'spike_threshold_breakfast': float(record.spike_threshold_breakfast) if isinstance(record.spike_threshold_breakfast, Decimal) else record.spike_threshold_breakfast,
                        'spike_threshold_lunch': float(record.spike_threshold_lunch) if isinstance(record.spike_threshold_lunch, Decimal) else record.spike_threshold_lunch,
                        'spike_threshold_dinner': float(record.spike_threshold_dinner) if isinstance(record.spike_threshold_dinner, Decimal) else record.spike_threshold_dinner,
                        'spike_threshold_snack': float(record.spike_threshold_snack) if isinstance(record.spike_threshold_snack, Decimal) else record.spike_threshold_snack,
                    })
                
                # Convert the list to a DataFrame
                df = pd.DataFrame(config_data)
                return df, None
            else:
                print("No glucose master configuration found.")
                return pd.DataFrame(), None

        except Exception as e:
            print(f"Error while fetching glucose master configuration: {e}")
            return pd.DataFrame(), str(e)


def get_glucose_master_configuration_as_json():
    """
    Fetch the glucose master configuration and return as JSON.
    """
    config_data, config_error = fetch_glucose_master_configuration()
    if config_error:
        return {"error": config_error}

    return config_data.to_dict(orient='records')[0] if not config_data.empty else {}



def main():
    """
    Main function to fetch and display glucose master configuration.
    """
    result = get_glucose_master_configuration_as_json()
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
 
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
