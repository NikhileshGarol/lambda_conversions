import pandas as pd
from db.GlucRead import get_glucose_readings_by_mobile_number
import json
from glucose_configuration import fetch_glucose_configuration, fetch_patient_details
from datetime import datetime, timedelta
# Configuration
BREAKFAST_START = ''
BREAKFAST_END = ' '
LUNCH_START = ' '
LUNCH_END = ' '
DINNER_START = ' '
DINNER_END = ' '

SPIKE_THRESHOLDS = {
    'breakfast': 0,
    'lunch': 0,
    'dinner': 0,
    'snack': 0
}




def get_glucose_config_by_mobile_number(mobile_no):

    print("here")
    """
    Fetch glucose configuration for a patient using their mobile number.
    
    Args:
        mobile_no (str): The patient's mobile number.
    
    Returns:
        dict: Glucose configuration details or an error message.
    """
    global BREAKFAST_START, BREAKFAST_END, LUNCH_START, LUNCH_END, DINNER_START, DINNER_END, SPIKE_THRESHOLDS
    
    
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
        BREAKFAST_START = config_dict.get("breakfast_start")
        BREAKFAST_END = config_dict.get("breakfast_end")
        LUNCH_START = config_dict.get("lunch_start")
        LUNCH_END = config_dict.get("lunch_end")
        DINNER_START = config_dict.get("dinner_start")
        DINNER_END = config_dict.get("dinner_end")

        
        
        
        
        SPIKE_THRESHOLDS = {
            'breakfast': config_dict.get("spike_threshold_breakfast"),
            'lunch': config_dict.get("spike_threshold_lunch"),
            'dinner': config_dict.get("spike_threshold_dinner"),
            'snack': config_dict.get("spike_threshold_snack")
        }
        
        print("Updated Configurations:")
        print(f"BREAKFAST_START: {BREAKFAST_START}, BREAKFAST_END: {BREAKFAST_END}")
        print(f"LUNCH_START: {LUNCH_START}, LUNCH_END: {LUNCH_END}")
        print(f"DINNER_START: {DINNER_START}, DINNER_END: {DINNER_END}")
        print("SPIKE_THRESHOLDS:", SPIKE_THRESHOLDS)
    
    return {
        "mobile_no": mobile_no,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }

