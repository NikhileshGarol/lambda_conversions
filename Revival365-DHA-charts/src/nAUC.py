import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from db.GlucRead import get_glucose_readings_by_mobile_number
import json


import pandas as pd
import numpy as np

# Old V 
# def calculate_auc(df, dx=5):
#     """Calculate the Area Under the Curve (AUC) using the trapezoidal rule."""
#     return np.trapezoid(df['value'], dx=dx)  # np.trapz is numpy's trapezoidal rule


# def calculate_metrics(df):
#     """Calculate daily and weekly metrics."""
#     df['date'] = pd.to_datetime(df['timestamp']).dt.date
#     daily_data = df.groupby('date').apply(lambda x: pd.Series({
#         'mean': x['value'].mean(),
#         'AUC': calculate_auc(x)
#     })).reset_index()

#     # Convert 'date' back to datetime to handle resampling
#     daily_data['date'] = pd.to_datetime(daily_data['date'])
    
#     # Add normalized AUC
#     daily_data['nAUC'] = daily_data['AUC'] / daily_data['mean']

#     # Ensure 'date' is a datetime object and use it as an index for resampling
#     daily_data.set_index('date', inplace=True)
#     weekly_summary = daily_data.resample('W').agg({
#         'mean': 'mean',
#         'AUC': 'sum',
#         'nAUC': 'mean'
#     }).reset_index()

#     return daily_data.reset_index(), weekly_summary

def calculate_auc(df: pd.DataFrame, dx: int = 5) -> float:
    """
    Calculate Area Under the Curve (AUC) using the trapezoidal rule.
    - Compatible with NumPy 2.x (np.trapezoid)
    - Safe against NaN / empty input
    """
    values = df['value'].dropna()

    # AUC requires at least two data points
    if len(values) < 2:
        return 0.0

    return float(np.trapezoid(values, dx=dx))


def calculate_metrics(df: pd.DataFrame):
    """
    Calculate daily and weekly glucose metrics.
    Fully hardened against:
    - NaN values
    - Empty days
    - Division by zero
    - JSON serialization issues
    """

    # --- Input sanitation ---
    df = df.copy()
    df = df.dropna(subset=['timestamp', 'value'])

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Ensure proper datetime handling
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    # --- Daily aggregation ---
    daily_data = (
        df.groupby('date', as_index=False)
        .apply(lambda x: pd.Series({
            'mean': float(x['value'].mean()) if not x['value'].empty else 0.0,
            'AUC': calculate_auc(x)
        }))
    )

    # Convert back to datetime for resampling
    daily_data['date'] = pd.to_datetime(daily_data['date'])

    # --- Defensive normalization ---
    daily_data['mean'] = daily_data['mean'].fillna(0.0)
    daily_data['AUC'] = daily_data['AUC'].fillna(0.0)

    daily_data['nAUC'] = daily_data.apply(
        lambda row: float(row['AUC'] / row['mean']) if row['mean'] > 0 else 0.0,
        axis=1
    )

    # --- Weekly aggregation ---
    daily_data.set_index('date', inplace=True)

    weekly_summary = (
        daily_data
        .resample('W')
        .agg({
            'mean': 'mean',
            'AUC': 'sum',
            'nAUC': 'mean'
        })
        .reset_index()
    )

    # Final NaN cleanup (API-safe)
    daily_data = daily_data.reset_index().fillna(0.0)
    weekly_summary = weekly_summary.fillna(0.0)

    return daily_data, weekly_summary



def construct_metadata():
    """Construct the complete metadata for the JSON output."""
    metadata = {
        "metrics": [
            {"key": "nAUC", "description": "Normalized AUC /10", "axis_label": "nAUC"},
            {"key": "mean", "description": "Average Glucose", "axis_label": "Mean Glucose (mg/dL)"},
            {"key": "AUC", "description": "Area Under the Curve /1000", "axis_label": "AUC"}
        ],
        "x_axis_default": "date",
        "x_axis_options": {
            "day": "Day of the Week",
            "date": "Date"
        },
        "y_axis": "Value",
        "graph_titles": {
            "weekly_summary": "Weekly Overview",
            "daily_details": "Detailed Daily"
        },
        "page_title": "nAUC View",
        "description": "This dashboard provides an overview of weekly and daily glucose metrics. Select a week to view detailed daily data.",
        "display_weeks": 4,
        "legend_config": {
            "position": "top right",
            "font_size": 12
        },
        "color_scheme": {
            "nAUC": "#1f77b4",
            "mean": "#ff7f0e",
            "AUC": "#2ca02c"
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


def construct_json(daily_data, weekly_summary, display_weeks=4):
    """Construct the required JSON output with data and metadata."""
    metadata = construct_metadata()
    data_list = []
    
    for _, week in weekly_summary.iterrows():
        year, week_number, _ = week['date'].isocalendar()

        week_number = week['date'].isocalendar()[1]  # Access the week number from the isocalendar tuple
        week_start_day = pd.to_datetime(f'{week["date"].year}-W{week_number}-1', format='%G-W%V-%u').date()

        week_end_day = week_start_day + pd.Timedelta(days=6)  # Sunday
        week_data = {
            "week_label": str(week_number),
            "week_start_day": week_start_day.strftime("%Y-%m-%d"),
            "week_end_day": week_end_day.strftime("%Y-%m-%d"),
            "summary": {
                "nAUC": int(week['nAUC'] / 10),  # Change to int
                "mean": int(week['mean']),  # Change to int
                "AUC": int(week['AUC'] / 1000)  # Change to int
            },
            "daily_data": []
        }
        
        # Get the ISO week number for the dates in daily_data and match with the current week in the loop
        week_dates = daily_data[daily_data['date'].dt.isocalendar().week == week_number]
        
        for _, day in week_dates.iterrows():
            day_data = {
                "day": day['date'].strftime("%A"),
                "date": day['date'].strftime("%Y-%m-%d"),
                "nAUC": int(day['nAUC'] / 10),  # Change to int
                "mean": int(day['mean']),  # Change to int
                "AUC": int(day['AUC'] / 1000),  # Change to int
                "description": "Example description"  # Placeholder for actual descriptions
            }
            week_data['daily_data'].append(day_data)

        # Only append week data if daily_data is not empty
        if week_data['daily_data']:
            data_list.append(week_data)

    json_output = {
        'metadata': metadata,
        'data': data_list
    }
    return json_output


def nAUC_Trends(mobile_no, specific_date=None):
    """Main function to orchestrate the fetching and processing of glucose data."""
    df, error = get_glucose_readings_by_mobile_number(mobile_no)
    
    if df is None or df.empty:
        return {
            "error": "No glucose data found for the given mobile number.",
            "mobile_no": mobile_no
        }
    
    if specific_date:
        specific_date = pd.to_datetime(specific_date).date()

        # Find the start and end of the week that contains the specific date
        start_of_week = pd.to_datetime(specific_date) - pd.to_timedelta(specific_date.weekday(), unit='d')
        end_of_week = start_of_week + pd.Timedelta(days=6)

        # Filter the DataFrame to include only the data for the week containing the specific date
        df = df[(pd.to_datetime(df['timestamp']).dt.date >= start_of_week.date()) &
                (pd.to_datetime(df['timestamp']).dt.date <= end_of_week.date())]

    daily_data, weekly_summary = calculate_metrics(df)
    output_json = construct_json(daily_data, weekly_summary)
    return output_json


if __name__ == "__main__":
    mobile_no = "+919945726507"
    specific_date = input("Enter specific date (YYYY-MM-DD) or leave blank for all: ")