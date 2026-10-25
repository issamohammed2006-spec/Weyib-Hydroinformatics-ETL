import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    user = os.getenv("DB_USER", "Issam")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    dbname = os.getenv("DB_NAME", "weyib_hydro")
    
    # MySQL connection string using pymysql
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}")