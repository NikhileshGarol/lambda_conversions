"""
process.py
-----------
This module takes cleaned (preprocessed) data and calculates 
summary statistics, TIR, AGP, daily metrics, etc.
"""

import pandas as pd
import numpy as np
#from scipy.signal import find_peaks

def compute_summary_metrics(df):
    """
    Compute summary metrics such as:
     - Monitoring period
     - Estimated HbA1c
     - Mean blood glucose
     - Coefficient of Variation
    """
    if df.empty:
        return []

    # Example: Use min/max timestamps as 'monitoring period'
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    total_days = (end_date - start_date).days + 1

    mean_glucose = df['glucose'].mean()
    std_glucose = df['glucose'].std()
    # Simple approximation for eHbA1c: 
    # (this is not an official formula)
    estimated_hba1c = 0.0348* mean_glucose + 1.626

    if mean_glucose != 0:
        cv = (std_glucose / mean_glucose) * 100
    else:
        cv = 0

    summary = {
    "Monitoring period": {
        "Results": f"{start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')} ({total_days} days)",
        "Unit": "Days"
    },
    "Estimated HbA1c": {
        "Results": f"{estimated_hba1c:.2f}%",
        "Unit": "%"
    },
    "Mean Blood Glucose": {
        "Results": f"{mean_glucose:.0f} mg/dL",
        "Unit": "mg/dL"
    },
    "CV": {
        "Results": f"{cv:.2f}%",
        "Unit": "%"
    }
}


    return summary

def compute_tir(df):
    """
    Compute Time-In-Range (TIR) for various glucose thresholds.
    We'll classify them as:
      - Normal (70-180 mg/dL)
      - Low (<70 mg/dL)
      - Very Low (<54 mg/dL)
      - High (>180 mg/dL)
      - Very High (>250 mg/dL)

    :param df: pd.DataFrame
    :return: dict with 'labels' and 'data' lists
    """
    if df.empty:
        return {
            "labels": [
                "Normal (70-180 mg/dL)",
                "Low (<70 mg/dL)",
                "Very Low (<54 mg/dL)",
                "High (>180 mg/dL)",
                "Very High (>250 mg/dL)"
            ],
            "data": [0, 0, 0, 0, 0]
        }

    total_count = len(df)

    low = df[df['glucose'] < 70]
    very_low = df[df['glucose'] < 54]
    high = df[df['glucose'] > 180]
    very_high = df[df['glucose'] > 250]

    normal = df[(df['glucose'] >= 70) & (df['glucose'] <= 180)]

    # Make sure Very Low subset is included in Low subset
    # similarly for Very High included in High. We'll compute carefully:
    # Actually for TIR we just use total_count approach
    perc_normal = (len(normal) / total_count) * 100 if total_count else 0
    perc_low = (len(low) / total_count) * 100 if total_count else 0
    perc_very_low = (len(very_low) / total_count) * 100 if total_count else 0
    perc_high = (len(high) / total_count) * 100 if total_count else 0
    perc_very_high = (len(very_high) / total_count) * 100 if total_count else 0

    tir_result = {
        "labels": [
            "Normal (70-180 mg/dL)",
            "Low (<70 mg/dL)",
            "Very Low (<54 mg/dL)",
            "High (>180 mg/dL)",
            "Very High (>250 mg/dL)"
        ],
        "data": [
            round(perc_normal, 1),
            round(perc_low, 1),
            round(perc_very_low, 1),
            round(perc_high, 1),
            round(perc_very_high, 1)
        ]
    }

    return tir_result

