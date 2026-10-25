import pandas as pd
from sqlalchemy import text
from db import get_engine

UPSERT_SQL = """
INSERT INTO measurement (station_id, parameter_id, timestamp_utc, value, source)
VALUES (:station_id, :parameter_id, :timestamp_utc, :value, :source)
ON DUPLICATE KEY UPDATE value = VALUES(value), ingested_at = CURRENT_TIMESTAMP;
"""

SELECT_ID_SQL = """
SELECT measurement_id FROM measurement 
WHERE station_id = :station_id AND parameter_id = :parameter_id 
AND timestamp_utc = :timestamp_utc AND source = :source;
"""

INSERT_FLAG_SQL = """
INSERT INTO qc_flag (measurement_id, flag, reason) 
VALUES (:measurement_id, :flag, :reason);
"""

def load_measurements(df: pd.DataFrame, param_map: dict):
    engine = get_engine()
    
    # Optional: Print how many rows we are about to insert
    print(f"Total rows to process: {len(df)}")
    
    with engine.begin() as conn:
        for index, row in df.iterrows():
            
            # 1. Skip rows with missing dates (MySQL cannot accept empty timestamps)
            if pd.isna(row["timestamp_utc"]):
                continue
                
            # 2. Convert NaN to None (which becomes NULL in MySQL)
            val = row["value"]
            if pd.isna(val):
                val = None
                
            # 3. Insert into measurement table
            conn.execute(text(UPSERT_SQL), {
                "station_id": row["station_id"],
                "parameter_id": param_map[row["parameter_code"]],
                "timestamp_utc": row["timestamp_utc"],
                "value": val,
                "source": row["source"],
            })
            
            # 4. Get the measurement_id
            result = conn.execute(text(SELECT_ID_SQL), {
                "station_id": row["station_id"],
                "parameter_id": param_map[row["parameter_code"]],
                "timestamp_utc": row["timestamp_utc"],
                "source": row["source"],
            }).fetchone()
            
            # 5. Insert into qc_flag table
            if result:
                m_id = result[0]
                reason = row["qc_reason"]
                if pd.isna(reason):
                    reason = None
                    
                conn.execute(text(INSERT_FLAG_SQL), {
                    "measurement_id": m_id,
                    "flag": row["qc_flag"],
                    "reason": reason
                })