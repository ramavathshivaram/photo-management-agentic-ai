import requests
import json
import sys

# Force stdout to UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_whatsapp_dispatch():
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
        
    photo_ids = [p["id"] for p in photos[:1]] # Send first photo
    
    # 3. Call send whatsapp API endpoint
    delivery_url = "http://localhost:5000/api/delivery/whatsapp"
    
    # For testing, let's try to send to a test recipient
    payload = {
        "recipient": "6302719741",
        "photo_ids": photo_ids
    }
    
    print(f"Triggering WhatsApp dispatch of photo IDs {photo_ids} to {payload['recipient']}...")
    response = requests.post(delivery_url, headers=headers, json=payload)
    
    print(f"Response Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)

if __name__ == "__main__":
    test_whatsapp_dispatch()