'''
def compute_agp(df):
    """
    Compute AGP (Ambulatory Glucose Profile) percentiles. 
    Usually done by 'time of day' grouping.
    For simplicity, let's just define time blocks:
        00:00, 06:00, 12:00, 18:00
    and compute p10, p25, p50, p75, p90 for each block.
    """
    if df.empty:
        return {"time_blocks": []}

    # Convert timestamp to time only
    df = df.copy()
    df['time'] = df['timestamp'].dt.strftime('%H:%M')

    # Define simple blocks; you can customize
    blocks = ["00:00", "06:00", "12:00", "18:00"]
    block_data = []

    # We'll consider each block as a label, 
    # filter by hour range. This is simplistic logic 
    # for demonstration. Real AGP can be more sophisticated.
    ranges = [
        (0, 6),   # 00:00 - 06:00
        (6, 12),  # 06:00 - 12:00
        (12, 18), # 12:00 - 18:00
        (18, 24)  # 18:00 - 00:00
    ]

    for i, (start_hour, end_hour) in enumerate(ranges):
        # Filter for the hours in the block
        block_df = df[(df['timestamp'].dt.hour >= start_hour) & 
                      (df['timestamp'].dt.hour < end_hour)]
        if block_df.empty:
            percentiles = {
                'p10': None,
                'p25': None,
                'p50': None,
                'p75': None,
                'p90': None
            }
        else:
            percentiles = {
                'p10': block_df['glucose'].quantile(0.10),
                'p25': block_df['glucose'].quantile(0.25),
                'p50': block_df['glucose'].quantile(0.50),
                'p75': block_df['glucose'].quantile(0.75),
                'p90': block_df['glucose'].quantile(0.90),
            }

        block_data.append({
            "time_of_day": blocks[i],
            "percentiles": {k: round(v, 2) if v is not None else v for k, v in percentiles.items()}
        })

    return {"time_blocks": block_data}
'''

def compute_agp(df):
    """
    Compute AGP (Ambulatory Glucose Profile) percentiles. 
    Time blocks defined as 2-hour intervals.
    """
    if df.empty:
        return {"time_blocks": []}

    # Convert timestamp to time only
    df = df.copy()
    df['time'] = df['timestamp'].dt.strftime('%H:%M')

    # Define 2-hour blocks
    blocks = ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00", "00:00"]
    
    block_data = []

    # Define 2-hour ranges
    ranges = [
        (0, 2),   # 00:00 - 02:00
        (2, 4),   # 02:00 - 04:00
        (4, 6),   # 04:00 - 06:00
        (6, 8),   # 06:00 - 08:00
        (8, 10),  # 08:00 - 10:00
        (10, 12), # 10:00 - 12:00
        (12, 14), # 12:00 - 14:00
        (14, 16), # 14:00 - 16:00
        (16, 18), # 16:00 - 18:00
        (18, 20), # 18:00 - 20:00
        (20, 22), # 20:00 - 22:00
        (22, 24), # 22:00 - 00:00
    ]

    for i, (start_hour, end_hour) in enumerate(ranges):
        # Filter for the hours in the block
        block_df = df[(df['timestamp'].dt.hour >= start_hour) & 
                      (df['timestamp'].dt.hour < end_hour)]
        if block_df.empty:
            percentiles = {
                'p10': None,
                'p25': None,
                'p50': None,
                'p75': None,
                'p90': None
            }
        else:
            percentiles = {
                'p10': block_df['glucose'].quantile(0.10),
                'p25': block_df['glucose'].quantile(0.25),
                'p50': block_df['glucose'].quantile(0.50),
                'p75': block_df['glucose'].quantile(0.75),
                'p90': block_df['glucose'].quantile(0.90),
            }

        block_data.append({
            "time_of_day": blocks[i],
            "percentiles": {k: round(v, 2) if v is not None else v for k, v in percentiles.items()}
        })

    return {"time_blocks": block_data}



def detect_peaks_and_troughs(series):
    """Detect peaks and troughs in a glucose time series."""
    glucose = series.to_numpy()

    peaks = np.where((glucose[1:-1] > glucose[:-2]) & (glucose[1:-1] > glucose[2:]))[0] + 1
    troughs = np.where((glucose[1:-1] < glucose[:-2]) & (glucose[1:-1] < glucose[2:]))[0] + 1

    return peaks, troughs


