import sqlite3
import os

DB_PATH = "database.db"

def check():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- LATEST DELIVERY HISTORY ---")
    cursor.execute("SELECT * FROM delivery_history ORDER BY id DESC LIMIT 5")
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\n--- PEOPLE / CONTACTS ---")
    cursor.execute("SELECT * FROM people")
    for row in cursor.fetchall():
        print(dict(row))
        
    conn.close()

if __name__ == "__main__":
    check()
