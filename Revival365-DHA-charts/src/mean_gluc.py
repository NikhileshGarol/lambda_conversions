import pandas as pd
import json  # Importing the json library
from db.GlucRead import get_glucose_readings_by_mobile_number

import pandas as pd

# Old V 
# def calculate_glucose_metrics(df, specific_date=None):
#     if df.empty:
#         return pd.DataFrame(), pd.DataFrame()

#     df['timestamp'] = pd.to_datetime(df['timestamp'])
#     df['date'] = df['timestamp'].dt.date

#     # Group by date and calculate metrics
#     daily_metrics = df.groupby('date').agg(
#         mean_glucose=('value', 'mean'),
#         glycemic_variability=('value', 'std')
#     ).reset_index()

#     # Add week and year for weekly aggregation
#     daily_metrics['date'] = pd.to_datetime(daily_metrics['date'])
#     daily_metrics['week_number'] = daily_metrics['date'].dt.isocalendar().week
#     daily_metrics['year'] = daily_metrics['date'].dt.isocalendar().year

#     # Filter by specific date if provided
#     if specific_date:
#         specific_date = pd.to_datetime(specific_date)
#         specific_week_number = specific_date.isocalendar().week
#         specific_year = specific_date.isocalendar().year
#         daily_metrics = daily_metrics[
#             (daily_metrics['week_number'] == specific_week_number) &
#             (daily_metrics['year'] == specific_year)
#         ]

#     # Aggregate by ISO week number and year
#     weekly_summary = daily_metrics.groupby(['year', 'week_number']).agg({
#         'mean_glucose': 'mean',
#         'glycemic_variability': 'mean'
#     }).reset_index()
#     weekly_summary['week_label'] = weekly_summary['week_number'].astype(str)

#     return daily_metrics, weekly_summary


def calculate_glucose_metrics(df: pd.DataFrame, specific_date=None):
    """
    Calculate daily and weekly glucose metrics.
    Safe against:
    - NaN timestamps
    - Empty datasets
    - ISO week conversion failures
    """

    # --- Input validation ---
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df.copy()

    # Remove invalid rows early
    df = df.dropna(subset=['timestamp', 'value'])

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # --- Datetime normalization ---
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])

    df['date'] = df['timestamp'].dt.normalize()

    # --- Daily aggregation ---
    daily_metrics = (
        df.groupby('date', as_index=False)
        .agg(
            mean_glucose=('value', 'mean'),
            glycemic_variability=('value', 'std')
        )
    )

    # Defensive fill (std can be NaN for single reading days)
    daily_metrics['mean_glucose'] = daily_metrics['mean_glucose'].fillna(0.0)
    daily_metrics['glycemic_variability'] = daily_metrics['glycemic_variability'].fillna(0.0)

    # --- ISO week extraction (safe) ---
    iso = daily_metrics['date'].dt.isocalendar()
    daily_metrics['week_number'] = iso.week.astype(int)
    daily_metrics['year'] = iso.year.astype(int)

    # --- Optional filtering by specific date ---
    if specific_date:
        specific_date = pd.to_datetime(specific_date, errors='coerce')
        if pd.notna(specific_date):
            iso_target = specific_date.isocalendar()
            daily_metrics = daily_metrics[
                (daily_metrics['week_number'] == int(iso_target.week)) &
                (daily_metrics['year'] == int(iso_target.year))
            ]

    # --- Weekly aggregation ---
    weekly_summary = (
        daily_metrics
        .groupby(['year', 'week_number'], as_index=False)
        .agg(
            mean_glucose=('mean_glucose', 'mean'),
            glycemic_variability=('glycemic_variability', 'mean')
        )
    )

    weekly_summary['week_label'] = weekly_summary['week_number'].astype(str)

    # Final NaN safeguard (API-safe)
    daily_metrics = daily_metrics.fillna(0.0)
    weekly_summary = weekly_summary.fillna(0.0)

    return daily_metrics, weekly_summary

def construct_metadata():
 
    metadata = {
        "metrics": [
            {"key": "mean_glucose", "description": "Average Daily Glucose", "axis_label": "Mean Glucose (mg/dL)"},
            {"key": "glycemic_variability", "description": "Daily Glycemic Variability", "axis_label": "Standard Deviation (mg/dL)"}
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
        "page_title": "Glucose Variability Dashboard",
        "description": "This dashboard provides an overview of weekly and daily glucose management metrics focusing on mean levels and variability. Select a week to view detailed daily data.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "mean_glucose": "#2ca02c",
            "glycemic_variability": "#ff7f0e"
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
        week_number, year = week['week_number'], week['year']
        
        week_start_day = pd.to_datetime(f'{year}-W{week_number}-1', format='%G-W%V-%u').date()  # Monday
        week_end_day = week_start_day + pd.Timedelta(days=6)  # Sunday
        week_data = {
            "week_label": week['week_label'],
            "week_start_day": week_start_day.strftime("%Y-%m-%d"),
            "week_end_day": week_end_day.strftime("%Y-%m-%d"),
            "summary": {
                "mean_glucose": int(week['mean_glucose']),  # Change to int
                "glycemic_variability": int(week['glycemic_variability'])  # Change to int
            },
            "daily_data": []
        }
        week_dates = daily_data[(daily_data['week_number'] == week_number) & (daily_data['year'] == year)]
        for _, day in week_dates.iterrows():
            day_data = {
                "day": day['date'].strftime("%A"),
                "date": day['date'].strftime("%Y-%m-%d"),
                "mean_glucose": int(day['mean_glucose']),  # Change to int
                "glycemic_variability": int(day['glycemic_variability']),  # Change to int
                "description": "Detailed glucose stats"
            }
            week_data['daily_data'].append(day_data)
        data_list.append(week_data)

    json_output = {
        'metadata': metadata,
        'data': data_list
    }
    return json_output


def glucose_trends(mobile_no, specific_date=None):
    """Fetch glucose trends based on mobile number and optional specific date."""
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }

    # Calculate metrics (weekly or for specific week)
    daily_data, weekly_summary = calculate_glucose_metrics(df, specific_date)
    
    # Construct JSON output
    output_json = construct_json(daily_data, weekly_summary)
    
 
    return output_json


if __name__ == "__main__":
    mobile_no = input("Enter mobile number: ")
    glucose_trends(mobile_no)