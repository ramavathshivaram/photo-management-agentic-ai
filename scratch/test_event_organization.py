import requests
import sqlite3
import json
import os
import shutil

PORTRAITS = [
    ("priya_test.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\priya_portrait_1780977988171.png"),
    ("mom_test.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\mom_portrait_1780978014989.png"),
    ("dad_test.png", r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\dad_portrait_1780978029167.png")
]

def db_cleanup(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Find user ID
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        uid = row[0]
        cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
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

def main():
    username = "testeventuser"
    password = "password123"
    
    print("Cleaning up database and organized_photos directory...")
    db_cleanup(username)
    
    org_photos_dir = os.path.join(os.getcwd(), "organized_photos")
    if os.path.exists(org_photos_dir):
        try:
            shutil.rmtree(org_photos_dir)
            print("Reset organized_photos/ directory.")
        except Exception as e:
            print(f"Could not reset organized_photos/: {e}")

    # 1. Register and Login
    reg_url = "http://localhost:5000/api/auth/register"
    login_url = "http://localhost:5000/api/auth/login"
    
    r_reg = requests.post(reg_url, json={"username": username, "password": password})
    assert r_reg.status_code == 201, f"Reg failed: {r_reg.text}"
    
    r_login = requests.post(login_url, json={"username": username, "password": password})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload Portraits
    upload_url = "http://localhost:5000/api/upload"
    for filename, filepath in PORTRAITS:
        if not os.path.exists(filepath):
            print(f"Portrait not found: {filepath}")
            continue
        print(f"Uploading {filename}...")
        with open(filepath, "rb") as f:
            files = {"photos": (filename, f, "image/png")}
            r = requests.post(upload_url, headers=headers, files=files)
        assert r.status_code == 200, f"Upload failed: {r.text}"
        print(f"Uploaded {filename}. Response: {r.json()}")

    # Verify that event classification columns are filled in database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    uid = cursor.fetchone()[0]
    cursor.execute("SELECT id, original_filename, event, event_confidence, event_occasion FROM photos WHERE user_id = ?", (uid,))
    db_photos = cursor.fetchall()
    print("\nDatabase Photo Records after Upload:")
    for row in db_photos:
        print(f"Photo ID {row[0]} ({row[1]}): Event='{row[2]}' Conf={row[3]:.4f} Occasion='{row[4]}'")
        assert row[3] is not None, "Error: event_confidence is NULL!"
        assert row[4] is not None, "Error: event_occasion is NULL!"
    conn.close()

    # 3. Trigger DBSCAN clustering
    cluster_url = "http://localhost:5000/api/people/cluster-dbscan"
    print("\nTriggering clustering...")
    r_cluster = requests.post(cluster_url, headers=headers)
    assert r_cluster.status_code == 200, f"Clustering failed: {r_cluster.text}"
    print("Clustering completed:", r_cluster.json())

    # 4. Trigger Photo Organization
    org_url = "http://localhost:5000/api/organize-photos"
    print("\nTriggering photo organization...")
    r_org = requests.post(org_url, headers=headers)
    assert r_org.status_code == 200, f"Organization failed: {r_org.text}"
    org_res = r_org.json()
    print("Organization response:", org_res)
    
    # 5. Verify Nested Directories Structure
    print("\nVerifying directory structure locally...")
    # Check that folders exist under organized_photos/People/
    people_path = os.path.join(os.getcwd(), "organized_photos", "People")
    assert os.path.exists(people_path), "Error: organized_photos/People/ does not exist!"
    
    person_dirs = os.listdir(people_path)
    print("Recognized Person Directories:", person_dirs)
    assert len(person_dirs) > 0, "Error: No person directories found!"
    
    for p_dir in person_dirs:
        p_path = os.path.join(people_path, p_dir)
        occasion_dirs = os.listdir(p_path)
        print(f"Folders inside Person '{p_dir}':", occasion_dirs)
        for o_dir in occasion_dirs:
            assert o_dir in ["Occasion", "Non_Occasion"], f"Error: Unexpected occasion type folder: {o_dir}"
            o_path = os.path.join(p_path, o_dir)
            event_dirs = os.listdir(o_path)
            print(f"  Event folders inside Occasion '{o_dir}':", event_dirs)
            for e_dir in event_dirs:
                e_path = os.path.join(o_path, e_dir)
                files = os.listdir(e_path)
                print(f"    Photos inside Event '{e_dir}':", files)
                assert len(files) > 0, f"Error: Event directory '{e_dir}' is empty!"

    print("\nALL EVENT-BASED PHOTO ORGANIZATION TESTS PASSED SUCCESSFULLY!\n")
    
    # Clean up test accounts
    db_cleanup(username)

if __name__ == "__main__":
    main()
