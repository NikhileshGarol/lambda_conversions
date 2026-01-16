'''
import requests
from datetime import datetime, timedelta, timezone
import numpy as np
import pytz
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling
from get_token import get_patient_glucose_config
from get_token import get_user_timezone
def fetch_data(url: str):

    """Fetch data from a given API URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Handle empty data (204 No Content) or missing 'glucose_readings'
        if response.status_code == 204 or "glucose_readings" not in data:
            print(f"✅ No data for: {url}")
            return None

        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from {url}: {e}")
        return None

     

def calculate_eHbA1c(mean_glucose):
    """Calculate estimated HbA1c using the formula: HbA1c (%) = 0.0348 × Mean Glucose + 1.626"""
    if mean_glucose is None:
        return None
    return round(0.0348 * mean_glucose + 1.626, 2)

def compute_glucose_variability(data, day_start_str, day_end_str):
 
    if not data or "glucose_readings" not in data:
        print("❌ No glucose data available for variability calculation.")
        return {"glucose_variability": {
    "day_glucose_stability": None,
    "night_glucose_stability": None,
    "overall_cv": None
}}


    day_start = datetime.strptime(day_start_str, "%H:%M").time()
    day_end = datetime.strptime(day_end_str, "%H:%M").time()

    day_values = []
    night_values = []

    for reading in data.get("glucose_readings", []):
        ts = datetime.fromisoformat(reading["timestamp"])
        value = reading["value"]
        if value < 50:
            continue
        if day_start <= ts.time() <= day_end:
            day_values.append(value)
        else:
            night_values.append(value)

    def calculate_cv(values):
        if not values:
            return None
        mean_val = np.mean(values)
        if mean_val == 0:
            return None
        std_val = np.std(values)
        return int(round((std_val / mean_val) * 100))

    return {"glucose_variability": {  
        "day_glucose_stability": calculate_cv(day_values) if day_values else None,
        "night_glucose_stability": calculate_cv(night_values) if night_values else None,
        "overall_cv": calculate_cv(day_values + night_values) if (day_values or night_values) else None
    }}

def get_fasting_glucose(glucose_data, user_id):
    """
    Determine the fasting glucose value based on the user's timezone, fasting end time,
    and available glucose readings.
    """

    # Get user timezone data and configuration
    configuration_data = get_patient_glucose_config(user_id)
    timezone_data = get_user_timezone(user_id)

    # Get fasting end time from configuration (default: '06:00:00')
    fasting_end_time_str = configuration_data['content'].get('fastingEndTime', '06:00:00')

    # Extract timezone identifier from "America/Chicago (GMT-06:00)" → "America/Chicago"
    current_tz_str = timezone_data['content']['currentTimezone'].split("(")[0].strip()
    print(f"✅ Extracted Timezone: {current_tz_str}")

    # Define timezone objects
    user_tz = ZoneInfo(current_tz_str)
    IST = ZoneInfo("Asia/Kolkata")

    # ✅ Get current UTC time and convert to user's timezone
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    user_now = utc_now.astimezone(user_tz)
    user_date = user_now.date()  # Current date in user's timezone

    # ✅ Get current IST time and date
    now_ist = datetime.now(IST)
    today_ist = now_ist.date()

    # ✅ Compute the fasting end time in user's timezone
    fasting_end_time = datetime.strptime(fasting_end_time_str, "%H:%M:%S").time()
    user_fasting_end_datetime = datetime.combine(user_date, fasting_end_time).replace(tzinfo=user_tz)

    # ✅ Convert fasting end time to IST
    wake_up_ist = user_fasting_end_datetime.astimezone(IST)

 
    print(f"✅ Current User Time in {current_tz_str}: {user_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"✅ Current Date in User Timezone: {user_date}")
    print(f"✅ Current Date in IST: {today_ist}")
    print(f"✅ Wake-Up Time in IST: {wake_up_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # ✅ Function to find the closest glucose reading within ±15 minutes
    def find_reading(wake_up_time):
        readings = glucose_data.get("glucose_readings", [])
        best_match = None
        closest_time_diff = 900  # 15 minutes in seconds

        for reading in readings:
            ts = datetime.fromisoformat(reading["timestamp"]).astimezone(IST)
            diff = abs((ts - wake_up_time).total_seconds())

            if diff < closest_time_diff:
                closest_time_diff = diff
                best_match = reading["value"]

        if best_match is None:
            print(f"❌ No glucose reading found within ±15 minutes of {wake_up_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"✅ Found Glucose Reading: {best_match} mg/dL")

        return best_match

    # ✅ Get the reading for wake-up time in IST
    return find_reading(wake_up_ist)
 
def process_glucose_readings(today_data, yesterday_data, user_id):
    """Process glucose readings to find highest, lowest, and latest values from today's data."""

    # ✅ Separate today's readings only
    today_readings = today_data.get("glucose_readings", []) if today_data else []

    # ✅ Convert timestamps to IST timezone
    valid_today_readings = []

    for r in today_readings:
        # Convert timestamp to IST timezone
        
        ts = datetime.fromisoformat(r["timestamp"])
        # ✅ Filter only valid glucose values (>=50) and today's readings
        if r["value"] >= 50 and ts.date() == datetime.now().date():
            valid_today_readings.append({
                "timestamp": ts,
                "value": r["value"]
            })

    # ✅ If no valid readings, return None
    if not valid_today_readings:
        print("❌ No valid glucose readings found for today.")
        return {
            "highest_glucose": None,
            "lowest_glucose": None,
            "latest_glucose": None,
            "latest_timestamp": None,
            "fasting_glucose": None,
            "estimated_HbA1c": None,
            "glucose_variability": {
                "day_glucose_stability": None,
                "night_glucose_stability": None,
                "overall_cv": None
            }
        }

    # ✅ Now calculate highest, lowest, and latest glucose from today's readings
    highest = max(valid_today_readings, key=lambda x: x["value"])
    lowest = min(valid_today_readings, key=lambda x: x["value"])
    sorted_readings = sorted(valid_today_readings, key=lambda x: x["timestamp"], reverse=True)
    latest = sorted_readings[0] if sorted_readings else None

    # ✅ Calculate mean glucose for eHbA1c
    mean_glucose = int(round(np.mean([r["value"] for r in valid_today_readings])))

    # ✅ Combine yesterday + today only for fasting glucose
    combined_data = (yesterday_data.get("glucose_readings", []) if yesterday_data else []) + today_readings
    fasting_glucose = get_fasting_glucose({"glucose_readings": combined_data}, user_id)

    # ✅ Compute glucose variability only for today
    glucose_variability = compute_glucose_variability(today_data, "06:00", "22:00") 


    # ✅ Return processed result
    result = {
        "highest_glucose": int(highest["value"]),
        "lowest_glucose": int(lowest["value"]),
        "latest_glucose": int(latest["value"]),
        "latest_timestamp": latest["timestamp"].isoformat(),
        "fasting_glucose": fasting_glucose,
        "estimated_HbA1c": calculate_eHbA1c(mean_glucose),
        "glucose_variability": glucose_variability
    }
    print("✅ Processed Glucose Readings:", result)
    return result

def get_glucose_data(user_id, date):
    """Fetch and process glucose readings for a given user and date."""
    # Fetch today's data
    glucose_url = f"https://devapi.revival365ai.com/data/chart/glucose-readings/{user_id}/{date}"
    today_data = fetch_data(glucose_url)
    
 
     
    # Fetch yesterday's data
    yesterday = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    glucose_url_yesterday = f"https://devapi.revival365ai.com/data/chart/glucose-readings/{user_id}/{yesterday}"
    yesterday_data = fetch_data(glucose_url_yesterday)

    result = process_glucose_readings(today_data, yesterday_data, user_id)
    return result if result else {}

    

# Example usage:
if __name__ == "__main__":
    user_id = 132
    date = ""
    glucose_processed = get_glucose_data(user_id, date)
'''
import requests
from datetime import datetime, timedelta, timezone
import numpy as np
import pytz
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling
from get_token import get_patient_glucose_config
from get_token import get_user_timezone
def fetch_data(url: str):

    """Fetch data from a given API URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Handle empty data (204 No Content) or missing 'glucose_readings'
        if response.status_code == 204 or "glucose_readings" not in data:
            print(f"✅ No data for: {url}")
            return None

        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from {url}: {e}")
        return None

     

def calculate_eHbA1c(mean_glucose):
    """Calculate estimated HbA1c using the formula: HbA1c (%) = 0.0348 × Mean Glucose + 1.626"""
    if mean_glucose is None:
        return None
    return round(0.0348 * mean_glucose + 1.626, 2)

def compute_glucose_variability(data, day_start_str, day_end_str):
 
    if not data or "glucose_readings" not in data:
        print("❌ No glucose data available for variability calculation.")
        return {"glucose_variability": {
    "day_glucose_stability": None,
    "night_glucose_stability": None,
    "overall_cv": None
}}


    day_start = datetime.strptime(day_start_str, "%H:%M").time()
    day_end = datetime.strptime(day_end_str, "%H:%M").time()

    day_values = []
    night_values = []

    for reading in data.get("glucose_readings", []):
        ts = datetime.fromisoformat(reading["timestamp"])
        value = reading["value"]
        if value < 50:
            continue
        if day_start <= ts.time() <= day_end:
            day_values.append(value)
        else:
            night_values.append(value)

    def calculate_cv(values):
        if not values:
            return None
        mean_val = np.mean(values)
        if mean_val == 0:
            return None
        std_val = np.std(values)
        return int(round((std_val / mean_val) * 100))

    return {"glucose_variability": {  
        "day_glucose_stability": calculate_cv(day_values) if day_values else None,
        "night_glucose_stability": calculate_cv(night_values) if night_values else None,
        "overall_cv": calculate_cv(day_values + night_values) if (day_values or night_values) else None
    }}


def get_fasting_glucose(glucose_data, user_id):
    """
    Determine the fasting glucose value based on the user's timezone, fasting end time,
    and available glucose readings.
    """

    # Get user timezone data and configuration
    configuration_data = get_patient_glucose_config(user_id)
    timezone_data = get_user_timezone(user_id)

    # Get fasting end time from configuration (default: '06:00:00')
    fasting_end_time_str = configuration_data['content'].get('fastingEndTime', '06:00:00')

    # Extract timezone identifier from "America/Chicago (GMT-06:00)" → "America/Chicago"
    current_tz_str = timezone_data['content']['currentTimezone'].split("(")[0].strip()
    print(f"✅ Extracted Timezone: {current_tz_str}")

    # Define timezone objects
    user_tz = ZoneInfo(current_tz_str)
    IST = ZoneInfo("Asia/Kolkata")

    # ✅ Get current UTC time and convert to user's timezone
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    user_now = utc_now.astimezone(user_tz)
    user_date = user_now.date()  # Current date in user's timezone

    # ✅ Get current IST time and date
    now_ist = datetime.now(IST)
    today_ist = now_ist.date()

    # ✅ Compute the fasting end time in user's timezone
    fasting_end_time = datetime.strptime(fasting_end_time_str, "%H:%M:%S").time()
    user_fasting_end_datetime = datetime.combine(user_date, fasting_end_time).replace(tzinfo=user_tz)

    # ✅ Convert fasting end time to IST
    wake_up_ist = user_fasting_end_datetime.astimezone(IST)

 
    print(f"✅ Current User Time in {current_tz_str}: {user_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"✅ Current Date in User Timezone: {user_date}")
    print(f"✅ Current Date in IST: {today_ist}")
    print(f"✅ Wake-Up Time in IST: {wake_up_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # ✅ Function to find the closest glucose reading within ±15 minutes
    def find_reading(wake_up_time):
        readings = glucose_data.get("glucose_readings", [])
        best_match = None
        closest_time_diff = 900  # 15 minutes in seconds

        for reading in readings:
            ts = datetime.fromisoformat(reading["timestamp"]).astimezone(IST)
            diff = abs((ts - wake_up_time).total_seconds())

            if diff < closest_time_diff:
                closest_time_diff = diff
                best_match = reading["value"]

        if best_match is None:
            print(f"❌ No glucose reading found within ±15 minutes of {wake_up_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"✅ Found Glucose Reading: {best_match} mg/dL")

        return best_match

    # ✅ Get the reading for wake-up time in IST
    return find_reading(wake_up_ist)



def process_glucose_readings(today_data, yesterday_data, user_id):
    """Process glucose readings to find highest, lowest, and latest values from today's data."""

    # ✅ Separate today's readings only
    today_readings = today_data.get("glucose_readings", []) if today_data else []

    # ✅ Convert timestamps to IST timezone
    valid_today_readings = []

    for r in today_readings:
        # Convert timestamp to IST timezone
        
        ts = datetime.fromisoformat(r["timestamp"])
        # ✅ Filter only valid glucose values (>=50) and today's readings
        if r["value"] >= 50 and ts.date() == datetime.now().date():
            valid_today_readings.append({
                "timestamp": ts,
                "value": r["value"]
            })

    # ✅ If no valid readings, return None
    if not valid_today_readings:
        print("❌ No valid glucose readings found for today.")
        return {
            "highest_glucose": None,
            "lowest_glucose": None,
            "latest_glucose": None,
            "latest_timestamp": None,
            "fasting_glucose": None,
            "estimated_HbA1c": None,
            "glucose_variability": {
                "day_glucose_stability": None,
                "night_glucose_stability": None,
                "overall_cv": None
            }
        }

    # ✅ Now calculate highest, lowest, and latest glucose from today's readings
    highest = max(valid_today_readings, key=lambda x: x["value"])
    lowest = min(valid_today_readings, key=lambda x: x["value"])
    sorted_readings = sorted(valid_today_readings, key=lambda x: x["timestamp"], reverse=True)
    latest = sorted_readings[0] if sorted_readings else None

    # ✅ Calculate mean glucose for eHbA1c
    mean_glucose = int(round(np.mean([r["value"] for r in valid_today_readings])))

    # ✅ Combine yesterday + today only for fasting glucose
    combined_data = (yesterday_data.get("glucose_readings", []) if yesterday_data else []) + today_readings
    fasting_glucose = get_fasting_glucose({"glucose_readings": combined_data}, user_id)

    # ✅ Compute glucose variability only for today
    glucose_variability = compute_glucose_variability(today_data, "06:00", "22:00") 


    # ✅ Return processed result
    result = {
        "highest_glucose": int(highest["value"]),
        "lowest_glucose": int(lowest["value"]),
        "latest_glucose": int(latest["value"]),
        "latest_timestamp": latest["timestamp"].isoformat(),
        "fasting_glucose": fasting_glucose,
        "estimated_HbA1c": calculate_eHbA1c(mean_glucose),
        "glucose_variability": glucose_variability
    }
    print("✅ Processed Glucose Readings:", result)
    return result
    
