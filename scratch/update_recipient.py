import sqlite3
import os

DB_PATH = "database.db"

def update_db():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update WhatsApp numbers for mock contacts to the user's verified number
    new_number = "+916302719741"
    cursor.execute("UPDATE people SET whatsapp_number = ?", (new_number,))
    conn.commit()
    
    print(f"Successfully updated all contact WhatsApp numbers in the database to {new_number}!")
    
    # Print updated contacts to verify
    cursor.execute("SELECT name, email, whatsapp_number FROM people")
    for row in cursor.fetchall():
        print(f"Contact: {row[0]} | Email: {row[1]} | WhatsApp: {row[2]}")
        
    conn.close()

if __name__ == "__main__":
    update_db()
