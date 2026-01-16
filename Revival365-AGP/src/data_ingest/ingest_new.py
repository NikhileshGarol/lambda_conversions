import json
from data_ingest.read_glucose_readings import glucose_readings

def ingest_data():
    """
    Ingest glucose data by fetching it from `get_data_as_json`.

    :param mobile_number: str, patient's mobile number
    :param start_date: str, start date in "YYYY-MM-DD" format (optional)
    :param end_date: str, end date in "YYYY-MM-DD" format (optional)
    :return: dict, JSON-like object with glucose data
    """
    mobile_number = "+918521345464"
    start_date = "2025-01-01"
    end_date = "2025-01-07"

    try:
        # Fetch glucose readings as JSON
        data = glucose_readings(mobile_number, start_date, end_date)

        # Handle errors returned from `get_data_as_json`
        if "error" in data:
            raise ValueError(data["error"])

        return data

    except Exception as e:
        raise RuntimeError(f"Error during data ingestion: {e}")

# If you need a main function for testing or standalone use, you can leave it like this
def main():
    # Example inputs for testing
    mobile_number = "+918521345464"
    start_date = "2025-01-01"
    end_date = "2025-01-07"

    try:
        # Call the ingest function and process the data
        glucose_data = ingest_data()
        print("Data ingestion successful!")
        print(json.dumps(glucose_data, indent=4))  # Pretty-print the data for debugging
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