def get_glucose_readings_for_user(user_id):
    """
    Fetch glucose readings for the user's local date by converting 
    their start and end time to IST and calling the API.
    """

    try:
        # ✅ Step 1: Get user timezone
        timezone_data = get_user_timezone(user_id)  # Assume this function gets user's timezone
        user_tz = ZoneInfo(timezone_data['content']['currentTimezone'].split("(")[0].strip())

        # ✅ Step 2: Compute user's local day start & end
        user_now = datetime.now(user_tz)
        local_start = datetime(user_now.year, user_now.month, user_now.day, 0, 0, 0, tzinfo=user_tz)
        local_end = local_start + timedelta(days=1, seconds=-1)

        print(f"✅ User Timezone: {user_tz} | Local Date: {local_start.date()}")

        # ✅ Step 3: Convert to IST
        ist_tz = ZoneInfo("Asia/Kolkata")
        ist_start = local_start.astimezone(ist_tz).strftime("%Y-%m-%dT%H:%M:%S")
        ist_end = local_end.astimezone(ist_tz).strftime("%Y-%m-%dT%H:%M:%S")


        print(f"✅ IST Start: {ist_start} | IST End: {ist_end}")

        # ✅ Step 4: Call the API
        url = f"https://devapi.revival365ai.com/data/chart/glucose-readings/{user_id}/{ist_start}/{ist_end}"
        print(url)
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()  # ✅ Return glucose readings as-is
        else:
            print(f"❌ API Error: {response.status_code}")
            return {"error": "Failed to fetch data"}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": "Something went wrong"}



def run_glucose_processing(user_id: int):
    """
    Fetches glucose readings using get_glucose_readings_for_user,
    processes the data, and returns the processed metrics.
    """
    # Fetch today's glucose readings based on user's local day using get_glucose_readings_for_user()
    glucose_data = get_glucose_readings_for_user(user_id)
    print("✅ Glucose data fetched from get_glucose_readings_for_user():")
    #print(glucose_data)

    # Process the glucose readings
    # Since we are using only today's data, we pass None for yesterday's data.
    processed_data = process_glucose_readings(glucose_data, yesterday_data=None, user_id=user_id)
    print("✅ Processed Glucose Data:")
    print(processed_data)
    
    return processed_data


if __name__ == "__main__":
    # Example usage when this script is executed directly
    user_id = 132
    run_glucose_processing(user_id)


 