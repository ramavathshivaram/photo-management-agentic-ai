import requests
import json
import sys

# Force stdout to UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_chat_session():
    # 1. Login
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    print("Logging in...")
    res = requests.post(login_url, json=login_data)
    token = res.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    agent_url = "http://localhost:5000/api/agent"
    
    # Step 1: Search
    print("\n[Step 1] Sending search query...")
    r1 = requests.post(agent_url, headers=headers, json={"query": "find rahul images"})
    print("Reply:", r1.json().get("reply"))
    print("State:", r1.json().get("state"))
    
    # Step 2: Choose Email (1)
    print("\n[Step 2] Selecting Email method...")
    r2 = requests.post(agent_url, headers=headers, json={"query": "1"})
    print("Reply:", r2.json().get("reply"))
    print("State:", r2.json().get("state"))
    
    # Step 3: Check Contact Confirmation or Recipient Entry
    state = r2.json().get("state")
    if state == "AWAITING_CONTACT_CONFIRMATION":
        # Say 'yes' to use the saved contact
        print("\n[Step 3] Accepting saved contact...")
        r3 = requests.post(agent_url, headers=headers, json={"query": "yes"})
    else:
        # Enter an email address
        print("\n[Step 3] Entering recipient email...")
        r3 = requests.post(agent_url, headers=headers, json={"query": "recipient@example.com"})
    print("Reply:", r3.json().get("reply"))
    print("State:", r3.json().get("state"))
    
    # Step 4: Approve Transaction
    print("\n[Step 4] Approving delivery transaction...")
    r4 = requests.post(agent_url, headers=headers, json={"query": "yes"})
    print("Reply:", r4.json().get("reply"))
    print("State:", r4.json().get("state"))
    print("Logs:")
    print("\n".join([f"> {log}" for log in r4.json().get("logs", [])]))

if __name__ == "__main__":
    run_chat_session()
