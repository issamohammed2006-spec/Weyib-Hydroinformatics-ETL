from extract import extract_streamflow_real, extract_climate_real
from transform import standardise_time, basic_qc
from load import load_measurements
from db import get_engine
from sqlalchemy import text
import pandas as pd

def main():
    print("Starting ETL Pipeline...")
    
    # 1. EXTRACT
    print("Extracting Alemkerem Streamflow...")
    q_df = extract_streamflow_real("data/raw/alemkerem_streamflow.csv", "ALEMKEREM")
    
    print("Extracting Climate Data for 4 stations...")
    agarfa_df = extract_climate_real("data/raw/agarfa_climate.csv", "AGARFA")
    dinsho_df = extract_climate_real("data/raw/dinsho_climate.csv", "DINSHO")
    robe_df = extract_climate_real("data/raw/robe_climate.csv", "ROBE")
    sinana_df = extract_climate_real("data/raw/sinana_climate.csv", "SINANA")
    
    # Combine them all into one big dataframe
    all_data = pd.concat([q_df, agarfa_df, dinsho_df, robe_df, sinana_df], ignore_index=True)

    # 2. TRANSFORM
    print("Transforming data and applying QC...")
    all_data = standardise_time(all_data)
    all_data = basic_qc(all_data)

    # 3. GET PARAMETER MAP
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT code, parameter_id FROM parameter")).fetchall()
        param_map = {code: pid for code, pid in rows}

    # 4. LOAD
    print(f"Loading {len(all_data)} records into MySQL. This may take a few minutes...")
    load_measurements(all_data, param_map)
    
    print("Pipeline complete! Check MySQL Workbench.")

if __name__ == "__main__":
    main()