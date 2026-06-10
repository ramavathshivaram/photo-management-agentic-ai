import requests
import json

def main():
    # Login
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    print("Logging in...")
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print("Login failed!")
        return
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("Login successful.")

    # Trigger clustering
    cluster_url = "http://localhost:5000/api/people/cluster-dbscan"
    print("Triggering DBSCAN clustering...")
    r_cluster = requests.post(cluster_url, headers=headers, json={"algorithm": "dbscan"})
    print(f"Clustering response: {r_cluster.status_code}")
    print(json.dumps(r_cluster.json(), indent=2))

    # Fetch clusters list to verify grouping
    clusters_list_url = "http://localhost:5000/api/people/clusters"
    print("Fetching clusters...")
    r_clusters = requests.get(clusters_list_url, headers=headers)
    print(f"Clusters response: {r_clusters.status_code}")
    print(json.dumps(r_clusters.json(), indent=2))

if __name__ == "__main__":
    main()
