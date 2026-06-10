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

    # Call agent chat endpoint for Person_1
    print("Testing chatbot for 'Person_1'...")
    res = requests.post("http://localhost:5000/api/agent", headers=headers, json={"query": "send Person_1's photos"})
    print("Response status:", res.status_code)
    data = res.json()
    print("Agent reply:", data.get("reply"))
    print("Found photos count:", len(data.get("photos", [])))
    print("Photos list:")
    for p in data.get("photos", []):
        print(f"  ID: {p['id']}, Filename: {p['original_filename']}")

if __name__ == "__main__":
    main()
