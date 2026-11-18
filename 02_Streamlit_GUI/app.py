import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import differential_evolution
import datetime
import os
from sqlalchemy import create_engine, text
from dotenv import dotenv_values

# ==========================================
# 1. DATABASE CONNECTION
# ==========================================
env_path = r"D:\Thesis\SQL\.env"
if os.path.exists(env_path):
    env_vars = dotenv_values(env_path)
else:
    env_vars = dotenv_values(".env")

@st.cache_resource
def get_db_engine():
    user = env_vars.get("DB_USER", "Issam")
    password = env_vars.get("DB_PASSWORD", "")
    host = env_vars.get("DB_HOST", "localhost")
    port = env_vars.get("DB_PORT", "3306")
    dbname = env_vars.get("DB_NAME", "weyib_hydro")
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}")

def fetch_db_rain(start_date, end_date, station_id='ALL'):
    engine = get_db_engine()
    if station_id == 'ALL':
        query = f"""
            SELECT m.timestamp_utc, s.station_id, m.value 
            FROM measurement m
            JOIN station s ON m.station_id = s.station_id
            JOIN parameter p ON m.parameter_id = p.parameter_id
            WHERE p.code = 'P' AND m.source = 'EMI'
            AND m.timestamp_utc >= '{start_date}' AND m.timestamp_utc <= '{end_date} 23:59:59'
        """
        df = pd.read_sql(text(query), engine)
        if df.empty: return pd.DataFrame()
        df_pivot = df.pivot_table(index='timestamp_utc', columns='station_id', values='value')
        df_pivot['Rainfall'] = df_pivot.mean(axis=1)
        df_final = df_pivot[['Rainfall']].reset_index().rename(columns={'timestamp_utc': 'datetime'})
    else:
        query = f"""
            SELECT m.timestamp_utc as datetime, m.value as Rainfall
            FROM measurement m
            JOIN station s ON m.station_id = s.station_id
            JOIN parameter p ON m.parameter_id = p.parameter_id
            WHERE p.code = 'P' AND m.source = 'EMI' AND s.station_id = '{station_id}'
            AND m.timestamp_utc >= '{start_date}' AND m.timestamp_utc <= '{end_date} 23:59:59'
        """
        df_final = pd.read_sql(text(query), engine)
    if not df_final.empty:
        df_final['Rainfall'] = df_final['Rainfall'] / 24.0 # Convert mm/day to mm/hr for daily data
    return df_final

# ==========================================
# 2. HYDROLOGICAL MODEL & METRICS
# ==========================================
def run_model(precip_mm, area_km2, C, T_lag, Q_b, time_step_hours=1.0):
    # Convert depth over the time step to intensity (mm/hr)
    precip_rate = precip_mm / time_step_hours
    
    # Calculate raw runoff (m3/s)
    Q_in = C * precip_rate * area_km2 * (1000 / 3600)
    
    # LINEAR RESERVOIR ROUTING (Smooths the hydrograph)
    if T_lag > 0:
        K = np.exp(-time_step_hours / T_lag) 
    else:
        K = 0.0
        
    Q_routed = np.zeros_like(Q_in)
    for i in range(len(Q_in)):
        if i == 0:
            Q_routed[i] = Q_in[i]
        else:
            Q_routed[i] = Q_routed[i-1] * K + Q_in[i] * (1 - K)
            
    return Q_routed + Q_b

def calc_metrics(obs, sim):
    mask = ~np.isnan(obs) & ~np.isnan(sim)
    o = obs[mask]
    s = sim[mask]
    if len(o) == 0: return np.nan, np.nan, np.nan
    rmse = np.sqrt(np.mean((o - s)**2))
    nse = 1 - (np.sum((o - s)**2) / np.sum((o - np.mean(o))**2))
    pbias = 100 * (np.sum(o - s) / np.sum(o))
    return nse, rmse, pbias

