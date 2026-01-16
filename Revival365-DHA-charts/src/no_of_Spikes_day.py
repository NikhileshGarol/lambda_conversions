import pandas as pd
from db.GlucRead import get_glucose_readings_by_mobile_number
import json
from glucose_configuration import fetch_glucose_configuration, fetch_patient_details
# Configuration
SPIKE_THRESHOLD = ''  # Glucose value increase that counts as a spike
DAY_START = ''  # Start of day in HH:MM format
DAY_END = ''  # End of day in HH:MM format

def get_glucose_config_by_mobile_number(mobile_no):

    print("here")
     
    global SPIKE_THRESHOLD,DAY_START, DAY_END
    
    
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
        SPIKE_THRESHOLD = config_dict.get("spike_threshold_day")
     
        DAY_START = config_dict.get("day_start")
        DAY_END = config_dict.get("day_end")
        
        
        
        
         
        print("Updated Configurations:")
        print(f"SPIKE_THRESHOLD: {SPIKE_THRESHOLD}")
 
        print(f"DAY_START: {DAY_START}, DAY_END: {DAY_END}")
 
    
    return {
        "mobile_no": mobile_no,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }



def calculate_spikes_and_averages(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' is datetime type

    # Filter data within the configured daily start and end times
    df = df.set_index('timestamp').between_time(DAY_START, DAY_END).reset_index()

    # Calculate daily mean glucose and identify spikes
    daily_data = df.groupby('date').agg(mean_glucose=('value', 'mean')).reset_index()
    daily_data['spike_details'] = daily_data.apply(lambda row: identify_spikes(df[df['date'] == row['date']], row['mean_glucose']), axis=1)

    # Aggregate weekly spikes and calculate daily average
    weekly_data = daily_data.groupby(daily_data['date'].dt.isocalendar().week).agg(
        weekly_spikes=('spike_details', lambda x: sum(len(d) for d in x)),
        daily_average=('spike_details', lambda x: int(sum(len(d) for d in x) / len(x)))  # Convert to int here
    ).reset_index().rename(columns={'week': 'week_number'})
    weekly_data['year'] = daily_data['date'].dt.year

    return daily_data, weekly_data

def identify_spikes(df, mean_glucose):
    spikes = []
    in_spike = False
    spike_group = []

    for _, row in df.iterrows():
        if row['value'] > mean_glucose + SPIKE_THRESHOLD:
            in_spike = True
            spike_group.append(row)
        else:
            if in_spike:
                # When exiting a spike group, record the highest reading in that group
                max_spike = max(spike_group, key=lambda x: x['value'])
                spikes.append({
                    'time': max_spike['timestamp'].strftime('%H:%M'),
                    'value': int(max_spike['value']),
                    'description': f"Glucose level of {max_spike['value']} mg/dL at {max_spike['timestamp'].strftime('%H:%M')}"
                })
                spike_group = []  # Reset for the next spike
                in_spike = False

    # Handle last spike group if the data ends with a spike
    if in_spike and spike_group:
        max_spike = max(spike_group, key=lambda x: x['value'])
        spikes.append({
            'time': max_spike['timestamp'].strftime('%H:%M'),
            'value': int(max_spike['value']),
            'description': f"Glucose level of {max_spike['value']} mg/dL at {max_spike['timestamp'].strftime('%H:%M')}"
        })

    return spikes


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
                "spikes": week['weekly_spikes'],
                "daily_average": week['daily_average']
            },
            "daily_data": []
        }
        week_dates = daily_data[(daily_data['date'].dt.isocalendar().week == week_number) & (daily_data['date'].dt.year == year)]
        for _, day in week_dates.iterrows():


            day_spikes = len(day['spike_details'])  # Number of spikes for the day
            daily_average = day_spikes  # The daily average will just be the count of spikes for that day

            # If there are no spikes for the day, set daily_average to 0
            daily_average = daily_average if day_spikes > 0 else 0
            day_data = {
                "date": day['date'].strftime("%Y-%m-%d"),
                "day": day['date'].strftime("%A"),
                "spikes": len(day['spike_details']),
                "daily_average": daily_average,
                "individual_data": day['spike_details']
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    return {
        'metadata': metadata,
        'data': data_list
    }

def construct_metadata():
    """
    Construct the complete metadata for the JSON output, tailored for glucose spike monitoring.
    This metadata now includes y-axis configuration for the detailed graph.
    """
    metadata = {
        "metrics": [
            {
                "key": "spikes",
                "description": "Number of Glucose Spikes",
                "axis_label": "Spikes per Day"
            },
            {
                "key": "daily_average",
                "description": "Average Glucose Spikes per day for the week",
                "axis_label": "Avg Spikes per Day this week"
            }
        ],
        "x_axis_default": "date",
        "x_axis_options": {
            "day": "Day of the Week",
            "date": "Date"
        },
        "y_axis": "Count",
        "y_axis_range": {  # Added to define fixed range for the y-axis in the detailed view
            "min": 0,
            "max": 200
        },
        "graph_titles": {
            "weekly_summary": "Weekly Spike Overview",
            "daily_details": "Daily Spike Details"
        },
        "page_title": "Glucose Spike Monitoring Dashboard(Day)",
        "description": "This dashboard provides an overview of glucose spikes above the configured threshold, showcasing weekly and daily metrics. It helps users monitor the frequency of glucose spikes and understand their daily glucose control.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "spikes": "#d62728"
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



'''
def analyze_glucose_spikes_day(mobile_no):
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }
    
    if df is not None:
        daily_data, weekly_data = calculate_spikes_and_averages(df)
        output_json = construct_spikes_json(daily_data, weekly_data)
#       print(output_json)
        print(json.dumps(output_json, indent=4)) 
    else:
        print(f"No glucose data found for the given mobile number: {error}")
        print(mobile_no)
    return output_json
'''
def analyze_glucose_spikes_day(mobile_no, specific_date=None):
    df, error = get_glucose_readings_by_mobile_number(mobile_no)

    config = get_glucose_config_by_mobile_number(mobile_no)
    if "error" in config:
        return {"error": f"Could not fetch glucose configuration: {config['error']}"}
    
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }

    # Convert 'timestamp' to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if specific_date:
        specific_date = pd.to_datetime(specific_date).date()
        
        # Find the start and end of the week containing the specific date
        week_start = specific_date - pd.Timedelta(days=specific_date.weekday())
        week_end = week_start + pd.Timedelta(days=6)
        
        # Filter the dataframe to include only the records for that week
        df = df[(df['timestamp'].dt.date >= week_start) & (df['timestamp'].dt.date <= week_end)]
        
        if df.empty:
            return {"error": f"No glucose data found in the week containing {specific_date}."}

    # Calculate spikes and averages
    daily_data, weekly_data = calculate_spikes_and_averages(df)
    output_json = construct_spikes_json(daily_data, weekly_data)
    
    print(json.dumps(output_json, indent=4))
    return output_json


if __name__ == "__main__":
    mobile_no = input("Enter mobile number: ")
    analyze_glucose_spikes_day(mobile_no)