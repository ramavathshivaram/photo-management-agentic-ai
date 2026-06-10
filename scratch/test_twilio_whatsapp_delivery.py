import requests
import json
import sys

# Force stdout to UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_twilio_whatsapp_dispatch():
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
        
    # Find a photo that has an HTTP link (from Cloudinary) or send the first one
    photo_ids = []
    for p in photos:
        if p["secure_url"].startswith("http"):
            photo_ids.append(p["id"])
            break
            
    if not photo_ids:
        # Fallback to first photo if no remote photos exist
        photo_ids = [photos[0]["id"]]
        
    # 3. Call send WhatsApp API endpoint (will route to Twilio because of .env config)
    delivery_url = "http://localhost:5000/api/delivery/whatsapp"
    payload = {
        "recipient": "6302719741",
        "photo_ids": photo_ids
    }
    
    print(f"Triggering Twilio WhatsApp dispatch of photo IDs {photo_ids} to {payload['recipient']}...")
    response = requests.post(delivery_url, headers=headers, json=payload)
    
    print(f"Response Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)

if __name__ == "__main__":
    test_twilio_whatsapp_dispatch()