# ==========================================
# 3. API FORECAST (Live Tab)
# ==========================================
def fetch_forecast(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation&forecast_days=3&timezone=auto"
    res = requests.get(url).json()
    times = pd.to_datetime(res['hourly']['time'])
    precip = np.array(res['hourly']['precipitation'])
    return times, precip

# ==========================================
# 4. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Flash Flood Forecaster", page_icon="🌊", layout="wide")
st.title("🌊 Flash Flood Forecasting Tool")

st.sidebar.header("Catchment Settings")
lat = st.sidebar.number_input("Latitude", value=6.98, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=40.96, format="%.4f")
area = st.sidebar.number_input("Catchment Area (km²)", value=4546.0)

st.sidebar.header("Manual Parameters (Live Tab)")
C_manual = st.sidebar.slider("Runoff Coeff (C)", 0.0, 1.0, 0.15, 0.01)
T_lag_manual = st.sidebar.slider("Lag Time (Hours)", 0.0, 48.0, 6.0, 1.0)
Q_b_manual = st.sidebar.slider("Baseflow (m³/s)", 0.0, 150.0, 20.0, 1.0)

tab1, tab2, tab3 = st.tabs([
    "🚀 Live Forecast", 
    "⚙️ Daily Calibration (MySQL)", 
    "⚡ IMERG Sub-Daily Calibration"
])

# --- TAB 1: LIVE FORECAST ---
with tab1:
    st.header("48-Hour Flash Flood Forecast")
    if st.button("Fetch Forecast & Simulate", type="primary"):
        with st.spinner("Fetching Open-Meteo data..."):
            times, precip = fetch_forecast(lat, lon)
            sim_flow = run_model(precip, area, C_manual, T_lag_manual, Q_b_manual, time_step_hours=1.0)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=times, y=precip, name="Forecast Rain (mm/hr)", marker_color='royalblue'), secondary_y=True)
            fig.add_trace(go.Scatter(x=times, y=sim_flow, name="Simulated Flow (m³/s)", line=dict(color='red', width=3)), secondary_y=False)
            fig.update_layout(title="Live Forecast Hydrograph", hovermode="x unified")
            fig.update_yaxes(title_text="Discharge (m³/s)", secondary_y=False)
            fig.update_yaxes(title_text="Rainfall (mm/hr)", autorange="reversed", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: DAILY CALIBRATION (MySQL) ---
with tab2:
    st.header("Daily Calibration using MySQL EMI Data")
    file_flow = st.file_uploader("Upload Observed Flow (datetime, Q_obs)", type="csv", key="daily_flow")
    
    if file_flow is not None:
        try:
            df_flow = pd.read_csv(file_flow)
            if 'Q-Observed' in df_flow.columns: 
                df_flow.rename(columns={'Q-Observed': 'Q_obs'}, inplace=True)
            df_flow['datetime'] = pd.to_datetime(df_flow['datetime'])
            df_flow.set_index('datetime', inplace=True)
            df_flow = df_flow.resample('1h').interpolate()
            
            st.write("### Select Calibration Window")
            min_date = df_flow.index.min().date()
            max_date = df_flow.index.max().date()
            
            col1, col2, col3 = st.columns(3)
            start_date = col1.date_input("Start Date", value=datetime.date(2006, 8, 15), min_value=min_date, max_value=max_date, key="daily_start")
            end_date = col2.date_input("End Date", value=datetime.date(2006, 8, 25), min_value=min_date, max_value=max_date, key="daily_end")
            station_choice = col3.selectbox("Rainfall Station", options=['ALL', 'AGARFA', 'DINSHO', 'ROBE', 'SINANA', 'GASERA'], key="daily_station")
            
            flow_window = df_flow.loc[str(start_date):str(end_date)]
            
            if st.button("Run Daily Calibration", type="primary"):
                with st.spinner("Optimizing..."):
                    df_rain_db = fetch_db_rain(str(start_date), str(end_date), station_choice)
                    if df_rain_db.empty:
                        st.error("No rainfall data found.")
                        st.stop()
                    
                    df_rain_db['datetime'] = pd.to_datetime(df_rain_db['datetime'])
                    df_rain_db.set_index('datetime', inplace=True)
                    df_rain_db = df_rain_db.reindex(flow_window.index, method='nearest').fillna(0)
                    
                    precip_array = df_rain_db['Rainfall'].values
                    obs_array = flow_window['Q_obs'].values
                    
                    def objective(params):
                        C, T_lag, Q_b = params
                        sim = run_model(precip_array, area, C, T_lag, Q_b, time_step_hours=1.0)
                        nse, _, _ = calc_metrics(obs_array, sim)
                        return float(-nse)
                    
                   # C (0.01-1.0), Lag (1-36 hrs), Qb (30-50 m3/s)
                    bounds = [(0.01, 1.0), (1.0, 36.0), (30.0, 50.0)]
                    result = differential_evolution(objective, bounds, seed=42)
                    best_C, best_T_lag, best_Q_b = result.x
                    
                    sim_best = run_model(precip_array, area, best_C, best_T_lag, best_Q_b, time_step_hours=1.0)
                    nse, rmse, pbias = calc_metrics(obs_array, sim_best)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("NSE", f"{nse:.3f}")
                    col2.metric("RMSE", f"{rmse:.2f}")
                    col3.metric("PBIAS", f"{pbias:.2f}%")
                    st.success(f"Optimized: C={best_C:.3f}, Lag={best_T_lag:.1f} hrs, Qb={best_Q_b:.1f}")
                    
                    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
                    fig2.add_trace(go.Bar(x=flow_window.index, y=precip_array, name="Rain", marker_color='royalblue'), secondary_y=True)
                    fig2.add_trace(go.Scatter(x=flow_window.index, y=obs_array, name="Observed", line=dict(color='black')), secondary_y=False)
                    fig2.add_trace(go.Scatter(x=flow_window.index, y=sim_best, name="Simulated", line=dict(color='red')), secondary_y=False)
                    fig2.update_layout(title="Daily Calibration", hovermode="x unified")
                    st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# --- TAB 3: IMERG SUB-DAILY CALIBRATION ---
with tab3:
    st.header("Sub-Daily Calibration using GPM IMERG")
    st.write("This uses the 3-hourly satellite data we generated for the September 2007 flood event.")
    
    file_flow_3h = st.file_uploader("Upload Observed Flow (datetime, Q_obs)", type="csv", key="imerg_flow")
    
    if file_flow_3h is not None:
        try:
            df_flow_3h = pd.read_csv(file_flow_3h)
            if 'Q-Observed' in df_flow_3h.columns: 
                df_flow_3h.rename(columns={'Q-Observed': 'Q_obs'}, inplace=True)
            df_flow_3h['datetime'] = pd.to_datetime(df_flow_3h['datetime'])
            df_flow_3h.set_index('datetime', inplace=True)
            
            # Resample to 3-hourly to match the IMERG data
            df_flow_3h = df_flow_3h.resample('3h').interpolate()
            
            # Set the fixed window for Sep 2007
            start_date = datetime.date(2007, 9, 1)
            end_date = datetime.date(2007, 9, 30)
            
            flow_window = df_flow_3h.loc[str(start_date):str(end_date)]
            
            if st.button("Run IMERG Calibration", type="primary"):
                with st.spinner("Loading IMERG data and optimizing..."):
                    
                    imerg_path = r"D:\Thesis\SQL\data\processed\imerg_sep2007_rainfall.csv"
                    
                    if not os.path.exists(imerg_path):
                        st.error(f"Error: {imerg_path} not found. Run phase7_imerg_validation.py first.")
                        st.stop()
                        
                    df_imerg = pd.read_csv(imerg_path)
                    df_imerg['datetime'] = pd.to_datetime(df_imerg['datetime'])
                    df_imerg.set_index('datetime', inplace=True)
                    
                    # Align IMERG rainfall to the 3-hourly flow data
                    df_imerg = df_imerg.reindex(flow_window.index, method='nearest').fillna(0)
                    
                    precip_array = df_imerg['rain_depth_mm'].values
                    obs_array = flow_window['Q_obs'].values
                    
                    def objective(params):
                        C, T_lag, Q_b = params
                        # CRITICAL: Time step is 3.0 hours here!
                        sim = run_model(precip_array, area, C, T_lag, Q_b, time_step_hours=3.0)
                        nse, _, _ = calc_metrics(obs_array, sim)
                        return float(-nse)
                    
                    # Increased max Lag to 96 hours (4 days) to allow for massive floodplain attenuation
                    bounds = [(0.01, 1.0), (1.0, 96.0), (30.0, 50.0)]
                    
                    result = differential_evolution(objective, bounds, seed=42)
                    best_C, best_T_lag, best_Q_b = result.x
                    
                    # CRITICAL: Time step is 3.0 hours here!
                    sim_best = run_model(precip_array, area, best_C, best_T_lag, best_Q_b, time_step_hours=3.0)
                    nse, rmse, pbias = calc_metrics(obs_array, sim_best)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("NSE", f"{nse:.3f}")
                    col2.metric("RMSE", f"{rmse:.2f}")
                    col3.metric("PBIAS", f"{pbias:.2f}%")
                    st.success(f"Optimized: C={best_C:.3f}, Lag={best_T_lag:.1f} hrs, Qb={best_Q_b:.1f}")
                    
                    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
                    fig3.add_trace(go.Bar(x=flow_window.index, y=precip_array, name="IMERG Rain (mm/3h)", marker_color='royalblue'), secondary_y=True)
                    fig3.add_trace(go.Scatter(x=flow_window.index, y=obs_array, name="Observed", line=dict(color='black')), secondary_y=False)
                    fig3.add_trace(go.Scatter(x=flow_window.index, y=sim_best, name="Simulated", line=dict(color='red')), secondary_y=False)
                    
                    fig3.update_layout(title="Sub-Daily Calibration (IMERG)", hovermode="x unified")
                    fig3.update_yaxes(title_text="Discharge (m³/s)", secondary_y=False)
                    fig3.update_yaxes(title_text="Rainfall (mm/3h)", autorange="reversed", secondary_y=True)
                    st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")