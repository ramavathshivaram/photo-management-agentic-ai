import sqlite3

DB_PATH = "database.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all faces
    cursor.execute("SELECT id, photo_id, label FROM faces")
    faces = cursor.fetchall()
    
    # Get all photos
    cursor.execute("SELECT id FROM photos")
    photo_ids = set([r["id"] for r in cursor.fetchall()])
    
    orphans = []
    for f in faces:
        if f["photo_id"] not in photo_ids:
            orphans.append(dict(f))
            
    print(f"Total faces in faces table: {len(faces)}")
    print(f"Total photos in photos table: {len(photo_ids)}")
    print(f"Total orphaned faces (photo_id not in photos table): {len(orphans)}")
    if orphans:
        print("Orphaned faces sample:")
        for o in orphans[:10]:
            print(o)
            
    conn.close()

if __name__ == "__main__":
    main()
