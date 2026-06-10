import sqlite3
import json
import numpy as np

def cosine_distance(v1, v2):
    import math
    if not v1 or not v2 or len(v1) != len(v2):
        return 1.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 1.0
    return 1.0 - (dot_product / (norm_v1 * norm_v2))

def main():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT f.id, f.label, f.embedding, p.original_filename FROM faces f JOIN photos p ON f.photo_id = p.id")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} faces in database:")
    
    faces = []
    for r in rows:
        emb = json.loads(r["embedding"])
        faces.append({
            "id": r["id"],
            "filename": r["original_filename"],
            "embedding": emb
        })
        print(f"Face ID {r['id']}: filename={r['original_filename']}")
        
    print("\nPairwise Cosine Distances:")
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            dist = cosine_distance(faces[i]["embedding"], faces[j]["embedding"])
            print(f"{faces[i]['filename']} <-> {faces[j]['filename']}: distance={dist:.4f}")

if __name__ == "__main__":
    main()
