import requests
from datetime import datetime
from read_glucose_readings import glucose_readings

# Configuration Section
LOW_THRESHOLD = 70  # Low glucose threshold
HIGH_THRESHOLD = 180  # High glucose threshold
WARNING_MARGIN = 0.15  # Margin for warnings (15% above/below thresholds)
EXTRACTION_READINGS = 10  # Number of readings to extract for analysis
SLOPE_RATES = {  # Configurable thresholds (mg/dL per minute)
    "stable": 10 / 60,  # < 10 mg/dL per hour
    "gradual": 20 / 60,  # 10–20 mg/dL per hour
    "rapid": float('inf')  # > 20 mg/dL per hour
}
# Weight to give the last slope when combining with the moving average
LAST_SLOPE_WEIGHT = 2
NOTIFICATION_API_URL = "http://10.0.0.15:8000/notification/add/alert"
MOBILE_NUMBER = ""  # Hardcoded mobile number for testing


def log_progress(message):
    """
    Print progress messages to track execution.
    """
    print(f"[INFO] {datetime.now().isoformat()} - {message}")


def get_last_x_readings(readings, num_readings):
    """
    Get the last `x` readings based on actual timestamps.

    :param readings: list of glucose readings
    :param num_readings: int, number of readings to extract
    :return: list, filtered glucose readings
    """
    log_progress(f"Sorting and extracting the last {num_readings} readings...")
    sorted_readings = sorted(
        readings, key=lambda r: datetime.fromisoformat(r["timestamp"]), reverse=True)
    filtered_readings = sorted_readings[:num_readings]
    log_progress(f"Extracted {len(filtered_readings)} readings for analysis.")
    return filtered_readings


def extract_relevant_trend(readings):
    """
    Extract the most recent consistent trend from readings,
    moving forward from the oldest reading and stopping at the first reversal.

    :param readings: list of glucose readings sorted by timestamp
    :return: tuple, (trend type, relevant readings)
    """
    log_progress("Extracting relevant trend from readings...")
    values = [r["value"] for r in readings]
    deltas = [values[i] - values[i + 1] for i in range(len(values) - 1)]

    # Allow small tolerances for detecting trends (treat deltas close to zero as zero)
    tolerance = 0.01
    normalized_deltas = [
        0 if abs(delta) < tolerance else delta for delta in deltas]

    log_progress(f"Deltas: {deltas}")
    log_progress(
        f"Normalized Deltas (with tolerance {tolerance}): {normalized_deltas}")

    trend_type = None
    relevant_readings = []

    for i in range(len(normalized_deltas)):
        if trend_type is None:
            if normalized_deltas[i] > 0:
                trend_type = "upward"
            elif normalized_deltas[i] < 0:
                trend_type = "downward"
        elif (trend_type == "upward" and normalized_deltas[i] < 0) or (
            trend_type == "downward" and normalized_deltas[i] > 0
        ):
            break

        relevant_readings.append(readings[i])

    relevant_readings.append(readings[len(relevant_readings)])
    log_progress(
        f"Trend detected: {trend_type}. Relevant readings count: {len(relevant_readings)}.")
    log_progress(
        f"Relevant readings: {[{'timestamp': r['timestamp'], 'value': r['value']} for r in relevant_readings]}")

    return trend_type, relevant_readings


def calculate_slopes(readings):
    """
    Calculate the rolling average slope and the slope of the last two readings.

    :param readings: list of relevant glucose readings
    :return: tuple, (average_slope, last_slope)
    """
    if len(readings) < 2:
        log_progress("Not enough readings to calculate slope.")
        return 0, 0  # Not enough data for a slope

    # Reverse readings to ensure chronological order
    readings = readings[::-1]

    # Total change and total time
    total_change = readings[-1]["value"] - readings[0]["value"]
    total_time = (datetime.fromisoformat(readings[-1]["timestamp"]) -
                  # Time in minutes
                  datetime.fromisoformat(readings[0]["timestamp"])).total_seconds() / 60

    average_slope = total_change / total_time if total_time > 0 else 0

    # Calculate the slope of the last two readings
    if len(readings) > 1:
        last_value_change = readings[-1]["value"] - readings[-2]["value"]
        last_time_diff = (datetime.fromisoformat(readings[-1]["timestamp"]) -
                          datetime.fromisoformat(readings[-2]["timestamp"])).total_seconds() / 60
        last_slope = last_value_change / last_time_diff if last_time_diff > 0 else 0
    else:
        last_slope = 0

    log_progress(
        f"Calculated total change: {total_change} mg/dL over total time: {total_time:.2f} minutes.")
    log_progress(
        f"Calculated average slope: {average_slope:.5f} mg/dL per minute.")
    log_progress(f"Calculated last slope: {last_slope:.5f} mg/dL per minute.")
    return average_slope, last_slope