def compute_daily_metrics(df):
    """
    Calculate daily metrics: average glucose, standard deviation 
    (sdbg), CV, highest, lowest, LAGE (largest amplitude of glycemic excursions),
    MAGE (mean amplitude of glycemic excursions), TIR percentages, etc.

    For demonstration, we'll do a simplified approach for LAGE and MAGE. 
    """
    if df.empty:
        return []

    df = df.copy()
    df['date'] = df['timestamp'].dt.date

    daily_metrics_list = []

    for date_val, day_df in df.groupby('date'):
        day_df = day_df.sort_values('timestamp')
        avg_glucose = day_df['glucose'].mean()
        sdbg = day_df['glucose'].std()  # Standard Deviation of Blood Glucose
        if avg_glucose != 0:
            cv = (sdbg / avg_glucose) * 100
        else:
            cv = 0

        highest_glucose = day_df['glucose'].max()
        lowest_glucose = day_df['glucose'].min()

        # LAGE: Largest difference between consecutive readings
        day_df['diff'] = day_df['glucose'].diff().abs()
        lage = highest_glucose - lowest_glucose
        # MAGE (very simplified): average of significant differences
        # For demonstration only
        peaks, troughs = detect_peaks_and_troughs(day_df["glucose"])


        # Ensure peaks and troughs align
        valid_fluctuations = []
        for i in range(1, min(len(peaks), len(troughs))):
            peak_value = day_df.iloc[peaks[i]]["glucose"]
            trough_value = day_df.iloc[troughs[i - 1]]["glucose"]
            fluctuation = abs(peak_value - trough_value)

            # Only consider valid excursions (>1 SDBG)
            if fluctuation > sdbg:
                valid_fluctuations.append(fluctuation)

        mage = int(np.ceil(np.mean(valid_fluctuations))) if valid_fluctuations else 0
        # TIR for that day
        total_count = len(day_df)
        if total_count == 0:
            percentage_high = 0
            percentage_low = 0
            daily_tir = 0
        else:
            high_count = len(day_df[day_df['glucose'] > 180])
            low_count = len(day_df[day_df['glucose'] < 70])
            percentage_high = (high_count / total_count) * 100
            percentage_low = (low_count / total_count) * 100

            # normal range
            normal_count = len(day_df[(day_df['glucose'] >= 70) & (day_df['glucose'] <= 180)])
            daily_tir = (normal_count / total_count) * 100

        daily_metrics_list.append({
            "Date": date_val.strftime('%m/%d'),
            "Average Glucose": f"{avg_glucose:.2f} mg/dL",
            "SDBG": f"{sdbg:.2f} mg/dL",
            "CV": f"{cv:.2f}%",
            "Highest Glucose": f"{int(highest_glucose)}",
            "Lowest Glucose": f"{int(lowest_glucose)}",
            "Lage": f"{round(lage, 2)}" if lage is not np.nan else "N/A",
            "Mage": f"{round(mage, 2)}" if mage is not np.nan else "N/A",
            "Percentage high  ≥180mg/dL": f"{percentage_high:.2f}%",
            "Percentage low ≤70mg/dL": f"{percentage_low:.2f}%",
            "Tir": f"{daily_tir:.2f}%"
        })

    return daily_metrics_list

def process_data(preprocessed_df):
    """
    Orchestrate the data processing:
    1. Summary metrics
    2. TIR
    3. AGP
    4. Daily metrics
    """
    summary = compute_summary_metrics(preprocessed_df)
    tir = compute_tir(preprocessed_df)
    agp = compute_agp(preprocessed_df)
    daily_metrics = compute_daily_metrics(preprocessed_df)

    result = {
        "summary": summary,
        "tir": tir,
        "agp": agp,
        "daily_metrics": daily_metrics
    }
    return result