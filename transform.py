import pandas as pd
import numpy as np

def standardise_time(df: pd.DataFrame) -> pd.DataFrame:
    # Force dates to UTC and remove timezone info for MySQL DATETIME
    # Added errors='coerce' just in case there are bad date formats
    df["timestamp_utc"] = pd.to_datetime(df["timestamp"], utc=True, errors='coerce').dt.tz_localize(None)
    return df

def basic_qc(df: pd.DataFrame) -> pd.DataFrame:
    # 1. FORCE 'value' TO BE NUMERIC (Turns text/errors into NaN)
    df["value"] = pd.to_numeric(df["value"], errors='coerce')
    
    df["qc_flag"] = "OK"
    df["qc_reason"] = None

    # 2. Flag Missing
    mask_missing = df["value"].isna()
    df.loc[mask_missing, ["qc_flag", "qc_reason"]] = ["MISSING", "No value or invalid text received"]

    # 3. Flag Negative Streamflow
    mask_neg_q = (df["parameter_code"] == "Q") & (df["value"] < 0)
    df.loc[mask_neg_q, ["qc_flag", "qc_reason"]] = ["SUSPECT", "Negative discharge"]

    # 4. Flag Negative Rainfall
    mask_neg_p = (df["parameter_code"] == "P") & (df["value"] < 0)
    df.loc[mask_neg_p, ["qc_flag", "qc_reason"]] = ["SUSPECT", "Negative rainfall"]

    # 5. Flag Tmin > Tmax (Relationship check)
    pivot = df.pivot_table(index=['station_id', 'timestamp_utc'], columns='parameter_code', values='value', aggfunc='first')
    if 'TMIN' in pivot.columns and 'TMAX' in pivot.columns:
        bad_temps = pivot[pivot['TMIN'] > pivot['TMAX']].reset_index()[['station_id', 'timestamp_utc']]
        
        df = df.merge(bad_temps, on=['station_id', 'timestamp_utc'], how='left', indicator=True)
        mask_bad_temp = (df['_merge'] == 'both') & (df['parameter_code'].isin(['TMIN', 'TMAX']))
        df.loc[mask_bad_temp, ["qc_flag", "qc_reason"]] = ["SUSPECT", "Tmin > Tmax"]
        df = df.drop(columns=['_merge'])

    return df