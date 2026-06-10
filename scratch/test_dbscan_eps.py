import sqlite3
import json
import numpy as np
from sklearn.cluster import DBSCAN

def normalize_embedding(emb):
    arr = np.array(emb, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr

def main():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT f.id, f.label, f.embedding, p.original_filename FROM faces f JOIN photos p ON f.photo_id = p.id")
    rows = cursor.fetchall()
    
    embeddings = []
    names = []
    for r in rows:
        emb = json.loads(r["embedding"])
        embeddings.append(normalize_embedding(emb))
        names.append(r["original_filename"])
        
    embeddings_matrix = np.vstack(embeddings).astype(np.float32)
    
    for eps in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.68]:
        dbscan = DBSCAN(eps=eps, min_samples=1, metric='cosine')
        labels = dbscan.fit_predict(embeddings_matrix)
        print(f"eps={eps:.2f}: clusters={labels} -> {dict(zip(names, labels))}")

if __name__ == "__main__":
    main()
