import pandas as pd
from db.GlucRead import get_glucose_readings_by_mobile_number
import json
from glucose_configuration import fetch_glucose_configuration, fetch_patient_details


# Configuration
DIP_THRESHOLD = ''  # Glucose value decrease that counts as a dip
DAY_START = ''  # Start of day in HH:MM format
DAY_END = ''  # End of day in HH:MM format
NIGHT_START = ''  # Start of night in HH:MM format
NIGHT_END = ''  # End of night in HH:MM format


def get_glucose_config_by_mobile_number(mobile_no):

    print("here")
     
    global DIP_THRESHOLD, NIGHT_START, NIGHT_END, DAY_START, DAY_END
    
    
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
        DIP_THRESHOLD = config_dict.get("dip_threshold_night")
        NIGHT_START = config_dict.get("night_start")
        NIGHT_END = config_dict.get("night_end")
        DAY_START = config_dict.get("day_start")
        DAY_END = config_dict.get("day_end")
        
        
        
        
         
        print("Updated Configurations:")
        print(f"DIP_THRESHOLD: {DIP_THRESHOLD}")
        print(f"NIGHT_END: {NIGHT_END}")
        print(f"DAY_START: {DAY_START}, DAY_END: {DAY_END}")
 
    
    return {
        "mobile_no": mobile_no,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }


def calculate_night_dips_and_averages(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' is datetime type

    df['value'] = df['value'].astype(int)


    # Filter data within the configured night time segments
    night_df = df.set_index('timestamp')
    morning_segment = night_df.between_time(NIGHT_START, DAY_START).reset_index()
    evening_segment = night_df.between_time(DAY_END, NIGHT_END).reset_index()
    night_df = pd.concat([morning_segment, evening_segment]).drop_duplicates()

    # Calculate daily mean glucose and identify dips for night time
    night_df['night_period'] = night_df['timestamp'].apply(lambda x: 'morning_segment' if NIGHT_START <= x.strftime('%H:%M') < DAY_START else 'evening_segment')
    daily_data = night_df.groupby(['date', 'night_period']).agg(mean_glucose=('value', 'mean')).reset_index()
    daily_data['dip_details'] = daily_data.apply(lambda row: identify_dips(night_df[(night_df['date'] == row['date']) & (night_df['night_period'] == row['night_period'])], row['mean_glucose']), axis=1)

    # Aggregate weekly dips and calculate daily average
    weekly_data = daily_data.groupby(daily_data['date'].dt.isocalendar().week).agg(
        weekly_dips=('dip_details', lambda x: sum(len(d) for d in x)),
        daily_average=('dip_details', lambda x: int(sum(len(d) for d in x) / len(x)))  # Force integer
    ).reset_index().rename(columns={'week': 'week_number'})
    weekly_data['year'] = daily_data['date'].dt.year

    return daily_data, weekly_data

def identify_dips(df, mean_glucose):
    dips = []
    in_dip = False
    dip_group = []

    for _, row in df.iterrows():
        if row['value'] < mean_glucose - DIP_THRESHOLD:
            in_dip = True
            dip_group.append(row)
        else:
            if in_dip:
                # When exiting a dip group, record the lowest reading in that group
                min_dip = min(dip_group, key=lambda x: x['value'])
                dips.append({
                    'time': min_dip['timestamp'].strftime('%H:%M'),
                    'value': int(min_dip['value']),
                    'description': f"Glucose level of {min_dip['value']} mg/dL at {min_dip['timestamp'].strftime('%H:%M')}"
                })
                dip_group = []  # Reset for the next dip
                in_dip = False

    # Handle last dip group if the data ends with a dip
    if in_dip and dip_group:
        min_dip = min(dip_group, key=lambda x: x['value'])
        dips.append({
            'time': min_dip['timestamp'].strftime('%H:%M'),
            'value': int(min_dip['value']),
            'description': f"Glucose level of {min_dip['value']} mg/dL at {min_dip['timestamp'].strftime('%H:%M')}"
        })

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
                "daily_average": int(week['daily_average'])
            },
            "daily_data": []
        }
        week_dates = daily_data[(daily_data['date'].dt.isocalendar().week == week_number) & (daily_data['date'].dt.year == year)]
        for _, day in week_dates.iterrows():
            day_data = {
                "date": day['date'].strftime("%Y-%m-%d"),
                "day": day['date'].strftime("%A"),
                "night_period": day['night_period'],
                "dips": len(day['dip_details']),
                "daily_average": week['daily_average'],
                "individual_data": day['dip_details']
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    return {
        'metadata': metadata,
        'data': data_list
    }

def construct_metadata():
    """
    Construct the complete metadata for the JSON output, tailored for glucose dip monitoring at night.
    This metadata includes y-axis configuration for the detailed graph and reflects night time monitoring.
    """
    metadata = {
        "metrics": [
            {
                "key": "dips",
                "description": "Number of Glucose Dips at Night",
                "axis_label": "Night Dips per Period"
            },
            {
                "key": "daily_average",
                "description": "Average Night Dips per Period for the week",
                "axis_label": "Avg Night Dips per Period this week"
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
            "weekly_summary": "Weekly Night Dip Overview",
            "daily_details": "Daily Night Dip Details"
        },
        "page_title": "Night Glucose Dip Monitoring Dashboard",
        "description": "This dashboard provides an overview of glucose dips below the configured threshold during night time, showcasing weekly and daily metrics. It helps users monitor the frequency of glucose dips at night and understand their nightly glucose control.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "dips": "#1f77b4"
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
 

def analyze_glucose_dips_night(mobile_no, specific_date=None):

    config = get_glucose_config_by_mobile_number(mobile_no)
    if "error" in config:
        return {"error": f"Could not fetch glucose configuration: {config['error']}"}

    df, error = get_glucose_readings_by_mobile_number(mobile_no)
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

    # Calculate night dips and averages if data is available
    daily_data, weekly_data = calculate_night_dips_and_averages(df)
    output_json = construct_dips_json(daily_data, weekly_data)
    
    print(json.dumps(output_json, indent=4))
    return output_json


if __name__ == "__main__":
    mobile_no = "+919901199334"
    analyze_glucose_dips_night(mobile_no)