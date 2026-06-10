import requests
import json

def test_chat_search():
    # 1. Login
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    print("Attempting to login...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed! Status code: {response.status_code}")
        return
        
    token = response.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Query chatbot for Rahul images
    agent_url = "http://localhost:5000/api/agent"
    chat_payload = {"query": "find rahul images"}
    print("Sending chatbot query: 'find rahul images'...")
    agent_response = requests.post(agent_url, headers=headers, json=chat_payload)
    
    print(f"Agent response status code: {agent_response.status_code}")
    print("Agent reply:")
    print(json.dumps(agent_response.json(), indent=2))

if __name__ == "__main__":
    test_chat_search()
