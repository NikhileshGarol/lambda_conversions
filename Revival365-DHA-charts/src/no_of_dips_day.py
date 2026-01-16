import pandas as pd
from db.GlucRead import get_glucose_readings_by_mobile_number
import json
from glucose_configuration import fetch_glucose_configuration, fetch_patient_details


# Configuration
DIP_THRESHOLD = ''  # Glucose value decrease below mean that counts as a dip
SPIKE_THRESHOLD = ''  # Glucose value increase above mean that counts as a spike
TIME_AFTER_SPIKE = ''  # Time window after a spike to look for a dip
DAY_START = ''  # Start of day in HH:MM format
DAY_END = ''  # End of day in HH:MM format


def get_glucose_config_by_mobile_number(mobile_no):

    print("here")
     
    global DIP_THRESHOLD, SPIKE_THRESHOLD, TIME_AFTER_SPIKE, DAY_START, DAY_END
    
    
     # Fetch the patient's ID based on mobile number
    patient_id, error = fetch_patient_details(mobile_no)
    if error or not patient_id:
        return {"error": f"Patient not found for mobile: {mobile_no}"}
    
    # Fetch glucose configuration
    config_data, config_error = fetch_glucose_configuration(patient_id)
    if config_error:
        return {"error": config_error}
    
    if not config_data.empty:
        config_dict = config_data.to_dict(orient='records')[0]
        
        # Update global variables
        DIP_THRESHOLD = config_dict.get("dip_threshold_day")
        SPIKE_THRESHOLD = config_dict.get("spike_threshold_day")
        TIME_AFTER_SPIKE = config_dict.get("time_after_spike_day")
        DAY_START = config_dict.get("day_start")
        DAY_END = config_dict.get("day_end")
        
        
        
        
         
        print("Updated Configurations:")
        print(f"DIP_THRESHOLD: {DIP_THRESHOLD}")
        print(f"SPIKE_THRESHOLD: {SPIKE_THRESHOLD}")
        print(f"DAY_START: {DAY_START}, DAY_END: {DAY_END}")
        print("TIME_AFTER_SPIKE:", TIME_AFTER_SPIKE)
    
    return {
        "mobile_no": mobile_no,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }




