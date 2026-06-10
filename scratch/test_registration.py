import requests
import sqlite3
import json

def cleanup_user(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    print(f"Cleaned up test user '{username}' from database.")

def main():
    reg_url = "http://localhost:5000/api/auth/register"
    login_url = "http://localhost:5000/api/auth/login"
    
    test_user = "testregisteruser"
    test_pass = "mypassword123"
    
    # Clean up first in case of dirty run
    cleanup_user(test_user)
    
    # 1. Test Registration
    print(f"Registering user '{test_user}'...")
    r_reg = requests.post(reg_url, json={"username": test_user, "password": test_pass})
    print("Registration Status:", r_reg.status_code)
    print("Registration Response:", r_reg.text)
    
    if r_reg.status_code != 201:
        print("Registration failed!")
        return
        
    # 2. Test Login with new user
    print(f"Logging in user '{test_user}'...")
    r_login = requests.post(login_url, json={"username": test_user, "password": test_pass})
    print("Login Status:", r_login.status_code)
    print("Login Response:", r_login.text)
    
    if r_login.status_code == 200:
        print("Login with newly registered user was successful!")
        token = r_login.json().get("token")
        if token:
            print("Received valid JWT token.")
            
    # Clean up test user
    cleanup_user(test_user)

if __name__ == "__main__":
    main()
