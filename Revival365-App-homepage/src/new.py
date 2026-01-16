import requests
from typing import Optional, Dict, Any
from datetime import datetime
def get_current_date():
    """Get current date based on the system's local timezone."""
    return datetime.now().strftime("%Y-%m-%d")



def fetch_data(url: str) -> Optional[Dict[str, Any]]:
    """Fetch data from a given API URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def process_readings(readings, reading_type: str):
    """Process general readings (HR, SpO2, Stress, HRV) to find highest, lowest, and latest values."""
    if not readings or not isinstance(readings, list):
        print(f"Error: Invalid {reading_type} readings received.")
        return None

    valid_readings = [r for r in readings if "value" in r and "timestamp" in r]
    if not valid_readings:
        print(f"Error: No valid {reading_type} readings found.")
        return None

    return {
        f"highest_{reading_type}": max(valid_readings, key=lambda x: x["value"])["value"],
        f"lowest_{reading_type}": int(round(min(valid_readings, key=lambda x: x["value"])["value"])),
        f"latest_{reading_type}": int(round(max(valid_readings, key=lambda x: x["timestamp"])["value"])),
        "latest_timestamp": max(valid_readings, key=lambda x: x["timestamp"])["timestamp"]
    }

def process_bp_readings(bp_data):
    """Process blood pressure readings separately (systolic & diastolic values)."""
    if not bp_data or not isinstance(bp_data, dict) or "bloodpressure_readings" not in bp_data:
        print("Error: Invalid blood pressure data received.")
        return None

    bp_readings = bp_data["bloodpressure_readings"]
    valid_readings = [r for r in bp_readings if "systolic" in r and "diastolic" in r and "timestamp" in r]
    
    if not valid_readings:
        print("Error: No valid blood pressure readings found.")
        return None

    return {
        "systolic_avg": bp_data.get("systolic_avg"),
        "diastolic_avg": bp_data.get("diastolic_avg"),
        "highest_systolic": max(valid_readings, key=lambda x: x["systolic"])["systolic"],
        "lowest_systolic": min(valid_readings, key=lambda x: x["systolic"])["systolic"],
        "highest_diastolic": max(valid_readings, key=lambda x: x["diastolic"])["diastolic"],
        "lowest_diastolic": min(valid_readings, key=lambda x: x["diastolic"])["diastolic"],
        "latest_systolic": max(valid_readings, key=lambda x: x["timestamp"])["systolic"],
        "latest_diastolic": max(valid_readings, key=lambda x: x["timestamp"])["diastolic"],
        "latest_timestamp": max(valid_readings, key=lambda x: x["timestamp"])["timestamp"]
    }

def process_activity_readings(activity_data, step_goal=1000):
    step_goal = 10000
    """Extract total calories burned, total steps, and calculate a score based on steps."""
    if not activity_data or not isinstance(activity_data, dict) or "activityReadings" not in activity_data:
        print("Error: Invalid activity data received.")
        return None

    activity_readings = activity_data["activityReadings"]
    if not activity_readings or not isinstance(activity_readings, list):
        print("Error: No valid activity readings found.")
        return None

    total_calories_burned = sum(r["totalCaloriesBurned"] for r in activity_readings if "totalCaloriesBurned" in r)
    total_steps = sum(r["totalStep"] for r in activity_readings if "totalStep" in r)

    # Calculate score based on step goal
    score = int(min(100, (total_steps / step_goal) * 100))
 # Score capped at 100

    return {
        "total_calories_burned": int(total_calories_burned),
        "total_steps": total_steps,
        "score": round(score, 2)  # Rounded to 2 decimal places
    }


def get_health_data(user_id: int, date: str) -> Dict[str, Any]:
    """Fetch and process health data for a given user and date."""
    print(date)
    base_url = "https://devapi.revival365ai.com/data/chart"
    
    endpoints = {
        "heart_rate": f"{base_url}/hr_readings/{user_id}/{date}",
        "spo2": f"{base_url}/spo2_readings/{user_id}/{date}",
        "stress": f"{base_url}/stress_readings/{user_id}/{date}",
        "blood_pressure": f"{base_url}/bp_readings/{user_id}/{date}",
        "hrv": f"{base_url}/hrv_readings/{user_id}/{date}",
        "activity": f"{base_url}/activity_readings/{user_id}/{date}"
    }

    # Fetch data
    data = {key: fetch_data(url) for key, url in endpoints.items()}

    # Process data
    result = {
        "heart_rate_data": process_readings(data["heart_rate"].get("heartrate_readings", []), "heart_rate") if data["heart_rate"] else None,
        "spo2_data": process_readings(data["spo2"].get("spo2_readings", []), "spo2") if data["spo2"] else None,
        "stress_data": process_readings(data["stress"].get("stress_readings", []), "stress") if data["stress"] else None,
        "blood_pressure_data": process_bp_readings(data["blood_pressure"]) if data["blood_pressure"] else None,
        "hrv_data": process_readings(data["hrv"].get("hrv_readings", []), "hrv") if data["hrv"] else None,
        "activity_data": process_activity_readings(data["activity"]) if data["activity"] else None
    }

    return result

# Example usage
# Automatically picks system's local date
user_id = ""
date = get_current_date() 
 #print("Processed Data:", processed_data)
