import pyodbc
import json
from pathlib import Path

def get_db_connection():
    # подключение к БД из config.json
    config_path = Path(__file__).resolve().parent.parent.parent / "config/config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    db = cfg["db"]
    conn_str = (
        f"DRIVER={db['driver']};"
        f"SERVER={db['server']};"
        f"DATABASE={db['database']};"
        f"UID={db['user']};"
        f"PWD={db['password']}"
    )

    return pyodbc.connect(conn_str)