def calculate_dips_and_averages(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    df = df.set_index('timestamp').between_time(DAY_START, DAY_END).reset_index()

    # Aggregate daily data
    daily_data = df.groupby('date').agg(mean_glucose=('value', 'mean')).reset_index()
    daily_data['dip_details'] = daily_data.apply(
        lambda row: identify_dips(df[df['date'] == row['date']], row['mean_glucose']), axis=1)
    
    daily_data['dips'] = daily_data['dip_details'].apply(lambda x: len(x))

    # Weekly summary
    daily_data['week'] = daily_data['date'].dt.isocalendar().week
    daily_data['year'] = daily_data['date'].dt.isocalendar().year
    weekly_data = daily_data.groupby(['year', 'week']).agg(
        weekly_dips=('dips', 'sum'),
        weekly_average_dips=('dips', lambda x: int(round(x.mean())))
    ).reset_index().rename(columns={'week': 'week_number'})

    return daily_data, weekly_data

def identify_dips(df, mean_glucose):
    dips = []
    spike_time = None  # Track the time when a spike occurs
    debug_info = []  # Collect debugging information

    for _, row in df.iterrows():
        current_time = row['timestamp']
        current_value = row['value']
        
        # Check for spike
        if current_value > mean_glucose + SPIKE_THRESHOLD:
            spike_time = current_time
           # debug_info.append(f"Spike detected: {current_value} at {current_time}")
        
        # Check for dip within the time window after a spike
        if spike_time:
            if (current_time - spike_time <= pd.Timedelta(TIME_AFTER_SPIKE)):
                if current_value < mean_glucose - DIP_THRESHOLD:
                    dips.append({
                        'time': current_time.strftime('%H:%M'),
                        'glucose_reading': current_value,  # Store the actual glucose reading at the dip
                        'description': f"Glucose level dipped to {current_value} mg/dL at {current_time.strftime('%H:%M')}"
                    })
 
                    spike_time = None  # Reset spike time after recording a dip

    
    return dips


def construct_dips_json(daily_data, weekly_data):
    metadata = construct_metadata()
    data_list = []

    for index, week in weekly_data.iterrows():
        week_number, year = week['week_number'], week['year']
        week_start_day = pd.to_datetime(f'{year}-W{week_number}-1', format='%G-W%V-%u').date()  # Monday
        week_end_day = week_start_day + pd.Timedelta(days=6)  # Sunday
        week_data = {
            "week_label": f"{week_number}",
            "week_start_day": week_start_day.strftime("%Y-%m-%d"),
            "week_end_day": week_end_day.strftime("%Y-%m-%d"),
            "summary": {
                "dips": week['weekly_dips'],
                "weekly_average_dips": week['weekly_average_dips']
            },
            "daily_data": []
        }
        # Extract the corresponding daily data within the week
        week_dates = daily_data[(daily_data['week'] == week_number) & (daily_data['year'] == year)]
        for _, day in week_dates.iterrows():
            day_data = {
                "date": day['date'].strftime("%Y-%m-%d"),
                "day": day['date'].strftime("%A"),
                "dips": day['dips'],
                "weekly_average_dips": week['weekly_average_dips'] if day['dips'] > 0 else 0,  # Weekly average dips also listed daily for reference
                "individual_data": day['dip_details'] if day['dips'] > 0 else []
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    return {
        'metadata': metadata,
        'data': data_list
    }

def construct_metadata():
    metadata = {
        "metrics": [
            {
                "key": "dips",
                "description": "Number of Glucose Dips",
                "axis_label": "Dips per Day"
            },
            {
                "key": "weekly_average_dips",
                "description": "Average number of glucose dips per day for the week",
                "axis_label": "Avg Dips per Day"
            }
        ],
        "x_axis_default": "date",
        "x_axis_options": {
            "day": "Day of the Week",
            "date": "Date"
        },
        "y_axis": "Count",
        "y_axis_range": {
            "min": 0,
            "max": 10
        },
        "graph_titles": {
            "weekly_summary": "Weekly Overview of Glucose Dips",
            "daily_details": "Daily Glucose Dip Details",
            "detailed_view": "Individual Glucose Dips"
        },
        "page_title": "Glucose Dip Monitoring Dashboard(Day)",
        "description": "This dashboard provides an overview of glucose dips below the configured threshold, showcasing weekly, daily, and detailed individual metrics.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "dips": "#4287f5"
        },
        "graph_dimensions": {
            "width": 1200,
            "height": 300
        },
        "interactive_features": {
            "tooltips": True,
            "zoom_enabled": True
        }
    }
    return metadata

def analyze_glucose_dips_day(mobile_no, specific_date=None):


    config = get_glucose_config_by_mobile_number(mobile_no)
    if "error" in config:
        return {"error": f"Could not fetch glucose configuration: {config['error']}"}

    df, error = get_glucose_readings_by_mobile_number(mobile_no)

    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }

    # Convert 'timestamp' to datetime if not already
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if specific_date:
        specific_date = pd.to_datetime(specific_date).date()  # Ensure the date is in the correct format
        
        # Find the start and end of the week containing the specific date
        week_start = specific_date - pd.Timedelta(days=specific_date.weekday())  # Monday as start of the week
        week_end = week_start + pd.Timedelta(days=6)  # Sunday as end of the week
        
        # Filter the dataframe to include only the records for that week
        df = df[(df['timestamp'].dt.date >= week_start) & (df['timestamp'].dt.date <= week_end)]

    if not df.empty:
        daily_data, weekly_data = calculate_dips_and_averages(df)  # Calculate dips and averages

        # Construct the output JSON using the data for the specific week
        output_json = construct_dips_json(daily_data, weekly_data)

        print(json.dumps(output_json, indent=4))
    else:
        print(f"No glucose data found for the given mobile number in the week containing {specific_date}.")
        output_json = {"error": f"No glucose data found in the week containing {specific_date}."}  # Initialize output_json here
    
    return output_json


if __name__ == "__main__":
    mobile_no = "+918108887421"
    analyze_glucose_dips_day(mobile_no)