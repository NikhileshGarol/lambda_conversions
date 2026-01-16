import pandas as pd
import numpy as np
from db.GlucRead import get_glucose_readings_by_mobile_number



def calculate_metrics(df, low_threshold, high_threshold):

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Convert timestamps to datetime and extract date
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    # Group by date and calculate daily metrics
    daily_metrics = df.groupby('date').apply(lambda x: pd.Series({
        "time_in_range": ((x['value'] >= low_threshold) & (x['value'] <= high_threshold)).mean() * 100,
        "time_above_range": (x['value'] > high_threshold).mean() * 100,
        "time_below_range": (x['value'] < low_threshold).mean() * 100,
        "mean_glucose": x['value'].mean()
    })).reset_index()

    # Prepare for weekly aggregation by adding ISO week number
    daily_metrics['date'] = pd.to_datetime(daily_metrics['date'])
    daily_metrics['week_number'] = daily_metrics['date'].dt.isocalendar().week
    daily_metrics['year'] = daily_metrics['date'].dt.isocalendar().year

    # Aggregation by ISO week number and year
    weekly_summary = daily_metrics.groupby(['year', 'week_number']).agg({
        'time_in_range': 'mean',
        'time_above_range': 'mean',
        'time_below_range': 'mean',
        'mean_glucose': 'mean'
    }).reset_index()

    weekly_summary['week_label'] = weekly_summary['week_number'].astype(str)

 
    return daily_metrics, weekly_summary


def construct_metadata():
    """Construct the complete metadata for the JSON output."""
    metadata = {
        "metrics": [
            {"key": "time_in_range", "description": "Time in Range", "axis_label": "% Time in Range"},
            {"key": "time_above_range", "description": "Time Above Range", "axis_label": "% Time Above Range"},
            {"key": "time_below_range", "description": "Time Below Range", "axis_label": "% Time Below Range"},
            {"key": "mean_glucose", "description": "Average Glucose", "axis_label": "Mean Glucose (mg/dL)"}
        ],
        "x_axis_default": "date",
        "x_axis_options": {
            "day": "Day of the Week",
            "date": "Date"
        },
        "y_axis": "Value",
        "graph_titles": {
            "weekly_summary": "Weekly Glucose Overview",
            "daily_details": "Daily Glucose Details"
        },
        "page_title": "TIR view",
        "description": "This dashboard provides an overview of weekly and daily glucose management metrics. Select a week to view detailed daily data.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "time_in_range": "#2ca02c",
            "time_above_range": "#ff7f0e",
            "time_below_range": "#1f77b4",
            "mean_glucose": "#9467bd"
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

def construct_json(daily_data, weekly_summary):
    metadata = construct_metadata()
    data_list = []

    for index, week in weekly_summary.iterrows():
        # Correct parsing of the week label
        week_number = int(week['week_label'])
        week_number = int(week['week_label'])
        year = int(week['year'])  # Ensure year is stored before dropping
        
        # Calculate the start and end of the week correctly
        week_start_day = pd.to_datetime(f"{year}-W{week_number:02d}-1", format="%G-W%V-%u").date()
        week_end_day = week_start_day + pd.Timedelta(days=6)
        week_data = {
            "week_label": week['week_label'],
            "week_start_day": week_start_day.strftime("%Y-%m-%d"),
            "week_end_day": week_end_day.strftime("%Y-%m-%d"),
            "summary": {
                "time_in_range": int(week['time_in_range']),
                "time_above_range": int(week['time_above_range']),
                "time_below_range": int(week['time_below_range']),
                "mean_glucose": int(week['mean_glucose'])
            },
            "daily_data": []
        }
        # Corrected filtering for week dates
        week_dates = daily_data[daily_data['date'].dt.isocalendar().week == week_number]

        for _, day in week_dates.iterrows():
            day_data = {
                "day": day['date'].strftime("%A"),
                "date": day['date'].strftime("%Y-%m-%d"),
                "time_in_range": int(day['time_in_range']),
                "time_above_range": int(day['time_above_range']),
                "time_below_range": int(day['time_below_range']),
                "mean_glucose": int(day['mean_glucose']),
                "description": "Detailed glucose stats"
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    json_output = {
        'metadata': metadata,
        'data': data_list
    }
    return json_output


'''
def tir_Trends(mobile_no):
    """Main function to orchestrate the fetching and processing of glucose data."""
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }
    if not df.empty:
        daily_data, weekly_summary = calculate_metrics(df, 70, 150)
        output_json = construct_json(daily_data, weekly_summary)
        print(output_json)
    else:
        print("No glucose data found for the given patient ID.")
    return output_json

'''


def tir_Trends(mobile_no, specific_date):
    """Main function to orchestrate the fetching and processing of glucose data."""
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }
    
    if specific_date:
        specific_date = pd.to_datetime(specific_date).date()
        # Calculate the start and end of the week
        start_of_week = specific_date - pd.Timedelta(days=specific_date.weekday())
        end_of_week = start_of_week + pd.Timedelta(days=6)

        # Filter the DataFrame to include only the data for the week containing the specific date
        df = df[(pd.to_datetime(df['timestamp']).dt.date >= start_of_week) &
                (pd.to_datetime(df['timestamp']).dt.date <= end_of_week)]

    daily_data, weekly_summary = calculate_metrics(df, 70, 150)
    output_json = construct_json(daily_data, weekly_summary)
    return output_json




if __name__ == "__main__":
    mobile_no = input("Enter mobile number ")
    tir_Trends(mobile_no)


