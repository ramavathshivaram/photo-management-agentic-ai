import requests
import sqlite3
import json
import os

PORTRAITS = {
    "priya": r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\priya_portrait_1780977988171.png",
    "mom": r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\mom_portrait_1780978014989.png"
}

def db_cleanup(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Find user ID
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        uid = row[0]
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
        # Find photo IDs
        cursor.execute("SELECT id FROM photos WHERE user_id = ?", (uid,))
        photo_ids = [r[0] for r in cursor.fetchall()]
        if photo_ids:
            placeholders = ",".join(["?"] * len(photo_ids))
            cursor.execute(f"DELETE FROM faces WHERE photo_id IN ({placeholders})", photo_ids)
            cursor.execute("DELETE FROM photos WHERE user_id = ?", (uid,))
        cursor.execute("DELETE FROM people WHERE user_id = ?", (uid,))
        cursor.execute("DELETE FROM delivery_history WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()
    print(f"Database cleaned up for user '{username}'.")

def register_user(username, password):
    reg_url = "http://localhost:5000/api/auth/register"
    r = requests.post(reg_url, json={"username": username, "password": password})
    assert r.status_code == 201, f"Failed to register {username}: {r.text}"
    print(f"Registered user '{username}' successfully.")

def login_user(username, password):
    login_url = "http://localhost:5000/api/auth/login"
    r = requests.post(login_url, json={"username": username, "password": password})
    assert r.status_code == 200, f"Failed to login {username}: {r.text}"
    token = r.json()["token"]
    print(f"Logged in user '{username}' successfully.")
    return {"Authorization": f"Bearer {token}"}

def upload_photo(headers, filename, filepath):
    upload_url = "http://localhost:5000/api/upload"
    with open(filepath, "rb") as f:
        files = {"photos": (filename, f, "image/png")}
        r = requests.post(upload_url, headers=headers, files=files)
    assert r.status_code == 200, f"Upload failed: {r.text}"
    print(f"Uploaded photo '{filename}' successfully.")
    return r.json()

def main():
    user_a = "tenant_a"
    user_b = "tenant_b"
    password = "password123"

    print("Cleaning up existing test accounts if any...")
    db_cleanup(user_a)
    db_cleanup(user_b)

    try:
        # 1. Register users
        register_user(user_a, password)
        register_user(user_b, password)

        # 2. Login as User A and User B
        headers_a = login_user(user_a, password)
        headers_b = login_user(user_b, password)

        # 3. User B should have 0 photos, metrics should be 0
        r_metrics_b = requests.get("http://localhost:5000/api/dashboard/metrics", headers=headers_b)
        assert r_metrics_b.status_code == 200
        metrics_b = r_metrics_b.json()
        assert metrics_b["total_photos"] == 0, f"Expected 0 photos for user B, got {metrics_b['total_photos']}"
        print("Verified: User B starts with 0 photos in metrics.")

        r_photos_b = requests.get("http://localhost:5000/api/photos", headers=headers_b)
        assert r_photos_b.status_code == 200
        assert len(r_photos_b.json()) == 0, f"Expected 0 photos in gallery for user B, got {len(r_photos_b.json())}"
        print("Verified: User B starts with empty photo gallery.")

        # 4. Upload photo to User A
        upload_photo(headers_a, "priya.png", PORTRAITS["priya"])

        # 5. User B should still have 0 photos
        r_metrics_b_after = requests.get("http://localhost:5000/api/dashboard/metrics", headers=headers_b)
        metrics_b_after = r_metrics_b_after.json()
        assert metrics_b_after["total_photos"] == 0, "Security Violation: User B sees User A's uploaded photo in metrics!"
        print("Verified: User B metrics remain isolated after User A uploads.")

        r_photos_b_after = requests.get("http://localhost:5000/api/photos", headers=headers_b)
        assert len(r_photos_b_after.json()) == 0, "Security Violation: User B sees User A's uploaded photo in gallery!"
        print("Verified: User B gallery remains isolated after User A uploads.")

        # 6. Upload photo to User B
        upload_photo(headers_b, "mom.png", PORTRAITS["mom"])

        # 7. Verify both have exactly 1 photo
        r_metrics_a = requests.get("http://localhost:5000/api/dashboard/metrics", headers=headers_a)
        assert r_metrics_a.json()["total_photos"] == 1
        r_metrics_b_final = requests.get("http://localhost:5000/api/dashboard/metrics", headers=headers_b)
        assert r_metrics_b_final.json()["total_photos"] == 1
        print("Verified: Both users have exactly 1 photo in their respective isolated galleries.")

        # 8. Trigger DBSCAN clustering for User B
        print("Triggering DBSCAN clustering for User B...")
        r_cluster_b = requests.post("http://localhost:5000/api/people/cluster-dbscan", headers=headers_b)
        assert r_cluster_b.status_code == 200
        print("DBSCAN clustering for User B completed.")

        # 9. Verify User B has clusters/labels and User A does not have User B's clusters
        r_clusters_b = requests.get("http://localhost:5000/api/people/clusters", headers=headers_b)
        clusters_b = r_clusters_b.json()
        print("User B Clusters:", [c["label"] for c in clusters_b])
        assert len(clusters_b) > 0, "Expected User B to have recognized clusters."

        r_clusters_a = requests.get("http://localhost:5000/api/people/clusters", headers=headers_a)
        clusters_a = r_clusters_a.json()
        print("User A Clusters:", [c["label"] for c in clusters_a])
        assert len(clusters_a) == 0, "Security Violation: User A has clusters before run, or sees User B's clusters!"

        # 10. Run DBSCAN clustering for User A
        print("Triggering DBSCAN clustering for User A...")
        r_cluster_a = requests.post("http://localhost:5000/api/people/cluster-dbscan", headers=headers_a)
        assert r_cluster_a.status_code == 200

        r_clusters_a_after = requests.get("http://localhost:5000/api/people/clusters", headers=headers_a)
        clusters_a_after = r_clusters_a_after.json()
        print("User A Clusters after clustering:", [c["label"] for c in clusters_a_after])
        assert len(clusters_a_after) > 0, "Expected User A to have recognized clusters after running clustering."

        # Verify cluster list contains only correct count (1 for each user)
        # Verify that their labels are distinct/isolated
        # Let's ensure User B can't merge or split User A's clusters
        label_a = clusters_a_after[0]["label"]
        label_b = clusters_b[0]["label"]

        # Get User A's face ID and check face labeling auth
        r_photos_a = requests.get("http://localhost:5000/api/photos", headers=headers_a)
        photos_a = r_photos_a.json()
        face_id_a = photos_a[0]["faces"][0]["id"]

        print(f"Testing unauthorized labeling: User B trying to label User A's face (ID {face_id_a}) (Should Fail with 403)...")
        r_unauth_label = requests.post(f"http://localhost:5000/api/faces/{face_id_a}/label", headers=headers_b, json={
            "label": "Priya_Sharma"
        })
        assert r_unauth_label.status_code == 403, f"Expected 403, got {r_unauth_label.status_code}"
        print("Verified: User B cannot label User A's face.")

        print(f"Labeling User A's face (ID {face_id_a}) to 'Priya_Sharma' as User A...")
        r_label_a = requests.post(f"http://localhost:5000/api/faces/{face_id_a}/label", headers=headers_a, json={
            "label": "Priya_Sharma"
        })
        assert r_label_a.status_code == 200
        print("Verified: User A successfully labeled their own face.")

        print(f"Testing merge operation: Attempting to merge User A's cluster 'Priya_Sharma' as User B (Should Fail)...")
        r_merge = requests.post("http://localhost:5000/api/people/merge-clusters", headers=headers_b, json={
            "src_label": "Priya_Sharma",
            "dest_label": label_b
        })
        # Should return 404 since src_label 'Priya_Sharma' does not exist in User B's faces
        assert r_merge.status_code == 404, f"Security Violation: User B was able to perform merge/access User A's cluster: {r_merge.status_code} {r_merge.text}"
        print("Verified: User B cannot merge User A's cluster (failed with 404).")

        print("Testing merge operation: Attempting to merge same cluster 'Priya_Sharma' into itself as User A (Should Fail)...")
        r_merge_self = requests.post("http://localhost:5000/api/people/merge-clusters", headers=headers_a, json={
            "src_label": "Priya_Sharma",
            "dest_label": "Priya_Sharma"
        })
        assert r_merge_self.status_code == 400, f"Expected 400, got {r_merge_self.status_code}"
        print("Verified: User A cannot merge 'Priya_Sharma' into itself.")

        print("Testing manual organize: organizing photos for User A...")
        r_org_a = requests.post("http://localhost:5000/api/organize-photos", headers=headers_a)
        assert r_org_a.status_code == 200
        org_a_res = r_org_a.json()
        print("Organize A result:", org_a_res)
        # Should only copy User A's photo
        # Verify copied_count is 2 (1 to Events/General, 1 to People/Person_X)
        assert org_a_res["copied_count"] == 2, f"Expected 2 copies, got {org_a_res['copied_count']}"

        print("Testing manual organize: organizing photos for User B...")
        r_org_b = requests.post("http://localhost:5000/api/organize-photos", headers=headers_b)
        assert r_org_b.status_code == 200
        org_b_res = r_org_b.json()
        print("Organize B result:", org_b_res)
        assert org_b_res["copied_count"] == 2, f"Expected 2 copies, got {org_b_res['copied_count']}"

        print("\nALL MULTI-TENANT ISOLATION TESTS PASSED SUCCESSFULLY!\n")

    finally:
        print("Cleaning up test accounts...")
        db_cleanup(user_a)
        db_cleanup(user_b)

if __name__ == "__main__":
    main()
