#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List

# ------------------------- ANSI Color Codes -------------------------
COLOR_RESET  = "\033[0m"
COLOR_DEEP   = "\033[34m"  # Blue for deep sleep
COLOR_LIGHT  = "\033[32m"  # Green for light sleep
COLOR_REM    = "\033[35m"  # Magenta for REM sleep
COLOR_AWAKE  = "\033[31m"  # Red for awake

def color_for_state(state: str) -> str:
    """Return ANSI color code for a given sleep state."""
    if state == "deep":
        return COLOR_DEEP
    elif state == "light":
        return COLOR_LIGHT
    elif state == "rem":
        return COLOR_REM
    elif state == "awake":
        return COLOR_AWAKE
    else:
        return COLOR_RESET

# ------------------------- Data Fetching -------------------------
def fetch_sleep_data(user_id: int, from_date: str, to_date: str) -> Dict[str, Any]:
    """
    Fetch sleep data from the API using the summary endpoint.
    """
    url = f"https://devapi.revival365ai.com/data/summary/sleep/{user_id}/{to_date}/{from_date}"
    print(f"Fetching sleep data from: {url}")
    print(f"From Date: {from_date}, To Date: {to_date}")
    
    response = requests.get(url)
    print(f"Response Status Code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("DEBUG: Input JSON successfully fetched.")
            return data
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# ------------------------- Time & Utility Functions -------------------------
def parse_time(date_str: str, time_str: str) -> datetime:
    """Parse date and time strings into a datetime object."""
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def adjust_record_time(record_date: str, time_str: str, night_start: str) -> datetime:
    """
    Adjust a record's timestamp so that records with a time on or after night_start
    are shifted to the previous calendar day.
    """
    dt = parse_time(record_date, time_str)
    threshold = datetime.strptime(night_start, "%H:%M").time()
    if dt.time() >= threshold:
        dt -= timedelta(days=1)
    return dt

def format_duration(minutes: float) -> str:
    """Format a duration (in minutes) into a human-friendly string."""
    if 0 < minutes < 1:
        minutes = 1
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"

def finalize_segment(segment: Dict[str, Any]) -> None:
    """Ensure that a segment has a non-zero duration."""
    duration = (segment["end"] - segment["start"]).total_seconds() / 60.0
    if duration <= 0:
        segment["end"] = segment["start"] + timedelta(minutes=1)
        duration = 1.0
    segment["duration"] = duration

def finalize_session(session: Dict[str, Any], session_start: datetime) -> None:
    """Ensure that a session has a non-zero duration."""
    duration = (session["sleep_end"] - session["sleep_start"]).total_seconds() / 60.0
    if duration <= 0:
        session["sleep_end"] = session_start + timedelta(minutes=1)
        duration = 1.0
    session["duration"] = duration

# ------------------------- Sleep Conversion -------------------------
def convert_sleep_value(data: float) -> int:
    """
    Use the raw sleep value directly:
      - 0 → deep
      - 1 → light
      - 2 → rem
      - 3 → awake
    Any value not in {0,1,2,3} defaults to 3 (awake).
    """
    try:
        val = int(data)
        if val in [0, 1, 2, 3]:
            return val
        else:
            return 3
    except:
        return 3

# ------------------------- Session Grouping -------------------------
def group_records_into_sessions(adjusted_records: List[Dict[str, Any]],
                                max_gap_minutes: int,
                                sleep_type_mapping: Dict[int, str],
                                debug: bool = False) -> List[Dict[str, Any]]:
    """
    Group sorted sleep records into sessions.
    
    Rules:
      - If the gap between consecutive records is >= max_gap_minutes (>= 5 minutes),
        end the current session.
      - If the gap is > 1 minute but < max_gap_minutes, insert an awake segment covering the entire gap.
      - If the gap is <= 1 minute, treat the records as continuous.
    """
    sessions = []
    if not adjusted_records:
        return sessions

    current_session = {"segments": []}
    current_session_start = adjusted_records[0]["dt"]
    current_segment = {
        "state": adjusted_records[0]["value"],
        "start": adjusted_records[0]["dt"],
        "end": adjusted_records[0]["dt"]
    }
    previous_time = adjusted_records[0]["dt"]

    for rec in adjusted_records[1:]:
        current_time = rec["dt"]
        current_state = rec["value"]
        gap = (current_time - previous_time).total_seconds() / 60.0

        if gap >= max_gap_minutes:
            if debug:
                print(f"DEBUG: Detected large gap of {gap:6.2f} mins between {previous_time.strftime('%Y-%m-%dT%H:%M:%S')} and {current_time.strftime('%Y-%m-%dT%H:%M:%S')}. Ending session.")
            current_segment["end"] = previous_time
            finalize_segment(current_segment)
            if debug:
                seg_state = sleep_type_mapping[current_segment["state"]]
                col = color_for_state(seg_state)
                print(f"DEBUG: Segment | State: {col}{seg_state:<6}{COLOR_RESET} | Start: {current_segment['start'].strftime('%Y-%m-%dT%H:%M:%S')} | End: {current_segment['end'].strftime('%Y-%m-%dT%H:%M:%S')} | Duration: {col}{current_segment['duration']:6.2f} mins{COLOR_RESET}")
            current_session["segments"].append(current_segment)

            current_session["sleep_start"] = current_session_start
            current_session["sleep_end"] = previous_time
            finalize_session(current_session, current_session_start)
            sessions.append(current_session)

            current_session = {"segments": []}
            current_session_start = current_time
            if debug:
                print(f"DEBUG: Starting new session at {current_time.strftime('%Y-%m-%dT%H:%M:%S')}.")
            current_segment = {
                "state": current_state,
                "start": current_time,
                "end": current_time
            }
        else:
            if gap > 1:
                if debug:
                    print(f"DEBUG: Detected gap of {gap:6.2f} mins between {previous_time.strftime('%Y-%m-%dT%H:%M:%S')} and {current_time.strftime('%Y-%m-%dT%H:%M:%S')}.")
                current_segment["end"] = previous_time
                finalize_segment(current_segment)
                if debug:
                    seg_state = sleep_type_mapping[current_segment["state"]]
                    col = color_for_state(seg_state)
                    print(f"DEBUG: Segment | State: {col}{seg_state:<6}{COLOR_RESET} | Start: {current_segment['start'].strftime('%Y-%m-%dT%H:%M:%S')} | End: {current_segment['end'].strftime('%Y-%m-%dT%H:%M:%S')} | Duration: {col}{current_segment['duration']:6.2f} mins{COLOR_RESET}")
                current_session["segments"].append(current_segment)

                awake_duration = gap
                if awake_duration > 0:
                    awake_start = previous_time
                    awake_end = current_time
                    if awake_end >= awake_start:
                        if debug:
                            col_awake = color_for_state("awake")
                            print(f"DEBUG: Inserting awake segment from {awake_start.strftime('%Y-%m-%dT%H:%M:%S')} to {awake_end.strftime('%Y-%m-%dT%H:%M:%S')} (duration: {awake_duration:6.2f} mins) as {col_awake}awake{COLOR_RESET}.")
                        awake_segment = {
                            "state": 3,  # 3 represents awake
                            "start": awake_start,
                            "end": awake_end
                        }
                        finalize_segment(awake_segment)
                        if debug:
                            col_awake = color_for_state("awake")
                            print(f"DEBUG: Segment | State: {col_awake}{'awake':<6}{COLOR_RESET} | Start: {awake_segment['start'].strftime('%Y-%m-%dT%H:%M:%S')} | End: {awake_segment['end'].strftime('%Y-%m-%dT%H:%M:%S')} | Duration: {col_awake}{awake_segment['duration']:6.2f} mins{COLOR_RESET}")
                        current_session["segments"].append(awake_segment)
                current_segment = {
                    "state": current_state,
                    "start": current_time,
                    "end": current_time
                }
            else:
                if current_state != current_segment["state"]:
                    current_segment["end"] = current_time
                    finalize_segment(current_segment)
                    if debug:
                        seg_state = sleep_type_mapping[current_segment["state"]]
                        col = color_for_state(seg_state)
                        print(f"DEBUG: State Change - Finalizing Segment | State: {col}{seg_state:<6}{COLOR_RESET} | Start: {current_segment['start'].strftime('%Y-%m-%dT%H:%M:%S')} | End: {current_segment['end'].strftime('%Y-%m-%dT%H:%M:%S')} | Duration: {col}{current_segment['duration']:6.2f} mins{COLOR_RESET}")
                    current_session["segments"].append(current_segment)
                    current_segment = {
                        "state": current_state,
                        "start": current_time,
                        "end": current_time
                    }
                else:
                    current_segment["end"] = current_time
        previous_time = current_time

    # Finalize the last segment and session.
    current_segment["end"] = previous_time
    finalize_segment(current_segment)
    if debug:
        seg_state = sleep_type_mapping[current_segment["state"]]
        col = color_for_state(seg_state)
        print(f"DEBUG: Finalizing Last Segment | State: {col}{seg_state:<6}{COLOR_RESET} | Start: {current_segment['start'].strftime('%Y-%m-%dT%H:%M:%S')} | End: {current_segment['end'].strftime('%Y-%m-%dT%H:%M:%S')} | Duration: {col}{current_segment['duration']:6.2f} mins{COLOR_RESET}")
    current_session["segments"].append(current_segment)
    current_session["sleep_start"] = current_session_start
    current_session["sleep_end"] = previous_time
    finalize_session(current_session, current_session_start)
    sessions.append(current_session)
    return sessions

# ------------------------- Sleep Summary Classification -------------------------
def classify_sleep_sessions(sleep_data: Dict[str, Any],
                            night_start: str,
                            day_start: str,
                            max_gap_minutes: int,
                            sleep_type_mapping: Dict[int, str],
                            valid_from: str,
                            valid_to: str,
                            debug: bool = False) -> Dict[str, Any]:
    """
    Process the raw sleep_data JSON and build a date-wise sleep summary.
    """
    sleep_summary: Dict[str, Any] = {}
    night_start_time = datetime.strptime(night_start, "%H:%M").time()
    day_start_time = datetime.strptime(day_start, "%H:%M").time()

    for entry in sleep_data.get("content", {}).get("data", []):
        for day in entry.get("daily_data", []):
            summary_date_str = day.get("date")
            if not summary_date_str:
                continue
            if summary_date_str < valid_from or summary_date_str > valid_to:
                continue

            daily_sleep_types = {state: 0 for state in sleep_type_mapping.values()}
            sleep_summary.setdefault(summary_date_str, {
                "night_sleep": [],
                "day_sleep": [],
                "total_night_sleep": "0m",
                "total_day_sleep": "0m",
                "sleep_types": {state: "0m" for state in sleep_type_mapping.values()}
            })

            adjusted_records: List[Dict[str, Any]] = []
            for record in day.get("individual_data", []):
                try:
                    adj_dt = adjust_record_time(day["date"], record["time"], night_start)
                    converted_value = convert_sleep_value(float(record["value"]))
                    adjusted_records.append({
                        "dt": adj_dt,
                        "value": converted_value
                    })
                except Exception as e:
                    if debug:
                        print(f"ERROR: Processing record {record}: {e}")
            adjusted_records.sort(key=lambda x: x["dt"])

            sessions = group_records_into_sessions(adjusted_records, max_gap_minutes, sleep_type_mapping, debug=debug)

            night_total = 0.0
            day_total = 0.0

            for session in sessions:
                session_start = session["sleep_start"]
                session_end = session["sleep_end"]
                session_duration = session["duration"]
                midpoint = session_start + (session_end - session_start) / 2

                session_sleep_types = {state: 0 for state in sleep_type_mapping.values()}
                for seg in session["segments"]:
                    state_name = sleep_type_mapping.get(seg["state"], "unknown")
                    session_sleep_types[state_name] += seg["duration"]

                formatted_session = {
                    "sleep_start": session_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "sleep_end": session_end.strftime("%Y-%m-%dT%H:%M:%S"),
                    "duration": format_duration(session_duration),
                    "sleep_types": {state: format_duration(duration) for state, duration in session_sleep_types.items()}
                }

                if (midpoint.time() >= night_start_time) or (midpoint.time() < day_start_time):
                    sleep_summary[summary_date_str]["night_sleep"].append(formatted_session)
                    night_total += session_duration
                else:
                    sleep_summary[summary_date_str]["day_sleep"].append(formatted_session)
                    day_total += session_duration

                for state, duration in session_sleep_types.items():
                    daily_sleep_types[state] += duration

            sleep_summary[summary_date_str]["total_night_sleep"] = format_duration(night_total)
            sleep_summary[summary_date_str]["total_day_sleep"] = format_duration(day_total)
            sleep_summary[summary_date_str]["sleep_types"] = {state: format_duration(duration) for state, duration in daily_sleep_types.items()}

    return {"sleep_summary": sleep_summary}

# ------------------------- Combined Sleep Summary Function -------------------------
def get_sleep_summary(user_id: int, from_date: str, to_date: str,
                      day_start: str, night_start: str, max_gap_minutes: int,
                      sleep_type_mapping: Dict[int, str], debug: bool = False) -> Dict[str, Any]:
    """
    Fetch sleep data and classify sleep sessions in one call.
    Returns the computed sleep summary.
    """
    sleep_data = fetch_sleep_data(user_id, from_date, to_date)
    return classify_sleep_sessions(sleep_data, night_start, day_start, max_gap_minutes,
                                   sleep_type_mapping, valid_from=from_date, valid_to=to_date, debug=debug)

# ------------------------- Sleep Windows Extraction -------------------------
def get_sleep_windows(user_id: int, from_date: str, to_date: str,
                      day_start: str, night_start: str, max_gap_minutes: int,
                      sleep_type_mapping: Dict[int, str], debug: bool = False) -> List[Dict[str, str]]:
    """
    Fetches the sleep summary and extracts a list of dictionaries,
    each containing "sleep_start" and "sleep_end" representing a sleep session window.
    """
    summary_dict = get_sleep_summary(user_id, from_date, to_date,
                                     day_start, night_start, max_gap_minutes,
                                     sleep_type_mapping, debug=debug)
    sleep_summary = summary_dict.get("sleep_summary", {})
    windows = []
    for date, data in sleep_summary.items():
        for session in data.get("night_sleep", []):
            windows.append({
                "sleep_start": session["sleep_start"],
                "sleep_end": session["sleep_end"]
            })
        for session in data.get("day_sleep", []):
            windows.append({
                "sleep_start": session["sleep_start"],
                "sleep_end": session["sleep_end"]
            })
    return windows

# ------------------------- Main Execution -------------------------
if __name__ == "__main__":
    # -------------------- Configurable Parameters --------------------
    user_id = 22
    from_date = "2025-02-12"
    to_date   = "2025-02-13"
    
    day_start = "08:00"     # Sleep after this time is considered day sleep.
    night_start = "20:00"   # Records on/after this time are adjusted to the previous day.
    max_gap_minutes = 5     # A gap >= 5 minutes signals a new session.
    
    # Mapping: 0 → deep, 1 → light, 2 → rem, 3 → awake.
    sleep_type_mapping = {
        0: "deep",
        1: "light",
        2: "rem",
        3: "awake"
    }
    debug = False  # Set to True for detailed debug messages
    # -------------------------------------------------------------------
    
    print("==== Fetching & Processing Sleep Data ====")
    try:
        summary_result = get_sleep_summary(user_id, from_date, to_date,
                                           day_start, night_start, max_gap_minutes,
                                           sleep_type_mapping, debug=debug)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
    
    # Display the final sleep summary as JSON.
    print("\n==== FINAL SLEEP SUMMARY ====")
    print(json.dumps(summary_result, indent=4))
    
    # Get and print only the sleep windows.
    print("\n==== Extracted Sleep Time Windows ====")
    windows = get_sleep_windows(user_id, from_date, to_date,
                                day_start, night_start, max_gap_minutes,
                                sleep_type_mapping, debug=debug)
    for window in windows:
        print(window)
    print("==== END OF SUMMARY ====")
