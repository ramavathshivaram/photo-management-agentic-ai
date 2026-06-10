import requests
import json
import sys

# Force stdout to UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_brevo_dispatch():
    # 1. Login
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    res = requests.post(login_url, json=login_data)
    token = res.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get photos to retrieve photo IDs
    photos_url = "http://localhost:5000/api/photos"
    photos_res = requests.get(photos_url, headers=headers)
    photos = photos_res.json()
    
    if not photos:
        print("No photos found in database to deliver!")
        return
        
    photo_ids = [p["id"] for p in photos[:2]] # Send first 2 photos
    
    # 3. Call send email API endpoint
    delivery_url = "http://localhost:5000/api/delivery/email"
    payload = {
        "recipient": "saolarkk@gmail.com",
        "photo_ids": photo_ids
    }
    
    print(f"Triggering Brevo dispatch of photo IDs {photo_ids} to saolarkk@gmail.com...")
    response = requests.post(delivery_url, headers=headers, json=payload)
    
    print(f"Response Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_brevo_dispatch()
