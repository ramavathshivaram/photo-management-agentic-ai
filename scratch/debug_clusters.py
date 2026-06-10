import sqlite3
import json
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN
import collections

DB_PATH = "database.db"

def normalize_embedding(emb):
    arr = np.array(emb, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, label, embedding, photo_id FROM faces")
    rows = cursor.fetchall()
    
    if not rows:
        print("No faces found!")
        return
        
    embeddings = []
    face_list = []
    for r in rows:
        try:
            emb = json.loads(r["embedding"])
            embeddings.append(normalize_embedding(emb))
            face_list.append({
                "id": r["id"],
                "label": r["label"],
                "photo_id": r["photo_id"]
            })
        except Exception as e:
            print(f"Error parsing embedding for face {r['id']}: {e}")
            
    embeddings_matrix = np.vstack(embeddings).astype(np.float32)
    n_samples = embeddings_matrix.shape[0]
    print(f"Total valid embeddings: {n_samples}")
    
    # 1. Run DBSCAN with different eps
    for eps in [0.35, 0.40, 0.45, 0.50]:
        db = DBSCAN(eps=eps, min_samples=1, metric='cosine')
        labels = db.fit_predict(embeddings_matrix)
        print(f"\nDBSCAN eps={eps}: {list(labels)}")
        clusters = collections.defaultdict(list)
        for idx, l in enumerate(labels):
            clusters[l].append(face_list[idx]["id"])
        for cl_lbl, fids in clusters.items():
            print(f"  Cluster {cl_lbl}: {fids}")
            
    # 2. Run HDBSCAN
    print("\nRunning HDBSCAN...")
    try:
        hdb = HDBSCAN(min_cluster_size=2, metric='cosine', min_samples=1)
        labels = hdb.fit_predict(embeddings_matrix)
        print(f"HDBSCAN labels: {list(labels)}")
        clusters = collections.defaultdict(list)
        for idx, l in enumerate(labels):
            clusters[l].append(face_list[idx]["id"])
        for cl_lbl, fids in clusters.items():
            print(f"  Cluster {cl_lbl}: {fids}")
    except Exception as e:
        print(f"HDBSCAN failed: {e}")
        
    conn.close()

if __name__ == "__main__":
    main()
