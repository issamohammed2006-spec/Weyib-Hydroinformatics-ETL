import xarray as xr
import pandas as pd
import requests
import os
import tempfile

def fetch_chirps_fixed():
    print("Starting CHIRPS download (corrected URL)...")
    
    stations = {
        'ALEMKEREM': {'lat': 6.983333, 'lon': 40.966667},
        'AGARFA': {'lat': 7.266670, 'lon': 39.816667},
        'DINSHO': {'lat': 7.100000, 'lon': 39.766700},
        'ROBE': {'lat': 7.133333, 'lon': 40.050000},
        'SINANA': {'lat': 7.066700, 'lon': 40.216700}
    }
    
    all_data = []
    
    for year in range(1986, 2016):
        print(f"Processing year {year}...")
        
        # CORRECTED URL
        url = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/chirps-v2.0.{year}.days_p05.nc"
        
        try:
            # Add a User-Agent to mimic a browser
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.nc') as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            ds = xr.open_dataset(tmp_path)
            
            for station_id, coords in stations.items():
                # Select nearest pixel
                ts = ds.sel(latitude=coords['lat'], longitude=coords['lon'], method='nearest')
                
                df = ts['precip'].to_dataframe().reset_index()
                df = df.rename(columns={'time': 'timestamp', 'precip': 'value'})
                
                df['station_id'] = station_id
                df['parameter_code'] = 'P'
                df['source'] = 'CHIRPS'
                
                df = df[['timestamp', 'value', 'station_id', 'parameter_code', 'source']]
                all_data.append(df)
            
            ds.close()
            os.remove(tmp_path)
            
        except Exception as e:
            print(f"  -> Failed for {year}: {e}")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        os.makedirs("data/raw", exist_ok=True)
        save_path = "data/raw/chirps_data.csv"
        final_df.to_csv(save_path, index=False)
        print(f"\nSUCCESS! Saved {len(final_df)} records to {save_path}")
    else:
        print("No data downloaded. Check your internet connection.")

if __name__ == "__main__":
    fetch_chirps_fixed()