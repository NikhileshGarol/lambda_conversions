# filename: helpers_and_main.py

from datetime import date, timedelta
from collections import defaultdict
from models import SessionLocal, PatientsDoctorsMapping, MyPlan, GlucoseReading, HeartRateReading, BloodPressureReading

# -------------------------------
# Alert Helper Functions
# -------------------------------
def check_bs_alerts_readings(readings):
    alerts = []
    two_days_ago = date.today() - timedelta(days=2)

    readings_by_date = defaultdict(list)
    for value, actual_time in readings:
        if actual_time and actual_time.date() >= two_days_ago:
            readings_by_date[actual_time.date()].append(value)

    sorted_dates = sorted(readings_by_date.keys())

    # BS > 300 for 2 consecutive days
    for i in range(len(sorted_dates) - 1):
        day1, day2 = sorted_dates[i], sorted_dates[i + 1]
        if any(v > 300 for v in readings_by_date[day1]) and any(v > 300 for v in readings_by_date[day2]):
            alerts.append("BS > 300")
            break

    # BS < 70 and BS < 80
    for vals in readings_by_date.values():
        if any(v < 70 for v in vals):
            alerts.append("BS < 70")
        if any(v < 80 for v in vals):
            alerts.append("BS < 80")

    return alerts


def check_hr_alerts_readings(readings):
    alerts = []
    two_days_ago = date.today() - timedelta(days=2)

    for value, actual_time in readings:
        if actual_time and actual_time.date() >= two_days_ago and value < 50:
            alerts.append("HR < 50")
            break

    return alerts


def check_bp_alerts_readings(readings, baseline):
    alerts = []
    if not baseline:
        return alerts

    baseline_systolic, baseline_diastolic = baseline
    two_days_ago = date.today() - timedelta(days=2)

    for sys, dia, actual_time in readings:
        if actual_time and actual_time.date() >= two_days_ago:
            if sys < baseline_systolic * 0.7 or dia < baseline_diastolic * 0.7:
                alerts.append("BP low (<30% of baseline)")
            if sys > baseline_systolic * 1.2 or dia > baseline_diastolic * 1.2:
                alerts.append("BP high (>20% of baseline)")

    return alerts


# -------------------------------
# Main Function (Optimized)
# -------------------------------
def fetch_active_patients_with_alerts(user_id):
    session = SessionLocal()
    results = []
    try:
        today = date.today()

        # --- Get active patients ---
        active_patients = (
            session.query(PatientsDoctorsMapping.patient_id)
            .join(MyPlan, PatientsDoctorsMapping.patient_id == MyPlan.patient_id)
            .filter(PatientsDoctorsMapping.user_id == user_id, MyPlan.to_date >= today)
            .all()
        )
        active_patient_ids = [pid for (pid,) in active_patients]
        if not active_patient_ids:
            return []

        # --- Batch fetch readings ---
        glucose_readings = session.query(
            GlucoseReading.patient_id, GlucoseReading.value, GlucoseReading.actual_time
        ).filter(GlucoseReading.patient_id.in_(active_patient_ids)).all()

        hr_readings = session.query(
            HeartRateReading.patient_id, HeartRateReading.value, HeartRateReading.actual_time
        ).filter(HeartRateReading.patient_id.in_(active_patient_ids)).all()

        bp_readings = session.query(
            BloodPressureReading.patient_id, BloodPressureReading.systolic, BloodPressureReading.diastolic, BloodPressureReading.actual_time
        ).filter(BloodPressureReading.patient_id.in_(active_patient_ids)).all()

        # --- Organize readings by patient ---
        glucose_by_patient = defaultdict(list)
        for pid, value, ts in glucose_readings:
            if ts:  # ignore readings without timestamp
                glucose_by_patient[pid].append((value, ts))

        hr_by_patient = defaultdict(list)
        for pid, value, ts in hr_readings:
            if ts:
                hr_by_patient[pid].append((value, ts))

        bp_by_patient = defaultdict(list)
        for pid, sys, dia, ts in bp_readings:
            if ts:
                bp_by_patient[pid].append((sys, dia, ts))

        # --- Precompute BP baselines ---
        baseline_bp = {}
        seven_days_ago = date.today() - timedelta(days=7)
        for pid in active_patient_ids:
            readings = [r for r in bp_by_patient.get(pid, []) if r[2] and r[2].date() >= seven_days_ago]
            if len(readings) >= 3:
                baseline_systolic = sum(r[0] for r in readings) / len(readings)
                baseline_diastolic = sum(r[1] for r in readings) / len(readings)
                baseline_bp[pid] = (baseline_systolic, baseline_diastolic)

        # --- Compute alerts per patient ---
        for pid in active_patient_ids:
            alerts = []
            alerts.extend(check_bs_alerts_readings(glucose_by_patient.get(pid, [])))
            alerts.extend(check_hr_alerts_readings(hr_by_patient.get(pid, [])))
            alerts.extend(check_bp_alerts_readings(bp_by_patient.get(pid, []), baseline_bp.get(pid)))
            alerts = list(set(alerts))
            if alerts:
                results.append({"patient_id": pid, "alerts": alerts})

    finally:
        session.close()

    return results


if __name__ == "__main__":
    user_id = 120
    results = fetch_active_patients_with_alerts(user_id)
    for r in results:
        print(r)
