import sqlite3

def check_db():
    conn = sqlite3.connect('diabetics.db')
    cursor = conn.cursor()
    
    tables = ['users', 'daily_logs', 'workout_programs', 'exercises']
    for table in tables:
        print(f"\n--- Table: {table} ---")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
            
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading {table}: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_db()
