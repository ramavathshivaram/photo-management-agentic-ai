import os
import json
import base64
import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify

JWT_SECRET = os.getenv("JWT_SECRET", "drishyamitra_jwt_super_secret_key_19283").encode('utf-8')

def base64_url_encode(data):
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def base64_url_decode(data):
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def generate_token(user_id, username, expires_in=86400):
    """Generates a secure HMAC-SHA256 signed session token (JWT equivalent)."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_in
    }
    
    header_b64 = base64_url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64_url_encode(json.dumps(payload).encode('utf-8'))
    
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET, message, hashlib.sha256).digest()
    signature_b64 = base64_url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_token(token):
    """Verifies the HMAC signature and expiration, returning the payload if valid."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        
        # Verify signature
        expected_signature = hmac.new(JWT_SECRET, message, hashlib.sha256).digest()
        expected_signature_b64 = base64_url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
            
        # Verify expiration
        payload = json.loads(base64_url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None

def login_required(f):
    """Flask decorator that enforces valid token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization token"}), 401
            
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired session token"}), 401
            
        request.user = payload
        return f(*args, **kwargs)
    return decorated
