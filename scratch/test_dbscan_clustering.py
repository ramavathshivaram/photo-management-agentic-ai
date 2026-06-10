import os
import requests
import json

def main():
    # 1. Login
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    print("Logging in...")
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print("Login failed!")
        return
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Upload portraits
    portraits = [
        ("priya_portrait.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\priya_portrait_1780977988171.png"),
        ("dad_portrait.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\dad_portrait_1780978029167.png"),
        ("mom_portrait.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\mom_portrait_1780978014989.png"),
        ("rahul_portrait.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\rahul_portrait_1780978002480.png"),
    ]

    upload_url = "http://localhost:5000/api/upload"
    for filename, filepath in portraits:
        if not os.path.exists(filepath):
            print(f"Portrait file not found: {filepath}")
            continue
        print(f"Uploading {filename}...")
        with open(filepath, "rb") as f:
            files = {"photos": (filename, f, "image/png")}
            r = requests.post(upload_url, headers=headers, files=files)
        print(f"Upload response: {r.status_code}")
        print(r.text)

    # 3. Trigger DBSCAN clustering
    cluster_url = "http://localhost:5000/api/people/cluster-dbscan"
    print("Triggering DBSCAN clustering...")
    r_cluster = requests.post(cluster_url, headers=headers)
    print(f"Clustering response: {r_cluster.status_code}")
    print(json.dumps(r_cluster.json(), indent=2))

    # 4. Fetch clusters list to verify grouping
    clusters_list_url = "http://localhost:5000/api/people/clusters"
    print("Fetching clusters...")
    r_clusters = requests.get(clusters_list_url, headers=headers)
    print(f"Clusters response: {r_clusters.status_code}")
    print(json.dumps(r_clusters.json(), indent=2))

if __name__ == "__main__":
    main()