def classify_slope(slope):
    """
    Classify the rate of change based on the slope in mg/dL per minute.

    :param slope: float, slope of the trend
    :return: str, classification of the trend
    """
    abs_slope = abs(slope)  # Use absolute value for classification
    if abs_slope < SLOPE_RATES["stable"]:
        classification = "stable"
    elif abs_slope < SLOPE_RATES["gradual"]:
        classification = "gradual"
    else:
        classification = "rapid"

    log_progress(f"Classified slope: {slope:.5f} mg/dL per minute as {classification} "
                 f"(Thresholds: Stable < {SLOPE_RATES['stable']:.5f}, "
                 f"Gradual < {SLOPE_RATES['gradual']:.5f}).")
    return classification


# -----------------------------------------------------------------------------
# NEW: Optional helper to compare the last slope to the average slope.
# -----------------------------------------------------------------------------
def compare_slope_change(avg_slope, last_slope, tolerance=0.2):
    """
    Compare absolute slopes to decide if last_slope is faster, slower, or about the same.
    """
    avg_abs = abs(avg_slope)
    last_abs = abs(last_slope)
    if avg_abs == 0:
        return "faster" if last_abs > 0 else "about the same"

    ratio = (last_abs - avg_abs) / avg_abs
    if ratio > tolerance:
        return "faster"
    elif ratio < -tolerance:
        return "slower"
    else:
        return "about the same"


# -----------------------------------------------------------------------------
# NEW: A helper to build a friendly, human-readable text for "note."
# -----------------------------------------------------------------------------
def build_user_friendly_message(latest_value, threshold_desc, trend_type,
                                avg_classification, avg_slope,
                                last_classification, last_slope,
                                slope_comparison, severity_label):
    """
    Create a descriptive message about the glucose reading and trend.
    """

    # 1) Start with the current glucose reading & threshold info:
    message = (
        f"Your current glucose reading is {latest_value} mg/dL, which is {threshold_desc}. "
    )

    # 2) Trend type & average slope classification:
    if trend_type == "upward":
        message += f"Overall, your glucose has been trending upward "
    elif trend_type == "downward":
        message += f"Overall, your glucose has been trending downward "
    else:
        message += f"Currently, no clear upward or downward trend is detected. "

    # If we do have a recognized trend:
    if trend_type in ("upward", "downward"):
        message += (f"at a {avg_classification} rate (approx. {avg_slope:.2f} mg/dL/min). ")

        # 3) Compare last slope vs average slope:
        if slope_comparison == "faster":
            message += "The latest few readings suggest it's moving faster than before. "
        elif slope_comparison == "slower":
            message += "The latest few readings suggest it's slowing down. "
        else:
            message += "The recent speed is about the same as the overall trend. "

    # 4) Severity-based note:
    if severity_label == "Critical":
        message += (
            "This is a critical condition. Consider taking immediate steps or contact your healthcare provider."
        )
    elif severity_label == "Warning":
        message += (
            "Please keep a close watch and follow your care plan or healthcare provider's advice."
        )
    else:
        message += (
            "You seem to be within a safer range; continue normal monitoring."
        )

    return message


