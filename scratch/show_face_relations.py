import sqlite3
import json

DB_PATH = "database.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, f.label, f.x, f.y, f.w, f.h, p.original_filename, p.id as photo_id
        FROM faces f
        JOIN photos p ON f.photo_id = p.id
        ORDER BY f.label, p.original_filename
    """)
    rows = cursor.fetchall()
    print(f"{'Face ID':<10} | {'Label':<12} | {'Photo ID':<10} | {'Filename':<30} | {'BBox':<20}")
    print("-" * 90)
    for r in rows:
        bbox = f"({r['x']},{r['y']},{r['w']},{r['h']})"
        print(f"{r['id']:<10} | {r['label']:<12} | {r['photo_id']:<10} | {r['original_filename']:<30} | {bbox:<20}")
    conn.close()

if __name__ == "__main__":
    main()
