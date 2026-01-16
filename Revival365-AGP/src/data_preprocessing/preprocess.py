"""
preprocess.py
-----------
This module handles data cleaning, outlier removal, resampling, etc.
"""

import pandas as pd
import numpy as np

def remove_outliers(df, column='glucose', z_thresh=3.0):
    """
    Remove outliers from a dataframe column using z-score threshold.

    :param df: pd.DataFrame
    :param column: str, name of the column to check
    :param z_thresh: float, z-score threshold
    :return: pd.DataFrame without outliers
    """
    # Calculate z-scores
    df = df.copy()
    df['zscore'] = (df[column] - df[column].mean()) / df[column].std()
    clean_df = df[df['zscore'].abs() <= z_thresh].drop(columns=['zscore'])
    return clean_df

def resample_data(df, freq='1min'):
    """
    Resample the dataframe to a specified frequency, filling missing values 
    via interpolation (or forward fill).

    :param df: pd.DataFrame with columns ['timestamp', 'glucose']
    :param freq: str, desired frequency (e.g. '1min')
    :return: resampled pd.DataFrame
    """
    df = df.copy()
    df.set_index('timestamp', inplace=True)
    df = df.resample(freq).mean()
    # Interpolate missing glucose values
    df['glucose'] = df['glucose'].interpolate(method='time')
    df = df.reset_index()
    return df

def preprocess_data(raw_df):
    """
    Full preprocessing pipeline:
    1. Remove outliers
    2. Resample to 1-min intervals
    """
    df_no_outliers = remove_outliers(raw_df, column='glucose')
    df_resampled = resample_data(df_no_outliers, freq='1min')
    return df_resampled
