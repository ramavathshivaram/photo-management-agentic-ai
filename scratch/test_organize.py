import requests
import json
import os

url_login = "http://localhost:5000/api/auth/login"
url_organize = "http://localhost:5000/api/organize-photos"

# 1. Login to get token
payload = {"username": "admin", "password": "admin123"}
r_login = requests.post(url_login, json=payload)
if r_login.status_code != 200:
    print(f"Login failed: {r_login.text}")
    exit(1)

token = r_login.json()["token"]
print(f"Login successful, token retrieved: {token[:20]}...")

# 2. Call Organize Photos API
headers = {"Authorization": f"Bearer {token}"}
r_org = requests.post(url_organize, headers=headers)
print(f"Organize endpoint status: {r_org.status_code}")
print(json.dumps(r_org.json(), indent=2))

# 3. Check organized_photos folder on disk
base_dir = os.path.join(os.getcwd(), "organized_photos")
if os.path.exists(base_dir):
    print("\nLocal folder 'organized_photos/' exists. Directory structure:")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")
else:
    print("Local folder 'organized_photos/' does not exist.")
