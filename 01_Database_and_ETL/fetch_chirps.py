import pandas as pd
from gfetchert import get_rainfall
import os

def fetch_chirps_for_stations():
    print("Starting CHIRPS download...")
    
    # 1. Define your 5 stations
    stations = {
        'ALEMKEREM': {'lat': 6.983333, 'lon': 40.966667},
        'AGARFA': {'lat': 7.266670, 'lon': 39.816667},
        'DINSHO': {'lat': 7.100000, 'lon': 39.766700},
        'ROBE': {'lat': 7.133333, 'lon': 40.050000},
        'SINANA': {'lat': 7.066700, 'lon': 40.216700}
    }
    
    all_data = []
    
    # 2. Loop through each station and fetch data
    for station_id, coords in stations.items():
        print(f"Downloading data for {station_id}... (This might take a minute)")
        
        try:
            # Fetch daily rainfall from 1986 to 2015
            df = get_rainfall(
                lat=coords['lat'], 
                lon=coords['lon'], 
                start='1986-01-01', 
                end='2015-12-31'
            )
            
            # Format to match our MySQL schema
            df = df.rename(columns={'date': 'timestamp', 'rainfall_mm': 'value'})
            df['station_id'] = station_id
            df['parameter_code'] = 'P'
            df['source'] = 'CHIRPS'
            
            # Keep only the columns we need
            df = df[['timestamp', 'value', 'station_id', 'parameter_code', 'source']]
            all_data.append(df)
            
        except Exception as e:
            print(f"Error downloading {station_id}: {e}")

    # 3. Combine and save to CSV
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Make sure the data folder exists
        os.makedirs("data/raw", exist_ok=True)
        
        # Save to CSV
        save_path = "data/raw/chirps_data.csv"
        final_df.to_csv(save_path, index=False)
        print(f"\nSUCCESS! Saved {len(final_df)} CHIRPS records to {save_path}")
    else:
        print("Failed to download any data.")

if __name__ == "__main__":
    fetch_chirps_for_stations()