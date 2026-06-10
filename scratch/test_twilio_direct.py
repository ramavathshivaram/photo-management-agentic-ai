import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
load_dotenv()

sid = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")
url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json"

print(f"Testing direct Twilio Account credentials...")
print(f"SID: {sid}")
print(f"Token (first 6 chars): {token[:6]}...")

res = requests.get(url, auth=HTTPBasicAuth(sid, token))
print(f"\nResponse Status Code: {res.status_code}")
print("Response Body:")
print(res.text)
