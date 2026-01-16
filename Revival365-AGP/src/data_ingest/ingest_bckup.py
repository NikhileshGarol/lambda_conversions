"""
ingest.py
-----------
This module is responsible for fetching or generating the 
raw glucose data. In a real project, this could be replaced with 
a database call, CSV file read, API fetch, etc.
"""

import pandas as pd
from datetime import datetime

def read_glucose_data_from_csv(file_path='case_1.csv'):
    """
    Reads glucose data from a CSV file.

    :param file_path: str, path to the CSV file
    :return: pd.DataFrame with columns ['timestamp', 'glucose']
    """
    try:
        data = pd.read_csv(file_path)

        # Ensure correct column names
        if 'timestamp' not in data.columns or 'glucose' not in data.columns:
            raise ValueError("CSV file must contain 'timestamp' and 'glucose' columns.")

        # Convert timestamp to datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Ensure glucose values are numeric
        data['glucose'] = pd.to_numeric(data['glucose'], errors='coerce')

        # Drop rows with invalid data
        data = data.dropna(subset=['timestamp', 'glucose'])

        return data
    except Exception as e:
        raise RuntimeError(f"Error reading glucose data from CSV: {e}")

def ingest_data():
    """
    Ingests data from the CSV file.
    Returns the raw data as a pandas DataFrame.
    """
    file_name = 'case_1_modified.csv'  # Adjust file name as needed
    raw_data = read_glucose_data_from_csv(file_name)
    print(raw_data)  # Displays the first few rows of the data
    return raw_data

