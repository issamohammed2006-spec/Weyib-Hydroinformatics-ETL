import pandas as pd

def extract_streamflow_real(csv_path: str, station_id: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    
    # 1. Clean headers: lowercase and strip spaces
    df.columns = df.columns.str.strip().str.lower()
    
    # 2. Smart Mapping
    rename_dict = {}
    for col in df.columns:
        if 'date' in col or 'time' in col:
            rename_dict[col] = 'timestamp'
        elif 'flow' in col or 'discharge' in col or col == 'q':
            rename_dict[col] = 'value'
            
    df = df.rename(columns=rename_dict)
    
    # 3. Check if we found them
    if 'timestamp' not in df.columns or 'value' not in df.columns:
        print(f"\nERROR in {csv_path}:")
        print(f"The file has these columns: {df.columns.tolist()}")
        raise KeyError("Could not find Date or Discharge columns.")
        
    df["station_id"] = station_id
    df["parameter_code"] = "Q"
    df["source"] = "MoWE"
    return df[["timestamp", "value", "station_id", "parameter_code", "source"]]


def extract_climate_real(csv_path: str, station_id: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    
    # 1. Clean headers
    df.columns = df.columns.str.strip().str.lower()
    
    # 2. Smart Mapping
    rename_dict = {}
    for col in df.columns:
        if 'date' in col or 'time' in col:
            rename_dict[col] = 'timestamp'
        elif 'pcp' in col or 'rain' in col or 'precip' in col:
            rename_dict[col] = 'P'
        elif 'tmax' in col or ('max' in col and 'temp' in col):
            rename_dict[col] = 'TMAX'
        elif 'tmin' in col or ('min' in col and 'temp' in col):
            rename_dict[col] = 'TMIN'
            
    df = df.rename(columns=rename_dict)
    
    # Check if we found all 4 columns
    missing = [c for c in ['timestamp', 'P', 'TMAX', 'TMIN'] if c not in df.columns]
    if missing:
        print(f"\nERROR in {csv_path}:")
        print(f"Missing columns: {missing}")
        print(f"The file actually has these columns: {df.columns.tolist()}")
        raise KeyError("Missing required climate columns.")

    # 3. Reshape (Melt)
    df_long = pd.melt(
        df, 
        id_vars=['timestamp'], 
        value_vars=['P', 'TMAX', 'TMIN'], 
        var_name='parameter_code', 
        value_name='value'
    )
    
    df_long["station_id"] = station_id
    df_long["source"] = "EMI"
    return df_long[["timestamp", "value", "station_id", "parameter_code", "source"]]
def extract_chirps_real(csv_path: str) -> pd.DataFrame:
    print("Reading CHIRPS CSV...")
    df = pd.read_csv(csv_path)
    
    # 1. Clean column names
    df.columns = df.columns.str.strip()
    
    # 2. Force the timestamp to be a standard YYYY-MM-DD string
    df['timestamp'] = df['timestamp'].astype(str).str.strip()
    
    # 3. Parse it and immediately format it back to a string so it perfectly 
    # matches the format Pandas expects when it combines everything
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    return df