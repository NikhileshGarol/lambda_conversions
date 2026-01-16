import pandas as pd
from data_ingest.ingest import ingest_data
from data_preprocessing.preprocess import preprocess_data
from data_processing.process import process_data
from data_formatting.format_to_json import format_to_json

def get_glucose_data(mobile_number=None, start_date=None, end_date=None):
    """
    Function to fetch, preprocess, process, and return glucose data in JSON format.
    Optionally accepts arguments for debugging or filtering.

    Args:
        mobile_number (str, optional): Mobile number for reference.
        start_date (str, optional): Start date for filtering.
        end_date (str, optional): End date for filtering.

    Returns:
        str: Processed glucose data in JSON format.
    """
    # Print the arguments
    print(f"Arguments received: mobile_number={mobile_number}, start_date={start_date}, end_date={end_date}")

    # 1. Ingest data
    raw_df = ingest_data(mobile_number=mobile_number)

    # 2. Preprocess data
    #cleaned_df = preprocess_data(raw_df)

    # 3. Process data
    processed = process_data(raw_df)

    # 4. Format to JSON
    json_str = format_to_json(processed)

    return json_str

if __name__ == "__main__":
    """
    Main function for testing the get_glucose_data function.
    """
    print("Testing get_glucose_data function...")

    # Example arguments
    mobile_number = "+918521345464"
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    # Call the function and print the output
    glucose_json = get_glucose_data(mobile_number, start_date, end_date)
    print("Processed Glucose Data in JSON Format:")
    print(glucose_json)

    # Optionally save the output to a file
    with open("glucose_data.json", "w") as f:
        f.write(glucose_json)
        print("JSON data saved to 'glucose_data.json'")