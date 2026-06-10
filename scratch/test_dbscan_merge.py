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

    # 2. Upload duplicate Priya portrait
    filepath = r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\priya_portrait_1780977988171.png"
    print("Uploading duplicate priya portrait...")
    with open(filepath, "rb") as f:
        files = {"photos": ("priya_portrait_copy.png", f, "image/png")}
        r = requests.post("http://localhost:5000/api/upload", headers=headers, files=files)
    print(f"Upload response: {r.status_code}")
    print(r.text)

    # 3. Trigger DBSCAN clustering
    print("Triggering DBSCAN clustering...")
    r_cluster = requests.post("http://localhost:5000/api/people/cluster-dbscan", headers=headers)
    print(f"Clustering response: {r_cluster.status_code}")
    print(json.dumps(r_cluster.json(), indent=2))

    # 4. Fetch clusters list to verify grouping
    print("Fetching clusters...")
    r_clusters = requests.get("http://localhost:5000/api/people/clusters", headers=headers)
    print(f"Clusters response: {r_clusters.status_code}")
    print(json.dumps(r_clusters.json(), indent=2))

if __name__ == "__main__":
    main()
