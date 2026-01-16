import requests
from datetime import datetime, timedelta
import math
from sleep_summary import get_sleep_windows  # Provided sleep window computation function

def fetch_hr_data(user_id, from_date, to_date):
    """
    Fetch HR data from the API given a user_id and a date range.
    """
    hr_url = f"https://devapi.revival365ai.com/data/summary/hr/{user_id}/{to_date}/{from_date}"
    response = requests.get(hr_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch HR data. Status code: {response.status_code}")
    return response.json()

def classify_hr_into_sleep_windows(sleep_windows, hr_data):
    """
    Given sleep windows (with ISO-format start/end times) and HR data,
    assign HR readings to the appropriate sleep window based on timestamps.
    
    Returns a list of dictionaries, each containing a sleep window and its HR entries.
    """
    window_hr_map = []
    for window in sleep_windows:
        sleep_start_dt = datetime.fromisoformat(window["sleep_start"])
        sleep_end_dt   = datetime.fromisoformat(window["sleep_end"])
        matching_hr_entries = []
        for week in hr_data.get("content", {}).get("data", []):
            for day_data in week.get("daily_data", []):
                daily_date = day_data.get("date")
                for hr_entry in day_data.get("individual_data", []):
                    hr_datetime_str = f"{daily_date}T{hr_entry['time']}"
                    try:
                        hr_dt = datetime.fromisoformat(hr_datetime_str)
                    except Exception:
                        continue
                    if sleep_start_dt <= hr_dt <= sleep_end_dt:
                        matching_hr_entries.append({
                            "time": hr_entry["time"],
                            "value": hr_entry["value"],
                            "datetime": hr_dt.isoformat()
                        })
        window_hr_map.append({
            "sleep_window": window,
            "hr_entries": matching_hr_entries
        })
    return window_hr_map

def extract_night_hr(classified_data):
    """
    Extract all HR readings from the classified sleep windows.
    These values represent HR during sleep (night HR).
    
    Returns a list of HR values.
    """
    night_hr_values = []
    for item in classified_data:
        for hr in item["hr_entries"]:
            night_hr_values.append(hr["value"])
    return night_hr_values

def extract_day_hr(hr_data, sleep_windows, target_day):
    """
    Extract HR readings for the target day that occurred while awake.
    This excludes HR readings that fall into any sleep window.
    
    Returns a list of HR values.
    """
    # Prepare sleep intervals for quick checking.
    sleep_intervals = []
    for window in sleep_windows:
        start = datetime.fromisoformat(window["sleep_start"])
        end = datetime.fromisoformat(window["sleep_end"])
        sleep_intervals.append((start, end))
    
    awake_hr_values = []
    for week in hr_data.get("content", {}).get("data", []):
        for day_data in week.get("daily_data", []):
            if day_data.get("date") != target_day:
                continue
            for hr_entry in day_data.get("individual_data", []):
                hr_datetime_str = f"{target_day}T{hr_entry['time']}"
                try:
                    hr_dt = datetime.fromisoformat(hr_datetime_str)
                except Exception:
                    continue
                # Exclude HR readings that fall within any sleep interval.
                in_sleep = any(start <= hr_dt <= end for start, end in sleep_intervals)
                if not in_sleep:
                    awake_hr_values.append(hr_entry["value"])
    return awake_hr_values

def extract_all_day_hr(hr_data, target_day):
    """
    Extract all HR readings for the target day, without filtering out sleep periods.
    
    Returns a list of HR values.
    """
    all_hr_values = []
    for week in hr_data.get("content", {}).get("data", []):
        for day_data in week.get("daily_data", []):
            if day_data.get("date") != target_day:
                continue
            for hr_entry in day_data.get("individual_data", []):
                all_hr_values.append(hr_entry["value"])
    return all_hr_values

def compute_rhr(hr_values, percentile_fraction=0.1, use_min_if_small=True):
    """
    Compute the Resting Heart Rate (RHR) from a list of HR values.
    
    Algorithm:
      1. Sort the HR values.
      2. Take the lowest 'percentile_fraction' of the readings (default is 10%).
      3. Compute their average, which is used as the RHR.
         (If there are very few readings and use_min_if_small is True, return the minimum.)
         
    The computed RHR is rounded to an integer.
    """
    if not hr_values:
        return None
    sorted_values = sorted(hr_values)
    n = len(sorted_values)
    cutoff = max(math.ceil(n * percentile_fraction), 1)
    if cutoff < 1 and use_min_if_small:
        rhr_val = sorted_values[0]
    else:
        rhr_val = sum(sorted_values[:cutoff]) / cutoff
    return int(round(rhr_val))

def compute_hr_metrics(hr_values, percentile_fraction=0.1):
    """
    Compute HR metrics for a list of HR values.
    
    Metrics computed:
      - min_hr: Minimum HR value.
      - max_hr: Maximum HR value.
      - avg_hr: Average HR value.
      - rhr: Resting HR computed as the average of the lowest percentile_fraction of readings.
    
    All values are rounded to integers.
    """
    if not hr_values:
        return {
            "min_hr": None,
            "max_hr": None,
            "avg_hr": None,
            "rhr": None
        }
    min_hr = min(hr_values)
    max_hr = max(hr_values)
    avg_hr = round(sum(hr_values) / len(hr_values))
    rhr = compute_rhr(hr_values, percentile_fraction=percentile_fraction)
    return {
        "min_hr": int(min_hr),
        "max_hr": int(max_hr),
        "avg_hr": int(avg_hr),
        "rhr": int(rhr)
    }

def compute_day_night_hr_metrics(user_id, target_day, day_start="08:00", night_start="20:00", max_gap_minutes=5):
    """
    For a given target day (YYYY-MM-DD), compute HR metrics separately for:
      - Night: HR readings during sleep windows (night-time HR).
      - Day: HR readings when awake (day-time HR).
      - Combined: All HR readings for the target day (unfiltered).
    
    Metrics include: minimum HR, maximum HR, average HR, and RHR (resting HR).
    
    The date range includes the previous night (since sleep windows are based on the prior night)
    and the target day.
    
    Returns a dictionary with keys:
      'night_metrics', 'day_metrics', 'combined_metrics'
    """
    # Determine date range: from_date (previous day) and to_date (target day)
    target_date_obj = datetime.fromisoformat(target_day)
    from_date_obj = target_date_obj - timedelta(days=1)
    from_date = from_date_obj.date().isoformat()
    to_date = target_day

    # Sleep type mapping required by get_sleep_windows.
    sleep_type_mapping = {
        0: "deep",
        1: "light",
        2: "rem",
        3: "awake"
    }
    
    # Fetch sleep windows using the provided function.
    sleep_windows = get_sleep_windows(
        user_id, from_date, to_date,
        day_start=day_start, night_start=night_start,
        max_gap_minutes=max_gap_minutes, sleep_type_mapping=sleep_type_mapping,
        debug=False
    )
    
    # Fetch HR data.
    hr_data = fetch_hr_data(user_id, from_date, to_date)
    
    # Classify HR data into sleep windows.
    classified_data = classify_hr_into_sleep_windows(sleep_windows, hr_data)
    
    # Extract HR readings:
    night_hr_values = extract_night_hr(classified_data)   # HR during sleep (night)
    day_hr_values = extract_day_hr(hr_data, [w["sleep_window"] for w in classified_data], target_day)  # Awake HR
    combined_hr_values = extract_all_day_hr(hr_data, target_day)  # All HR for target day
    
    # Compute metrics for each group.
    night_metrics = compute_hr_metrics(night_hr_values)
    day_metrics = compute_hr_metrics(day_hr_values)
    combined_metrics = compute_hr_metrics(combined_hr_values)
    
    return {
        #"night_metrics": night_metrics,
        #"day_metrics": day_metrics,
        "combined_metrics": combined_metrics
    }

# Example usage:
if __name__ == "__main__":
    user_id = 22
    target_day = "2025-02-18"  # Example target day
    metrics = compute_day_night_hr_metrics(user_id, target_day)
    print("HR Metrics for the day:")
    print(metrics)