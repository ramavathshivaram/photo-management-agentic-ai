import sqlite3
import json
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

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
    cursor.execute("SELECT embedding, label FROM faces")
    rows = cursor.fetchall()
    
    embeddings = []
    for r in rows:
        try:
            emb = json.loads(r["embedding"])
            embeddings.append(normalize_embedding(emb))
        except Exception:
            continue
            
    embeddings_matrix = np.vstack(embeddings).astype(np.float32)
    n_samples = embeddings_matrix.shape[0]
    
    print(f"Total samples: {n_samples}")
    
    eps_grid = [0.30, 0.35, 0.38, 0.40, 0.42, 0.45, 0.48, 0.50, 0.55]
    for eps in eps_grid:
        db = DBSCAN(eps=eps, min_samples=1, metric='cosine')
        labels = db.fit_predict(embeddings_matrix)
        n_clusters = len(set(labels))
        
        if 1 < n_clusters < n_samples:
            try:
                score = silhouette_score(embeddings_matrix, labels, metric='cosine')
                print(f"eps={eps:.2f} | clusters={n_clusters} | Silhouette Score={score:.4f}")
            except Exception as e:
                print(f"eps={eps:.2f} | clusters={n_clusters} | Error: {e}")
        else:
            print(f"eps={eps:.2f} | clusters={n_clusters} | (Not eligible for silhouette score)")
            
    conn.close()

if __name__ == "__main__":
    main()
