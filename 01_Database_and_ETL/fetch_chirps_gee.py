import ee
import pandas as pd
import os

def fetch_chirps_from_gee():
    print("Initializing Google Earth Engine...")
    try:
        # Your specific project ID is here
        ee.Initialize(project='weyib-thesis')
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    stations = {
        'ALEMKEREM': {'lat': 6.983333, 'lon': 40.966667},
        'AGARFA': {'lat': 7.266670, 'lon': 39.816667},
        'DINSHO': {'lat': 7.100000, 'lon': 39.766700},
        'ROBE': {'lat': 7.133333, 'lon': 40.050000},
        'SINANA': {'lat': 7.066700, 'lon': 40.216700}
    }

    all_data = []
    
    print("Fetching CHIRPS data...")
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')

    for station_id, coords in stations.items():
        print(f"Processing {station_id}... (This will take a few minutes)")
        
        point = ee.Geometry.Point([coords['lon'], coords['lat']])
        filtered_chirps = chirps.filterDate('1986-01-01', '2015-12-31').filterBounds(point)
        
        def extract_value(image):
            val = image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=5566
            )
            return ee.Feature(None, {
                'date': image.date().format('YYYY-MM-dd'),
                'precip': val.get('precipitation')
            })
        
        time_series = filtered_chirps.map(extract_value)
        
        df = ee.data.computeFeatures({
            'expression': time_series,
            'fileFormat': 'PANDAS_DATAFRAME'
        })
        
        df = df.rename(columns={'date': 'timestamp', 'precip': 'value'})
        df['station_id'] = station_id
        df['parameter_code'] = 'P'
        df['source'] = 'CHIRPS'
        
        df = df[['timestamp', 'value', 'station_id', 'parameter_code', 'source']]
        all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        os.makedirs("data/raw", exist_ok=True)
        save_path = "data/raw/chirps_data.csv"
        final_df.to_csv(save_path, index=False)
        print(f"\nSUCCESS! Saved {len(final_df)} records to {save_path}")
    else:
        print("No data was downloaded.")

if __name__ == "__main__":
    fetch_chirps_from_gee()