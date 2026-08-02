import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ro_inspection.db"))

def clear_data():
    if not os.path.exists(db_path):
        print("Database file does not exist.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM inspection_logs;")
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='inspection_logs';")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()
    print("All dummy inspection logs deleted successfully!")

if __name__ == "__main__":
    clear_data()
