import ee
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def extract_imerg_event():
    print("Authenticating with Google Earth Engine...")
    try:
        ee.Initialize(project='weyib-thesis')
    except Exception as e:
        print(f"Error: {e}")
        return

    # 1. Define the Event Window
    start_date = '2007-09-01'
    end_date = '2007-09-30'
    
    lat, lon = 6.90, 40.83
    point = ee.Geometry.Point([lon, lat])

    print("Fetching GPM IMERG sub-daily data (This may take a minute)...")
    
    # 2. Load GPM IMERG Collection
    imerg = ee.ImageCollection('NASA/GPM_L3/IMERG_V07') \
        .filterDate(start_date, end_date) \
        .filterBounds(point) \
        .select('precipitation') # precipitation is in mm/hr

    # 3. Extract the time series
    def extract_val(img):
        val = img.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=11132
        )
        return ee.Feature(None, {
            'datetime': img.date().format('YYYY-MM-dd HH:mm:ss'),
            'precip_mm_hr': val.get('precipitation')
        })

    time_series = imerg.map(extract_val)
    
    # 4. Convert to Pandas DataFrame
    df = ee.data.computeFeatures({
        'expression': time_series,
        'fileFormat': 'PANDAS_DATAFRAME'
    })

    if df.empty:
        print("No IMERG data found for this period.")
        return

    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').set_index('datetime')
    
    # 5. Convert mm/hr to 3-Hourly Total Depth (mm)
    df['rain_depth_mm'] = df['precip_mm_hr'] * 0.5 
    df_3h = df['rain_depth_mm'].resample('3h').sum().reset_index() # '3h' not '3H'
    
    # 6. Load Observed Flow Data (Smart Column Detection)
    flow_path = "data/processed/sofumer_regression_filled.csv"
    if not os.path.exists(flow_path):
        print(f"Error: {flow_path} not found. Run the regression filler first.")
        return
        
    flow_df = pd.read_csv(flow_path, index_col=0, parse_dates=True)
    flow_df = flow_df.loc['2007-09-01':'2007-09-30']

    # --- CRITICAL FIX: Detect the correct column name ---
    possible_names = ['discharge_m3s', 'SOFUMER_FILLED', 'Q_obs', 'value']
    flow_col = None
    for name in possible_names:
        if name in flow_df.columns:
            flow_col = name
            break
            
    if flow_col is None:
        # If not found, just use the first numeric column
        flow_col = flow_df.columns[0]
        print(f"Warning: Expected column not found. Using '{flow_col}' as flow data.")
    else:
        print(f"Found flow column: '{flow_col}'")

    # 7. Plotting
    print("Generating comparison plot...")
    fig, ax1 = plt.subplots(figsize=(15, 6), dpi=150)

    # Plot Rainfall (Inverted Bar)
    ax1.bar(df_3h['datetime'], df_3h['rain_depth_mm'], color='royalblue', width=0.1, label='GPM IMERG Rainfall (3-Hrly)')
    ax1.set_ylabel('Rainfall Depth (mm / 3hr)', color='royalblue', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='royalblue')
    ax1.invert_yaxis() 
    
    # Auto-adjust y-axis limit for rainfall
    max_rain = df_3h['rain_depth_mm'].max()
    ax1.set_ylim(max_rain * 1.2, 0) 

    # Plot Streamflow on secondary axis
    ax2 = ax1.twinx()
    # Use the detected column name here!
    ax2.plot(flow_df.index, flow_df[flow_col], color='black', linewidth=2, label='Observed Sofumer Flow')
    ax2.set_ylabel('Discharge (m³/s)', color='black', fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='black')

    # Highlight the max peak
    peak_date = flow_df[flow_col].idxmax()
    peak_val = flow_df[flow_col].max()
    ax2.scatter(peak_date, peak_val, color='red', s=100, zorder=5)
    ax2.annotate(f'Max Peak: {peak_val:.2f} m³/s\nDate: {peak_date.strftime("%b %d, %Y")}',
                 xy=(peak_date, peak_val), xytext=(40, -40), textcoords='offset points',
                 bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.8),
                 arrowprops=dict(arrowstyle="->", color='black', lw=1.5),
                 fontsize=10, fontweight='bold')

    plt.title('September 2007 Flood Event: GPM IMERG Sub-Daily Rainfall vs Observed Flow', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Save plot
    os.makedirs("outputs/figures", exist_ok=True)
    plt.tight_layout()
    plt.savefig("outputs/figures/imerg_sep2007_validation.png")
    plt.close()
    
    # Save to CSV for Streamlit App
    df_3h.to_csv("data/processed/imerg_sep2007_rainfall.csv", index=False)
    print("Plot saved to outputs/figures/imerg_sep2007_validation.png")
    print("Data saved to data/processed/imerg_sep2007_rainfall.csv")

if __name__ == "__main__":
    extract_imerg_event()