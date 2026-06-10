import os
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv
load_dotenv()

def test_media_delivery():
    wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    recipient = "916302719741"
    
    # Let's try two photos: Rahul.jpg (42KB, small, no spaces) and the screenshot (1.19MB, large, has spaces)
    photos = [
        {"path": "static/uploads/1780985742_Rahul.jpg", "name": "Rahul.jpg", "mime": "image/jpeg"},
        {"path": "static/uploads/1780985828_ChatGPT Image May 8, 2026, 08_15_38 PM.png", "name": "ChatGPT_Image.png", "mime": "image/png"}
    ]
    
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "Content-Type": "application/json"
    }
    
    for photo in photos:
        print(f"\n--- Testing Photo: {photo['name']} ---")
        if not os.path.exists(photo["path"]):
            print(f"File {photo['path']} not found!")
            continue
            
        with open(photo["path"], "rb") as f:
            file_bytes = f.read()
            
        # 1. Upload to Meta media endpoint
        upload_url = f"https://graph.facebook.com/v25.0/{wa_phone_id}/media"
        files = {
            "file": (photo["name"], file_bytes, photo["mime"]),
            "messaging_product": (None, "whatsapp")
        }
        media_headers = {
            "Authorization": f"Bearer {wa_token}"
        }
        
        print(f"Uploading {photo['name']} ({len(file_bytes)} bytes) to Meta...")
        upload_res = requests.post(upload_url, headers=media_headers, files=files, timeout=20, verify=False)
        print(f"Upload Status Code: {upload_res.status_code}")
        print("Upload Response:")
        print(upload_res.text)
        
        if upload_res.status_code not in [200, 201]:
            print("Upload failed, skipping send.")
            continue
            
        media_id = upload_res.json().get("id")
        
        # 2. Send media message using media ID
        send_url = f"https://graph.facebook.com/v25.0/{wa_phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "image",
            "image": {
                "id": media_id
            }
        }
        
        print(f"Sending media message (ID: {media_id}) to {recipient}...")
        send_res = requests.post(send_url, headers=headers, json=payload, timeout=20, verify=False)
        print(f"Send Message Status Code: {send_res.status_code}")
        print("Send Message Response:")
        print(send_res.text)

if __name__ == "__main__":
    test_media_delivery()
