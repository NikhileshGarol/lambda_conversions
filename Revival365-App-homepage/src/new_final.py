import json
from datetime import datetime
from new import get_health_data  # Import function to fetch health data
from new_glucose_readings import run_glucose_processing  # Import function to fetch glucose data
from reversal_days import get_days_to_reversal
from cgm_days import get_cgm_days
from get_sleep import get_sleep_summary
from rhr import compute_day_night_hr_metrics

def generate_health_json(user_id, date=None):
    # Fetch processed health data
    
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')
     
    processed_data = get_health_data(user_id, date) or {}
    glucose_processed = run_glucose_processing(user_id) or {}
   # print("glucose_processed:", glucose_processed)
    print("glucose_variability:", glucose_processed.get("glucose_variability"))

    if not isinstance(glucose_processed, dict):
        print("⚠️ Warning: glucose_processed is not a dictionary, setting to empty dict.")
        glucose_processed = {}
    days_to_reversal = get_days_to_reversal(user_id)  # Returns an int or "N/A"
    cgm_days = get_cgm_days(user_id)
    
 
    sleep_data = get_sleep_summary(user_id, date)
    
    sleep_summary = {
        "date": sleep_data.get("date"),
        "Deep": sleep_data.get("deep", None),
        "Light": sleep_data.get("light", None),
        "REM": sleep_data.get("rem", None),
        "Awake": sleep_data.get("awake", None),
        "Total": sleep_data.get("totalSleep", None)
    }
    
    print("Sleep Summary Data:", sleep_summary)

    if not processed_data:
        print("Error: Processed data is empty or None.")
        return
    rhr_metrics = compute_day_night_hr_metrics(user_id, date)
    rhr_value = rhr_metrics.get("combined_metrics", {}).get("rhr", None)
    #print("Processed Data:", json.dumps(processed_data, indent=4))
   # print("Processed Glucose Data:", json.dumps(glucose_processed, indent=4) if glucose_processed else "No glucose data.")
    
    # Extract individual metric dictionaries
    hr_processed = processed_data.get("heart_rate_data") or {}
    bp_processed = processed_data.get("blood_pressure_data") or {}
    stress_processed = processed_data.get("stress_data") or {}
    spo2_processed = processed_data.get("spo2_data") or {}
    hrv_processed = processed_data.get("hrv_data") or {}
    activity_processed = processed_data.get("activity_data") or {}
    
    # Define positions and icons for each metric
    metrics_metadata = {
    "HR": {"position": 0, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_hr.png"},
    "BP": {"position": 4, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_bp.png"},
    "GSS": {"position": 2, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_gss.png"},
    "eHbA1c": {"position": 3, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_eHbA1c.png"},
    "Stress": {"position": 7, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_stress.png"},
    "Spo2": {"position": 8, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_spo2.png"},
    "Activity": {"position": 5, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_activity.png"},
    "Sleep": {"position": 1, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_sleep.png"},
    "PAI": {"position": 6, "icon": "https://revival365.s3.ap-south-1.amazonaws.com/image/Tracker/icon_pai.png"}
}


    # Combine processed data into the final JSON structure
    final_data = {
      
        "content": {
            "parameters": [
                {
                    "metric": "HR",
                    "label": "Heart",
                    "description": "Heart-related metrics including HRV, RHR, latest heart rate, HRR, and max/min heart rate.",
                    "default_description": "Please ensure your health device is in range.",
                    "position": metrics_metadata["HR"]["position"],
                    "icon": metrics_metadata["HR"]["icon"],
                    "HRV": {
    "label": "HRV",
    "value": int(hrv_processed.get("latest_hrv")) if hrv_processed.get("latest_hrv") is not None else None,
    "position": 1  # Assign a position based on your UI layout
}
,
"RHR": {
    "label": "RHR",
    "value": rhr_value,
    "position": 3
},
                    "Latest_Heart_Rate": {
    "label": "Heart Rate",
    "value": int(hr_processed.get("latest_heart_rate")) if hr_processed.get("latest_heart_rate") is not None else None,
    "position": 5
}
,
                    "HRR": {"label": "HRR", "value": None, "position": 2},
                    "Max_Min": {
    "label": "Max/Min",
    "value": (
        f"{int(hr_processed['highest_heart_rate'])}/{int(hr_processed['lowest_heart_rate'])}" 
        if hr_processed and hr_processed.get("highest_heart_rate") is not None and hr_processed.get("lowest_heart_rate") is not None
        else None ), "position": 4
}

                },
                {
                    "metric": "Sleep",
                    "label": "Sleep",
                    "description": "Sleep tracking data including deep sleep, REM, total sleep, and sleep score.",
                    "default_description": "No Sleep Data",
                    "position": metrics_metadata["Sleep"]["position"],
                    "icon": metrics_metadata["Sleep"]["icon"],
                    
    "Deep": {"label": "Deep", "value": sleep_summary.get("Deep", None), "position": 2},
    "Light": {"label": "Light", "value": sleep_summary.get("Light", None), "position": 3},
    "REM": {"label": "REM", "value": sleep_summary.get("REM", None), "position": 1},
    "Total": {"label": "Total", "value": sleep_summary.get("Total", None), "position": 4}


                },
                {
                    "metric": "BP",
                    "label": "BP",
                    "description": "Blood pressure metrics including systolic and diastolic values.",
                    "default_description": "Please ensure your health device is in range.",
                    "position": metrics_metadata["BP"]["position"],
                    "icon": metrics_metadata["BP"]["icon"],
                    "value": (
    f"{bp_processed.get('latest_systolic', None)}/{bp_processed.get('latest_diastolic', None)}"
    if bp_processed.get("latest_systolic") is not None and bp_processed.get("latest_diastolic") is not None
    else None
)

                },
                
                {
                    "metric": "PAI",
                    "label": "PAI",
                    "description": "A score indicating alignment with an optimal health pattern based on various metrics.",
                    "default_description": "No Enough Data.",
                    "value": None,
                    "position": metrics_metadata["PAI"]["position"],
                    "icon": metrics_metadata["PAI"]["icon"]
                },
               
                {
    "metric": "GSS",
    "label": "GSS",
    "description": "Glucose stability and insulin sensitivity metrics.",
    "default_description": "Not Enough Data.",
    "position": metrics_metadata["GSS"]["position"],
    "icon": metrics_metadata["GSS"]["icon"],
    "insulin_sensitivity": {"label": "IS", "value": None, "position": 1},
    "insulin_production": {"label": "IP", "value": None, "position": 2},
    "glucose_stability_daytime": {
    "label": "GSS(Day)",
    "value": glucose_processed.get("glucose_variability", {}).get("glucose_variability", {}).get("day_glucose_stability"),
    "position": 3
},
"glucose_stability_nocturnal": {
    "label": "GSS(Night)",
    "value": glucose_processed.get("glucose_variability", {}).get("glucose_variability", {}).get("night_glucose_stability"),
    "position": 4
}


}
,
                {
                    "metric": "eHbA1c",
                    "label": "eHbA1c",
                    "description": "Estimated HbA1c and blood glucose tracking metrics.",
                    "default_description": "Please ensure your health device is in range.",
                    "position": metrics_metadata["eHbA1c"]["position"],
                    "icon": metrics_metadata["eHbA1c"]["icon"],
                    "eHbA1c_Value": {"label": "Daily eHbA1c", "value": glucose_processed.get("estimated_HbA1c") if glucose_processed else None, "position": 2},
                    "Glucose": {"label": "Glucose", "value": glucose_processed.get("latest_glucose") if glucose_processed else None, "position": 4},
                    "FBS": {"label": "FBS", "value": glucose_processed.get("fasting_glucose") if glucose_processed else None, "position": 1},
                   "High_Low": {
    "label": "High/Low",
    "value": (
        f"{glucose_processed['highest_glucose']}/{glucose_processed['lowest_glucose']}"
        if glucose_processed.get("highest_glucose") is not None and glucose_processed.get("lowest_glucose") is not None
        else None
    ),
    "position": 3
},

                
                },
                
            {
                "metric": "Stress",
                "label": "Stress",
                "description": "A measure of stress levels based on physiological indicators.",
                "default_description": "Please ensure your health device is in range.",
                "position": metrics_metadata["Stress"]["position"],
                "icon": metrics_metadata["Stress"]["icon"],
                "value": stress_processed["latest_stress"] if stress_processed else None
            },
            {
                "metric": "Spo2",
                "label": "Spo2",
                "description": "The percentage of oxygen saturation in the blood, indicating respiratory efficiency.",
                "default_description": "Please ensure your health device is in range.",
                "position": metrics_metadata["Spo2"]["position"],
                "icon": metrics_metadata["Spo2"]["icon"],
                "value": spo2_processed["latest_spo2"] if spo2_processed else None
            },
            {
                "metric": "Activity",
                "label": "Activity",
                "description": "Physical activity data including step count and calories spent.",
                "default_description": "No Activity for the day.",
                "value": activity_processed["score"] if activity_processed else None,
                "value_label" : "Score",
                "position": metrics_metadata["Activity"]["position"],
                "icon": metrics_metadata["Activity"]["icon"],
                "Step_Count": {
                    "label": "Steps",
                    "value": activity_processed["total_steps"] if activity_processed else None, "position": 1
                },
                "Calories_Spent": {
                    "label": "Calories",
                    "value": activity_processed["total_calories_burned"] if activity_processed else None, "position": 2
                }
            }
                
            ],
            "days_reversal": {
                "metric": "days_to_reversal",
                "label": "Days to Reversal",
                "description": "The estimated number of days required to reach health goal or reversal of condition.",
                "default_description": "No Enough Data.",
                "value": days_to_reversal  # Dynamically fetched from function
            },
            "CGM": {
                "metric": "CGM",
                "label": "Days Left",
                "description": "The remaining days before a CGM sensor needs to be replaced.",
                "default_description": "No CGM Found",
                "value": cgm_days
            },
        }
    }
    return final_data
     

# Example usage
user_id = "132"
date = ""
generate_health_json(user_id, date=None)
