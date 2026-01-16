import pandas as pd
import json
from dateutil.tz import gettz

from db.GlucRead import get_glucose_readings_by_mobile_number
from glucose_configuration import fetch_glucose_configuration, fetch_patient_details

# Define IST timezone
IST = gettz("Asia/Kolkata")

# Global variable for fasting end time
FASTING_END_TIME = None

def get_glucose_config_by_mobile_number(mobile_no):
    global FASTING_END_TIME
    
    print("here")  # Debugging print
    
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
        fasting_end_str = config_dict.get("fasting_end_time")  # Expecting 'HH:MM:SS'
        
        if fasting_end_str:  # Ensure it's not None or empty
            FASTING_END_TIME = pd.to_datetime(fasting_end_str, format='%H:%M:%S').time()

    print(f"\n[DEBUG] FASTING_END_TIME (IST): {FASTING_END_TIME} (Type: {type(FASTING_END_TIME)})")  # Debugging
    
    return {
        "mobile_no": mobile_no,
        "glucose_configuration": config_data.to_dict(orient='records') if not config_data.empty else None
    }




def calculate_fbg(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    global FASTING_END_TIME  # Ensure we use the global variable
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Convert timestamp to datetime and assign IST timezone
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None).dt.tz_localize(IST)
    df['date'] = df['timestamp'].dt.date  # Extract date without timezone

    if isinstance(FASTING_END_TIME, str):  
        FASTING_END_TIME = pd.to_datetime(FASTING_END_TIME, format='%H:%M:%S').time()
    
    # Convert FASTING_END_TIME to a datetime object in IST
    df['fasting_end_datetime'] = df['timestamp'].dt.normalize() + pd.to_timedelta(FASTING_END_TIME.strftime('%H:%M:%S'))
    
    # Compute time difference and select the closest value to fasting end time
    df['time_diff'] = (df['fasting_end_datetime'] - df['timestamp']).dt.total_seconds().abs()
    fbg_df = df.loc[df.groupby('date')['time_diff'].idxmin()]
    fbg_df = fbg_df[['date', 'value']].rename(columns={'value': 'fbg'})

    # Add week and year for weekly aggregation
    fbg_df['date'] = pd.to_datetime(fbg_df['date'])
    fbg_df['week_number'] = fbg_df['date'].dt.isocalendar().week
    fbg_df['year'] = fbg_df['date'].dt.isocalendar().year

    # Aggregate by ISO week number and year
    weekly_fbg = fbg_df.groupby(['year', 'week_number']).agg({'fbg': 'mean'}).reset_index()
    weekly_fbg['week_label'] = weekly_fbg['week_number'].astype(str)

    return fbg_df, weekly_fbg

def construct_metadata() -> dict:
    metadata = {
        "metrics": [
            {"key": "fbg", "description": "Fasting Blood Glucose", "axis_label": "FBG (mg/dL)"}
        ],
        "x_axis_default": "date",
        "x_axis_options": {
            "day": "Day of the Week",
            "date": "Date"
        },
        "y_axis": "Value",
        "graph_titles": {
            "weekly_summary": "Weekly FBG Overview",
            "daily_details": "Daily FBG Details"
        },
        "page_title": "FBG Dashboard",
        "description": "This dashboard provides an overview of fasting blood glucose management focusing on FBG levels. Select a week to view detailed daily data.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "fbg": "#2ca02c"
        },
        "graph_dimensions": {
            "width": 1200,
            "height": 200
        },
        "interactive_features": {
            "tooltips": True,
            "zoom_enabled": True
        }
    }
    return metadata

def construct_json(daily_data: pd.DataFrame, weekly_summary: pd.DataFrame) -> dict:
    metadata = construct_metadata()
    data_list = []

    for index, week in weekly_summary.iterrows():
        week_number, year = week['week_number'], week['year']
        week_start_day = pd.to_datetime(f'{year}-W{week_number}-1', format='%G-W%V-%u').date()  # Monday
        week_end_day = week_start_day + pd.Timedelta(days=6)  # Sunday

        week_data = {
            "week_label": week['week_label'],
            "week_start_day": week_start_day.strftime("%Y-%m-%d"),
            "week_end_day": week_end_day.strftime("%Y-%m-%d"),
            "summary": {
                "fbg": int(week['fbg'])  # Change to int
            },
            "daily_data": []
        }
        week_dates = daily_data[(daily_data['week_number'] == week_number) & (daily_data['year'] == year)]
        for _, day in week_dates.iterrows():
            day_data = {
                "day": day['date'].strftime("%A"),
                "date": day['date'].strftime("%Y-%m-%d"),
                "fbg": int(day['fbg']),  # Change to int
                "description": "FBG reading for the day"
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    json_output = {
        'metadata': metadata,
        'data': data_list
    }
    return json_output

def get_weekly_data_for_date(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    Get the FBG data for the week that contains the specified date.

    Args:
        df (pd.DataFrame): DataFrame containing glucose readings with 'date', 'week_number', and 'year' columns.
        date (str): The date in the format 'YYYY-MM-DD' for which to get the weekly data.

    Returns:
        pd.DataFrame: A DataFrame containing FBG data for the specified week.
    """
    # Convert the input date to datetime
    input_date = pd.to_datetime(date)

    # Get the week number and year of the input date
    week_number = input_date.isocalendar().week
    year = input_date.isocalendar().year

    # Filter the DataFrame for the specified week and year
    weekly_data = df[(df['week_number'] == week_number) & (df['year'] == year)]

    return weekly_data[['date', 'fbg', 'week_number', 'year']]  # Return relevant columns

def fbg_trends(mobile_no: str, specific_date: str = None) -> dict:


    config = get_glucose_config_by_mobile_number(mobile_no)
    if "error" in config:
        return {"error": f"Could not fetch glucose configuration: {config['error']}"}
        
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    
    if df is not None and not df.empty:
        daily_data, weekly_summary = calculate_fbg(df)
        
        # If a specific date is provided, get the data for that week
        if specific_date:
            weekly_data = get_weekly_data_for_date(daily_data, specific_date)
            specific_week_summary = weekly_summary[
                (weekly_summary['week_number'] == weekly_data['week_number'].iloc[0]) &
                (weekly_summary['year'] == weekly_data['year'].iloc[0])
            ]
            
            if not weekly_data.empty:
                output_json = construct_json(weekly_data, specific_week_summary)  # Pass only specific week data
                print(json.dumps(output_json, indent=4))
                return output_json
            else:
                error_output = {
                    "error": "No FBG data found for the week of the specified date.",
                    "date": specific_date
                }
                print(json.dumps(error_output, indent=4))
                return error_output
        
        # In case no specific date is provided, return the full data
        output_json = construct_json(daily_data, weekly_summary)
        print(json.dumps(output_json, indent=4))
        return output_json
    else:
        # Return an error message in JSON format
        error_output = {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }
        print(json.dumps(error_output, indent=4))  # Print the error JSON
        return error_output  # Return the error JSON


if __name__ == "__main__":
    mobile_no = "+919901199334"
    specific_date = "2025-02-27"  # Example date
    fbg_trends(mobile_no, specific_date)