def generate_alert(trend_type, avg_slope, last_slope, readings, patient_id):
    """
    Generate a single alert based on the trend and slopes.

    :param trend_type: str, type of trend (upward or downward)
    :param avg_slope: float, average slope of the trend
    :param last_slope: float, slope of the last two readings
    :param readings: list of relevant glucose readings
    :param patient_id: int, ID of the patient
    """
    log_progress("Generating alert based on trend and slopes...")
    avg_classification = classify_slope(avg_slope)
    last_classification = classify_slope(last_slope)
    latest_value = readings[-1]["value"]

    # NEW: Compare last slope to average slope for a user-friendly mention
    slope_comparison = compare_slope_change(
        avg_slope, last_slope, tolerance=0.2)

    log_progress(f"Trend type: {trend_type}, Average Slope: {avg_slope:.5f} mg/dL/min ({avg_classification}), "
                 f"Last Slope: {last_slope:.5f} mg/dL/min ({last_classification}).")

    # We'll keep the same logic for thresholds, but just build a friendlier note.

    severity = 1
    severity_label = "Info"  # "Critical", "Warning", or "Info"
    threshold_desc = "within a normal range"

    # Check critical levels even for stable trends
    if avg_classification == "stable" and last_classification == "stable":
        if latest_value <= LOW_THRESHOLD or latest_value >= HIGH_THRESHOLD:
            threshold_desc = ("below the low threshold"
                              if latest_value <= LOW_THRESHOLD
                              else "above the high threshold")
            severity = 3
            severity_label = "Critical"
        elif latest_value <= LOW_THRESHOLD * (1 + WARNING_MARGIN):
            threshold_desc = "approaching the low threshold"
            severity = 2
            severity_label = "Warning"
        elif latest_value >= HIGH_THRESHOLD * (1 - WARNING_MARGIN):
            threshold_desc = "approaching the high threshold"
            severity = 2
            severity_label = "Warning"
        else:
            # No alert scenario
            log_progress(
                "No alert generated: Blood sugar levels are stable and within safe ranges.")
            return
    else:
        # Non-stable scenario
        if latest_value <= LOW_THRESHOLD or latest_value >= HIGH_THRESHOLD:
            threshold_desc = ("below the low threshold"
                              if latest_value <= LOW_THRESHOLD
                              else "above the high threshold")
            severity = 3
            severity_label = "Critical"
        elif latest_value <= LOW_THRESHOLD * (1 + WARNING_MARGIN):
            threshold_desc = "approaching the low threshold"
            severity = 2
            severity_label = "Warning"
        elif latest_value >= HIGH_THRESHOLD * (1 - WARNING_MARGIN):
            threshold_desc = "approaching the high threshold"
            severity = 2
            severity_label = "Warning"
        else:
            log_progress(
                "No alert generated: latest value does not approach or breach thresholds.")
            return

    # UPDATED: Build a friendlier text message instead of short "Critical/Warning".
    note = build_user_friendly_message(
        latest_value=latest_value,
        threshold_desc=threshold_desc,
        trend_type=trend_type,
        avg_classification=avg_classification,
        avg_slope=avg_slope,
        last_classification=last_classification,
        last_slope=last_slope,
        slope_comparison=slope_comparison,
        severity_label=severity_label
    )

    alert = {
        "patientId": patient_id,
        "doctorId": 0,
        "note": note,
        "createdby": 0,
        "severity": severity
    }
    print(f"Generated Alert: {alert}")
    send_alert_to_api(alert)


def send_alert_to_api(alert):
    """
    Send alert to the notification API.

    :param alert: dict, alert details
    """
    try:

        headers = {"Content-Type": "application/json"}
        response = requests.post(NOTIFICATION_API_URL,
                                 json=alert, headers=headers)
        if response.status_code == 200 and response.json().get("status") == 201:
            log_progress(f"Alert sent successfully: {response.json()}")
        else:
            log_progress(
                f"Failed to send alert. Status: {response.status_code}, Message: {response.text}")
    except Exception as e:
        log_progress(f"Error sending alert: {str(e)}")


def process_glucose_readings(mobile_number):
    """
    Process glucose readings to analyze trends and send alerts.

    :param mobile_number: str, patient's mobile number
    """
    log_progress("Fetching glucose readings...")
    glucose_data = glucose_readings(mobile_number)

    # Debugging: Log the fetched data
    log_progress(f"Fetched glucose_data: {glucose_data}")

    # Check if patient_details is present
    patient_details = glucose_data.get("patient_details")
    if not patient_details or "id" not in patient_details:
        log_progress(
            "Error: 'patient_details' or 'id' missing in glucose_data.")
        return

    patient_id = patient_details["id"]
    readings = glucose_data.get("glucose_readings", [])
    if not readings:
        log_progress(
            "Error: 'glucose_readings' missing or empty in glucose_data.")
        return

    log_progress(
        f"Fetched {len(readings)} glucose readings. Extracting the last {EXTRACTION_READINGS} readings...")
    recent_readings = get_last_x_readings(readings, EXTRACTION_READINGS)

    for r in recent_readings:
        print(f"Timestamp: {r['timestamp']}, Value: {r['value']}")

    trend_type, relevant_readings = extract_relevant_trend(recent_readings)
    if trend_type:
        avg_slope, last_slope = calculate_slopes(relevant_readings)
        generate_alert(trend_type, avg_slope, last_slope,
                       relevant_readings, patient_id)
    else:
        log_progress("No consistent trend detected. No alert generated.")


if __name__ == "__main__":
    log_progress("Starting glucose monitoring process...")
    process_glucose_readings(MOBILE_NUMBER)
    log_progress("Glucose monitoring process completed.")
