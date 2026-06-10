import sqlite3
import json

DB_PATH = "database.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, photo_id, label, x, y, w, h FROM faces")
    rows = cursor.fetchall()
    print(f"Total faces in DB: {len(rows)}")
    labels = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    print("Face counts per label:")
    for l, count in labels.items():
        print(f"  {l}: {count}")
    conn.close()

if __name__ == "__main__":
    main()
