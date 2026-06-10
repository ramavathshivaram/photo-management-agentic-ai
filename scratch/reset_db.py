import sqlite3

def main():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Reset face labels
    cursor.execute("UPDATE faces SET label = 'Unknown'")
    
    # Delete auto-generated Person clusters
    cursor.execute("DELETE FROM people WHERE name LIKE 'Person_%'")
    
    # Clean up photos recognized_person fields
    cursor.execute("UPDATE photos SET recognized_person = NULL")
    
    conn.commit()
    conn.close()
    print("Database reset successful.")

if __name__ == "__main__":
    main()