def calculate_spikes_and_averages(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    df = df.set_index('timestamp').between_time('00:00', '23:59').reset_index()

    # Aggregate daily data
    daily_data = df.groupby('date').agg(mean_glucose=('value', 'mean')).reset_index()
    daily_data['spike_details'] = daily_data.apply(
        lambda row: identify_spikes(df[df['date'] == row['date']], row['mean_glucose']), axis=1)
    
    for period in SPIKE_THRESHOLDS.keys():
        daily_data[f'{period}_spikes'] = daily_data['spike_details'].apply(lambda x: len(x[period]))

    # Weekly summary
    daily_data['week'] = daily_data['date'].dt.isocalendar().week
    daily_data['year'] = daily_data['date'].dt.isocalendar().year
    weekly_data = daily_data.groupby(['year', 'week']).agg(
        breakfast_spikes=('breakfast_spikes', 'sum'),
        lunch_spikes=('lunch_spikes', 'sum'),
        dinner_spikes=('dinner_spikes', 'sum'),
        snack_spikes=('snack_spikes', 'sum'),
        weekly_average_spikes=('spike_details', lambda x: sum(len(v['breakfast']) + len(v['lunch']) + len(v['dinner']) + len(v['snack']) for v in x) / len(x))
    ).reset_index().rename(columns={'week': 'week_number'})

    return daily_data, weekly_data

def identify_spikes(df, mean_glucose):
    spikes = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
    active_spike = {period: False for period in SPIKE_THRESHOLDS.keys()}  
    current_spike = {period: None for period in SPIKE_THRESHOLDS.keys()}  

    for _, row in df.iterrows():
        current_time = row['timestamp']
        current_value = row['value']

        # Determine the period (passing next meal start time to prevent overlap)
        if is_within_time_range(current_time, BREAKFAST_START, BREAKFAST_END, LUNCH_START):
            period = 'breakfast'
        elif is_within_time_range(current_time, LUNCH_START, LUNCH_END, DINNER_START):
            period = 'lunch'
        elif is_within_time_range(current_time, DINNER_START, DINNER_END):
            period = 'dinner'
        else:
            period = 'snack'

        threshold = SPIKE_THRESHOLDS[period]

        if current_value > mean_glucose + threshold:
            if not active_spike[period]:  
                current_spike[period] = {
                    'time': current_time.strftime('%H:%M'),
                    'value': current_value,
                    'above_mean': current_value - mean_glucose
                }
                active_spike[period] = True  
            else:
                if current_value > current_spike[period]['value']:
                    current_spike[period] = {
                        'time': current_time.strftime('%H:%M'),
                        'value': current_value,
                        'above_mean': current_value - mean_glucose
                    }

        else:
            if active_spike[period]:  
                spike_details = {
                    'time': current_spike[period]['time'],
                    'value': current_spike[period]['value'],
                    'above_mean': current_spike[period]['above_mean'],
                    'description': f"{period.capitalize()} spike to {current_spike[period]['value']} mg/dL ({current_spike[period]['above_mean']} mg/dL above mean) at {current_spike[period]['time']}"
                }
                spikes[period].append(spike_details)
                current_spike[period] = None  
                active_spike[period] = False  

    return spikes



def is_within_time_range(time, start, end, next_start=None):
 

    # Convert "HH:MM:SS" → "HH:MM" by slicing the first 5 characters
    start = start[:5]
    end = end[:5]
    if next_start:
        next_start = next_start[:5]

    # Convert to time objects
    start_time = datetime.strptime(start, "%H:%M").time()
    end_time = datetime.strptime(end, "%H:%M").time()

    # Extend end time by 1 hour
    extended_end_time = (datetime.combine(datetime.today(), end_time) + timedelta(hours=1)).time()

    if next_start:
        next_start_time = datetime.strptime(next_start, "%H:%M").time()
        extended_end_time = min(extended_end_time, next_start_time)

    return start_time <= time.time() <= extended_end_time  # Ensure boundary cases are included


 

def get_weekly_data_for_date(df, date):
    """
    Get glucose data for the week that contains the specified date.

    Args:
        df (pd.DataFrame): DataFrame with glucose readings.
        date (str): The date in 'YYYY-MM-DD' format for which to get the weekly data.

    Returns:
        pd.DataFrame: DataFrame containing data for the specified week.
    """
    input_date = pd.to_datetime(date)
    week_number = input_date.isocalendar().week
    year = input_date.isocalendar().year
    weekly_data = df[(df['week'] == week_number) & (df['year'] == year)]
    return weekly_data




def construct_spikes_json(daily_data, weekly_data):
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
                "breakfast_spikes": int(week['breakfast_spikes']),
                "lunch_spikes": int(week['lunch_spikes']),
                "dinner_spikes": int(week['dinner_spikes']),
                "snack_spikes": int(week['snack_spikes']),
                "weekly_average_spikes": int(round(week['weekly_average_spikes']))  # Convert float to int
            },
            "daily_data": []
        }
        # Extract the corresponding daily data within the week
        week_dates = daily_data[(daily_data['week'] == week_number) & (daily_data['year'] == year)]
        for _, day in week_dates.iterrows():
            day_data = {
                "date": day['date'].strftime("%Y-%m-%d"),
                "day": day['date'].strftime("%A"),
                "breakfast_spikes": int(1 if day['spike_details']['breakfast'] else 0),  # Ensure integer
                "lunch_spikes": int(1 if day['spike_details']['lunch'] else 0),         # Ensure integer
                "dinner_spikes": int(1 if day['spike_details']['dinner'] else 0),       # Ensure integer
                "snack_spikes": int(len(day['spike_details']['snack'])),                # Ensure integer
                "individual_data": [
                    {
                        "time": item['time'],
                        "value": int(item['value']),                # Convert float value to int
                        "above_mean": int(item['above_mean']),      # Convert above_mean to int
                        "description": item['description']
                    } for item in day['spike_details']['breakfast'] + day['spike_details']['lunch'] + day['spike_details']['dinner'] + day['spike_details']['snack']
                ]
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
                "key": "breakfast_spikes",
                "description": "Number of Breakfast Spikes",
                "axis_label": "Spikes per Week"
            },
            {
                "key": "lunch_spikes",
                "description": "Number of Lunch Spikes",
                "axis_label": "Spikes per Week"
            },
            {
                "key": "dinner_spikes",
                "description": "Number of Dinner Spikes",
                "axis_label": "Spikes per Week"
            },
            {
                "key": "snack_spikes",
                "description": "Number of Snack Spikes",
                "axis_label": "Spikes per Day"
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
            "weekly_summary": "Weekly Overview of Glucose Spikes",
            "daily_details": "Daily Glucose Spike Details",
            "detailed_view": "Individual Glucose Spikes"
        },
        "page_title": "Meal Spike Monitoring Dashboard",
        "description": "This dashboard provides an overview of glucose spikes above the configured thresholds, showcasing weekly, daily, and detailed individual metrics.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "breakfast_spikes": "#4287f5",
            "lunch_spikes": "#ff7f0e",
            "dinner_spikes": "#2ca02c",
            "snack_spikes": "#d62728"
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

def analyze_glucose_spikes(mobile_no, specific_date=None):
    config = get_glucose_config_by_mobile_number(mobile_no)
    if "error" in config:
        return {"error": f"Could not fetch glucose configuration: {config['error']}"}
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }

    daily_data, weekly_data = calculate_spikes_and_averages(df)
    
    if specific_date:
        weekly_data_filtered = get_weekly_data_for_date(daily_data, specific_date)
        if weekly_data_filtered.empty:
            return {
                "error": "No glucose data found for the specified date.",
                "date": specific_date
            }
        specific_week_summary = weekly_data[
            (weekly_data['week_number'] == weekly_data_filtered['week'].iloc[0]) & 
            (weekly_data['year'] == weekly_data_filtered['year'].iloc[0])
        ]
        output_json = construct_spikes_json(weekly_data_filtered, specific_week_summary)
    else:
        output_json = construct_spikes_json(daily_data, weekly_data)

    print(json.dumps(output_json, indent=4))
    return output_json

if __name__ == "__main__":
    mobile_no = "+919901199334"
    analyze_glucose_spikes(mobile_no)