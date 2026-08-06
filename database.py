import sqlite3
import json
import os
import uuid
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ro_inspection.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table for inspection logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inspection_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_code TEXT NOT NULL,
        line_code TEXT DEFAULT '',
        inspection_date TEXT NOT NULL,
        inspector TEXT NOT NULL,
        values_json TEXT NOT NULL,
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    ''')
    
    # Table for active user sessions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Session Management
def create_session(user_id: str = "1234") -> str:
    token = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO user_sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user_id, created_at))
    conn.commit()
    conn.close()
    return token

def verify_session(token: str) -> bool:
    if not token:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_sessions WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

# CRUD Functions
def create_log(building_code: str, line_code: str, inspection_date: str, inspector: str, values: dict, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    values_json = json.dumps(values, ensure_ascii=False)
    
    cursor.execute('''
    INSERT INTO inspection_logs (building_code, line_code, inspection_date, inspector, values_json, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (building_code, line_code, inspection_date, inspector, values_json, notes, created_at))
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id

def get_logs(building_code: str = None, start_date: str = None, end_date: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM inspection_logs WHERE 1=1"
    params = []
    
    if building_code:
        query += " AND building_code = ?"
        params.append(building_code)
    if start_date:
        query += " AND inspection_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND inspection_date <= ?"
        params.append(end_date)
        
    query += " ORDER BY inspection_date DESC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    logs = []
    for r in rows:
        item = dict(r)
        item["values"] = json.loads(item["values_json"])
        del item["values_json"]
        logs.append(item)
        
    conn.close()
    return logs

def get_log_by_id(log_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inspection_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        item["values"] = json.loads(item["values_json"])
        del item["values_json"]
        return item
    return None

def update_log(log_id: int, building_code: str, line_code: str, inspection_date: str, inspector: str, values: dict, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    values_json = json.dumps(values, ensure_ascii=False)
    
    cursor.execute('''
    UPDATE inspection_logs
    SET building_code = ?, line_code = ?, inspection_date = ?, inspector = ?, values_json = ?, notes = ?
    WHERE id = ?
    ''', (building_code, line_code, inspection_date, inspector, values_json, notes, log_id))
    
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_log(log_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inspection_logs WHERE id = ?", (log_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
