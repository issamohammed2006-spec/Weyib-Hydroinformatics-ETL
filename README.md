# Weyib Hydroinformatics ETL Pipeline

## 📌 Project Overview
This repository contains an automated Extract, Transform, Load (ETL) pipeline and a relational MySQL database designed for hydro-climatological data analysis in the Weyib sub-basin, Ethiopia. 

The pipeline ingests multi-decadal daily data (1984–2015) for the **Alemkerem streamflow station** and four **climate stations** (Agarfa, Dinsho, Robe, and Sinana). It automatically applies Quality Control (QC) rules before loading the data into a structured MySQL database.

## 🗄️ Database Schema (CLO1)
The MySQL database consists of 6 normalized tables:
* `agency`: Data providers (MoWE, EMI).
* `station`: Station metadata (coordinates, type, catchment area).
* `parameter`: Controlled vocabulary for variables (Q, P, TMAX, TMIN).
* `measurement`: The central fact table containing ~141,000 time-series records.
* `qc_flag`: Audit trail for data quality (OK, MISSING, SUSPECT).
* `dataset_metadata`: FAIR data provenance and licensing.

## ⚙️ ETL Pipeline (CLO2 & CLO3)
The Python pipeline (`run_pipeline.py`) performs the following:
1. **Extract**: Reads raw CSV files from the `data/raw/` directory.
2. **Transform**: 
   * Converts local timestamps to UTC.
   * Melts wide climate data into a long format.
   * Applies automated QC checks (flags negative flow, missing values, and Tmin > Tmax).
3. **Load**: Inserts records into MySQL using an idempotent `UPSERT` method to prevent duplicates.

## 🚀 How to Run the Pipeline

### 1. Prerequisites
* Python 3.9+
* MySQL Server 8.0+
* Required libraries: `pip install pandas sqlalchemy pymysql python-dotenv`

### 2. Database Setup
1. Open MySQL Workbench.
2. Open the `Hylnfo proj1.sql` file in your text editor.
3. Copy the entire SQL script and run it in MySQL Workbench. This single script will automatically create the database, build all 6 tables, and insert the seed data (agencies, stations, parameters).

### 3. Environment Variables
Create a file named `.env` in the root directory (do not commit this file to GitHub):
```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=weyib_hydro
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
