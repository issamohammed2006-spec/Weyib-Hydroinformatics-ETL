# Weyib Sub-Basin Hydroinformatics Framework (HENG632Y)

This repository contains a fully integrated, end-to-end Hydroinformatics framework developed for the Weyib sub-basin, Ethiopia. It spans three core projects: relational data engineering, web-based operational forecasting, and automated hydrological-hydraulic modeling.

## 📂 Repository Structure

### Project 1: Data Model & Automation (`01_Database_and_ETL`)
*   **MySQL Database:** A 6-table normalized schema (`agency`, `station`, `parameter`, `measurement`, `qc_flag`, `dataset_metadata`) storing over 235,000 records.
*   **ETL Pipeline:** Python scripts that automatically fetch CHIRPS satellite data via Google Earth Engine, process EMI/MoWE ground data, perform gap-filling (Regional Regression), apply Quality Control, and load the data into MySQL.

### Project 2: Web Service & Dashboard (`02_Streamlit_GUI`)
*   **Flash Flood Forecaster GUI:** A Streamlit application that pulls live rainfall forecasts from the Open-Meteo API and simulates real-time river discharge.
*   **Automated Calibration:** Uses `scipy.optimize` to calibrate a 3-parameter conceptual rainfall-runoff model.
*   **GPM IMERG Integration:** Integrates 3-hourly NASA GPM IMERG satellite data for sub-daily flood event analysis (e.g., September 2007 event).

### Project 3: Integrated Modeling (`03_Integrated_Modeling`)
*   **HEC-HMS (Hydrology):** A 5-subbasin semi-distributed model calibrated to a 100-Year design storm (Peak: 2726.5 m³/s).
*   **HEC-RAS (Hydraulics):** Automated 2D flood routing to generate the 100-Year Flood Hazard Map.
*   **Sentinel-1 Validation:** Automated Google Earth Engine scripts to extract SAR flood extents and compare them against the model using Confusion Matrices (F1-Score, Kappa).
*   **Automation Scripts:** Python scripts (`rivia`, `win32com`) to run HMS and RAS programmatically.

## 🚀 How to Run the Pipeline

1. **Prerequisites:** Python 3.10+, MySQL 8.0+, HEC-HMS 4.13, HEC-RAS 6.5.
2. **Database Setup:** Run the SQL script in `01_Database_and_ETL` to build the schema.
3. **Environment Variables:** Create a `.env` file in the root directory (refer to `.env.example`).
4. **Data Ingestion:** Run `python 01_Database_and_ETL/run_pipeline.py` to populate the database.
5. **GUI Tool:** Navigate to `02_Streamlit_GUI/` and run `streamlit run app.py`.
6. **Modeling Automation:** Navigate to `03_Integrated_Modeling/` and run the respective Phase scripts.

## ⚠️ Data Availability
To comply with GitHub file size limits, large datasets (`.tif`, `.hdf`, `.csv`) are not stored in this repository. The Python scripts provided automatically fetch and generate these datasets via Google Earth Engine and MySQL APIs.
