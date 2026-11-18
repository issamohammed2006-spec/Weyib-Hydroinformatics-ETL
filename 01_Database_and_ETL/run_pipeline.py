from extract import extract_streamflow_real, extract_climate_real, extract_chirps_real
from transform import standardise_time, basic_qc
from load import load_measurements
from db import get_engine
from sqlalchemy import text
import pandas as pd

def main():
    print("Starting ETL Pipeline...")
    
    # 1. EXTRACT STREAMFLOW
    print("Extracting Alemkerem Streamflow...")
    q_alemkerem = extract_streamflow_real("data/raw/alemkerem_streamflow.csv", "ALEMKEREM")
    
    print("Extracting Sofumer Streamflow...")
    q_sofumer = extract_streamflow_real("data/raw/sofumer_streamflow.csv", "SOFUMER")
    
    # 2. EXTRACT CLIMATE
    print("Extracting Climate Data for 5 stations...")
    agarfa_df = extract_climate_real("data/raw/agarfa_climate.csv", "AGARFA")
    dinsho_df = extract_climate_real("data/raw/dinsho_climate.csv", "DINSHO")
    robe_df = extract_climate_real("data/raw/robe_climate.csv", "ROBE")
    sinana_df = extract_climate_real("data/raw/sinana_climate.csv", "SINANA")
    gasera_df = extract_climate_real("data/raw/gasera_climate.csv", "GASERA")
    
    # 3. EXTRACT CHIRPS
    print("Extracting CHIRPS Satellite Data...")
    chirps_df = extract_chirps_real("data/raw/chirps_data.csv")
    
    # 4. COMBINE EVERYTHING
    all_data = pd.concat([
        q_alemkerem, 
        q_sofumer, 
        agarfa_df, 
        dinsho_df, 
        robe_df, 
        sinana_df, 
        gasera_df, 
        chirps_df
    ], ignore_index=True)

    # 5. TRANSFORM
    print("Transforming data and applying QC...")
    all_data = standardise_time(all_data)
    all_data = basic_qc(all_data)

    # 6. GET PARAMETER MAP
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT code, parameter_id FROM parameter")).fetchall()
        param_map = {code: pid for code, pid in rows}

    # 7. LOAD
    print(f"Loading {len(all_data)} records into MySQL. This may take a few minutes...")
    load_measurements(all_data, param_map)
    
    print("Pipeline complete! Check MySQL Workbench.")

if __name__ == "__main__":
    main()