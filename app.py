import sys
import os
import time
import json
import re
import urllib.request
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

# Force stdout/stderr to UTF-8 on Windows to prevent UnicodeEncodeErrors with emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask_cors import CORS
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

import cloudinary
import cloudinary.uploader
from deepface import DeepFace
import cv2
from PIL import Image
import scrfd

# Import local auth and database helpers
import database
from auth import login_required, generate_token, verify_token
import werkzeug.security

app = Flask(__name__, static_folder="static")
CORS(app)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "IMAGE"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "553597411633342"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Pre-load DeepFace ArcFace model to prevent watchdog reloader from triggering on first request
try:
    print("Pre-loading DeepFace ArcFace model...")
    DeepFace.build_model("ArcFace")
    print("DeepFace ArcFace model pre-loaded successfully.")
except Exception as startup_err:
    safe_err = str(startup_err).encode('ascii', errors='replace').decode('ascii')
    print(f"DeepFace model pre-loading failed: {safe_err}")

# SCRFD Detector Configuration and Download
SCRFD_MODEL_PATH = os.path.join("assets", "models", "scrfd_2.5g_bnkps.onnx")
SCRFD_MODEL_URL = "https://huggingface.co/RuteNL/SCRFD-face-detection-ONNX/resolve/main/2.5g_bnkps.onnx"

def ensure_scrfd_model():
    if not os.path.exists(SCRFD_MODEL_PATH):
        print(f"SCRFD model not found. Downloading from {SCRFD_MODEL_URL}...")
        os.makedirs(os.path.dirname(SCRFD_MODEL_PATH), exist_ok=True)
        try:
            urllib.request.urlretrieve(SCRFD_MODEL_URL, SCRFD_MODEL_PATH)
            print(f"SCRFD model downloaded to {SCRFD_MODEL_PATH}")
        except Exception as e:
            print(f"Failed to download SCRFD model: {e}")
            raise e

# Initialize detector
scrfd_detector = None
try:
    ensure_scrfd_model()
    print("Initializing SCRFD model...")
    scrfd_detector = scrfd.SCRFD.from_path(SCRFD_MODEL_PATH)
    print("SCRFD model initialized successfully.")
except Exception as scrfd_err:
    print(f"SCRFD model initialization failed: {scrfd_err}")

def detect_and_represent(img_path, enforce_detection=False):
    if scrfd_detector is None:
        raise Exception("SCRFD detector is not initialized.")
        
    img_cv = cv2.imread(img_path)
    if img_cv is None:
        raise Exception(f"Failed to read image at {img_path}")
        
    h_img, w_img, _ = img_cv.shape
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    
    faces = scrfd_detector.detect(img_pil)
    
    if not faces and enforce_detection:
        raise Exception("No face detected in the image.")
        
    representations = []
    for face in faces:
        # 1. Reject low-quality face detections (confidence threshold)
        if face.probability < 0.55:
            print(f"Rejected low-quality face with probability {face.probability:.4f}")
            continue
            
        # 2. Align face using 5 keypoints for side poses/tilts
        kps = face.keypoints
        if kps:
            try:
                reference_5pts = np.array([
                    [30.2946, 51.6963], # left eye
                    [65.5318, 51.5014], # right eye
                    [48.0252, 71.7366], # nose
                    [33.5493, 92.3655], # left mouth corner
                    [62.7299, 92.2041]  # right mouth corner
                ], dtype=np.float32)
                
                src_pts = np.array([
                    [kps.left_eye.x, kps.left_eye.y],
                    [kps.right_eye.x, kps.right_eye.y],
                    [kps.nose.x, kps.nose.y],
                    [kps.left_mouth.x, kps.left_mouth.y],
                    [kps.right_mouth.x, kps.right_mouth.y]
                ], dtype=np.float32)
                
                M, inliers = cv2.estimateAffinePartial2D(src_pts, reference_5pts)
                if M is not None:
                    processed_face = cv2.warpAffine(img_cv, M, (112, 112))
                else:
                    bbox = face.bbox
                    x1 = max(0, int(bbox.upper_left.x))
                    y1 = max(0, int(bbox.upper_left.y))
                    x2 = min(w_img, int(bbox.lower_right.x))
                    y2 = min(h_img, int(bbox.lower_right.y))
                    processed_face = img_cv[y1:y2, x1:x2]
            except Exception as align_err:
                print(f"Alignment failed: {align_err}, falling back to raw crop")
                bbox = face.bbox
                x1 = max(0, int(bbox.upper_left.x))
                y1 = max(0, int(bbox.upper_left.y))
                x2 = min(w_img, int(bbox.lower_right.x))
                y2 = min(h_img, int(bbox.lower_right.y))
                processed_face = img_cv[y1:y2, x1:x2]
        else:
            bbox = face.bbox
            x1 = max(0, int(bbox.upper_left.x))
            y1 = max(0, int(bbox.upper_left.y))
            x2 = min(w_img, int(bbox.lower_right.x))
            y2 = min(h_img, int(bbox.lower_right.y))
            processed_face = img_cv[y1:y2, x1:x2]
            
        if processed_face.size == 0:
            continue
            
        bbox = face.bbox
        x1 = max(0, int(bbox.upper_left.x))
        y1 = max(0, int(bbox.upper_left.y))
        x2 = min(w_img, int(bbox.lower_right.x))
        y2 = min(h_img, int(bbox.lower_right.y))
            
        try:
            reps = DeepFace.represent(
                img_path=processed_face,
                model_name="ArcFace",
                detector_backend="skip"
            )
            if reps:
                emb = reps[0]["embedding"]
                representations.append({
                    "facial_area": {
                        "x": x1,
                        "y": y1,
                        "w": x2 - x1,
                        "h": y2 - y1
                    },
                    "embedding": emb
                })
        except Exception as e:
            print(f"Failed to extract ArcFace embedding: {e}")
            
    return representations

# FAISS and Numpy tools for storing/searching embeddings
import numpy as np
import faiss

# Cosine Similarity Threshold Configuration (between 0.4 and 0.6 as requested)
COSINE_SIM_THRESHOLD = float(os.getenv("COSINE_SIMILARITY_THRESHOLD", "0.50"))
COSINE_DIST_THRESHOLD = 1.0 - COSINE_SIM_THRESHOLD


def normalize_embedding(emb):
    arr = np.array(emb, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr

def calculate_face_confidences(faces_list):
    # Group faces by label
    by_label = {}
    for face in faces_list:
        lbl = face["label"]
        if lbl != "Unknown":
            if lbl not in by_label:
                by_label[lbl] = []
            by_label[lbl].append(face)
            
    # Compute centroids
    centroids = {}
    for lbl, group in by_label.items():
        embs = []
        for f in group:
            if "embedding" in f and f["embedding"]:
                try:
                    emb_val = f["embedding"]
                    if isinstance(emb_val, str):
                        emb_val = json.loads(emb_val)
                    embs.append(normalize_embedding(emb_val))
                except Exception:
                    continue
        if embs:
            mean_emb = np.mean(embs, axis=0)
            centroids[lbl] = normalize_embedding(mean_emb)
            
    # Calculate confidence for each face
    for face in faces_list:
        lbl = face["label"]
        if lbl == "Unknown" or lbl not in centroids:
            face["confidence"] = 1.0  # Single/unknown face defaults to 1.0
        else:
            try:
                emb_val = face["embedding"]
                if isinstance(emb_val, str):
                    emb_val = json.loads(emb_val)
                emb = normalize_embedding(emb_val)
                sim = float(np.dot(emb, centroids[lbl]))
                face["confidence"] = round(max(0.0, min(1.0, sim)), 3)
            except Exception:
                face["confidence"] = 1.0

def match_face_faiss(emb, known_profiles, threshold=COSINE_SIM_THRESHOLD):
    if not known_profiles:
        return "Unknown"
    try:
        embeddings = [normalize_embedding(p["embedding"]) for p in known_profiles]
        embeddings_matrix = np.vstack(embeddings).astype(np.float32)
        
        # ArcFace output vectors are 512 dimensions
        index = faiss.IndexFlatIP(512)
        index.add(embeddings_matrix)
        
        query_vector = normalize_embedding(emb).reshape(1, -1)
        distances, indices = index.search(query_vector, 1)
        
        best_similarity = distances[0][0]
        best_index = indices[0][0]
        
        # For ArcFace, inner product >= 0.32 matches
        if best_index != -1 and best_similarity >= threshold:
            return known_profiles[best_index]["label"]
    except Exception as e:
         print(f"FAISS search match failed: {e}")
    return "Unknown"


# Active chat sessions in memory
AGENT_SESSIONS = {}

def get_db():
    conn = sqlite3.connect(database.DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# CLIP model lazy initialization helpers
_clip_model = None
_clip_processor = None

def get_clip_model_and_processor():
    global _clip_model, _clip_processor
    if _clip_model is None:
        try:
            from transformers import CLIPProcessor, CLIPModel
            model_name = "openai/clip-vit-base-patch32"
            print("Initializing CLIP model...")
            _clip_model = CLIPModel.from_pretrained(model_name)
            _clip_processor = CLIPProcessor.from_pretrained(model_name)
            print("CLIP model initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize CLIP model: {e}")
            raise e
    return _clip_model, _clip_processor

def classify_photo_event_with_gemini(img_path, categories):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Defaulting to Casual.")
        return "Casual", 1.0
        
    try:
        from PIL import Image
        from google import genai
        from google.genai import types
        import io
        
        image = Image.open(img_path).convert("RGB")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Analyze this image and classify it into exactly one of the following event categories:
        {", ".join(categories)}
        
        You must consider background context, clothing, decorations, flowers, stage setup, and background objects.
        Reply in JSON format matching this schema:
        {{
            "event": "category_name",
            "confidence": 0.0 to 1.0
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        res_data = json.loads(response.text.strip())
        event_name = res_data.get("event", "Casual")
        confidence = float(res_data.get("confidence", 1.0))
        
        if event_name not in categories:
            event_name = "Casual"
            
        print(f"Gemini classified {img_path} as {event_name} (conf={confidence:.4f})")
        return event_name, confidence
    except Exception as gemini_err:
        print(f"Gemini classification failed: {gemini_err}")
        return "Casual", 1.0

def classify_photo_event(img_path, num_faces=None):
    """
    Classifies the photo at img_path into event categories.
    Returns: (event_name, confidence_score, occasion_type)
    """
    categories = [
        "Wedding", "Birthday", "Engagement", "Reception", "Graduation",
        "Festival", "Religious Event", "Office Event", "Travel", "Casual",
        "Family Photo", "Family Gathering"
    ]
    occasion_categories = {
        "Wedding", "Birthday", "Engagement", "Reception", "Graduation",
        "Festival", "Religious Event", "Office Event", "Family Gathering"
    }
    
    # 1. Try local CLIP model first
    try:
        from PIL import Image
        import torch
        model, processor = get_clip_model_and_processor()
        image = Image.open(img_path).convert("RGB")
        prompts = [f"a photo of a {c}" for c in categories]
        
        inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)[0].tolist()
            
        best_idx = probs.index(max(probs))
        event_name = categories[best_idx]
        confidence = probs[best_idx]
        
        print(f"CLIP classified {img_path} as {event_name} (conf={confidence:.4f})")
    except Exception as clip_err:
        print(f"CLIP classification failed: {clip_err}. Falling back to Gemini...")
        # 2. Fallback to Gemini
        event_name, confidence = classify_photo_event_with_gemini(img_path, categories)
        
    # Heuristic override for Family Photos/Gatherings based on face count
    if num_faces is not None and num_faces >= 2:
        # If the image was classified as a generic category (Casual, Travel) or other confidence is low
        if event_name in ["Casual", "Travel"] or confidence < 0.75:
            if num_faces >= 4:
                event_name = "Family Gathering"
                confidence = 0.90
            else:
                event_name = "Family Photo"
                confidence = 0.90
            print(f"Face count heuristic: override event classification to {event_name} due to {num_faces} detected faces.")

    # Apply occasion thresholds
    if confidence > 0.80 and event_name in occasion_categories:
        occasion_type = "Occasion"
    else:
        occasion_type = "Non_Occasion"
        
    return event_name, confidence, occasion_type

# Event auto-classification keyword mapper
def classify_event(filename):
    fn_lower = filename.lower()
    if any(k in fn_lower for k in ["wedding", "marriage", "shaadi", "reception", "bride", "groom", "ring"]):
        return "Wedding"
    elif any(k in fn_lower for k in ["tour", "trip", "travel", "vacation", "manali", "trek", "beach", "lake", "mountain"]):
        return "Tour/Trip"
    elif any(k in fn_lower for k in ["birthday", "bday", "cake", "candles", "celebration"]):
        return "Birthday"
    elif any(k in fn_lower for k in ["diwali", "festival", "holi", "eid", "christmas", "puja", "diya"]):
        return "Festival"
    elif any(k in fn_lower for k in ["family", "gathering", "parents", "group_photo", "siblings", "relatives"]):
        return "Family Photo"
    elif any(k in fn_lower for k in ["party", "gathering", "dinner", "event", "celebration", "hackathon"]):
        return "Event"
    return "General"

# One-time migration function for event column mapping
def migrate_existing_photo_events():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, original_filename, event FROM photos")
        rows = cursor.fetchall()
        updated = 0
        for row in rows:
            photo_id = row["id"]
            filename = row["original_filename"]
            current_event = row["event"]
            if not current_event or current_event == 'General':
                new_event = classify_event(filename)
                if new_event != 'General':
                    cursor.execute("UPDATE photos SET event = ? WHERE id = ?", (new_event, photo_id))
                    updated += 1
        if updated > 0:
            conn.commit()
            print(f"Completed auto-event migration for {updated} existing photos.")
    except Exception as e:
        print(f"Error migrating events: {e}")
    finally:
        conn.close()

def backfill_event_classification():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, secure_url, original_filename FROM photos WHERE event_confidence IS NULL")
        rows = cursor.fetchall()
        if rows:
            print(f"Startup: Found {len(rows)} photos requiring event classification. Classifying...")
            for r in rows:
                photo_id = r["id"]
                secure_url = r["secure_url"]
                original_filename = r["original_filename"]
                
                temp_path = None
                if secure_url.startswith("/static/"):
                    local_path = secure_url.lstrip("/")
                    if os.path.exists(local_path):
                        temp_path = local_path
                else:
                    import requests
                    try:
                        os.makedirs("temp", exist_ok=True)
                        temp_path = os.path.join("temp", f"backfill_{photo_id}_{original_filename}")
                        res = requests.get(secure_url, timeout=15, verify=False)
                        if res.status_code == 200:
                            with open(temp_path, "wb") as f:
                                f.write(res.content)
                        else:
                            temp_path = None
                    except Exception as download_err:
                        print(f"Download failed for backfill photo {photo_id}: {download_err}")
                        temp_path = None
                
                if temp_path and os.path.exists(temp_path):
                    try:
                        cursor.execute("SELECT COUNT(*) FROM faces WHERE photo_id = ?", (photo_id,))
                        num_faces = cursor.fetchone()[0]
                        event_name, confidence, occasion_type = classify_photo_event(temp_path, num_faces=num_faces)
                        cursor.execute("""
                            UPDATE photos
                            SET event = ?, event_confidence = ?, event_occasion = ?
                            WHERE id = ?
                        """, (event_name, confidence, occasion_type, photo_id))
                        print(f"Backfill: Classified photo ID {photo_id} as {event_name} ({occasion_type}, conf={confidence:.4f})")
                    except Exception as err:
                        print(f"Failed to classify photo ID {photo_id} during backfill: {err}")
                    finally:
                        if not secure_url.startswith("/static/") and os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
            conn.commit()
    except Exception as e:
        print(f"Startup event classification backfill failed: {e}")
    finally:
        conn.close()

# Run migration and backfill at startup
try:
    migrate_existing_photo_events()
    backfill_event_classification()
except Exception as e:
    print(f"Startup event migration/backfill failed: {e}")


# Helper to calculate cosine distance between two embedding vectors
def cosine_distance(v1, v2):
    import math
    if not v1 or not v2 or len(v1) != len(v2):
        return 1.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 1.0
    return 1.0 - (dot_product / (norm_v1 * norm_v2))

# Auto-labels any matching unknown faces in the database using similarity distance
def propagate_labels(person_name, reference_embedding, user_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Select all Unknown faces belonging to this user's photos
        cursor.execute("""
            SELECT f.id, f.embedding 
            FROM faces f 
            JOIN photos p ON f.photo_id = p.id 
            WHERE p.user_id = ? AND f.label = 'Unknown'
        """, (user_id,))
        unknown_faces = cursor.fetchall()
        
        updated_count = 0
        for face in unknown_faces:
            face_id = face["id"]
            try:
                emb = json.loads(face["embedding"])
                dist = cosine_distance(reference_embedding, emb)
                if dist <= COSINE_DIST_THRESHOLD:  # Threshold for similarity matching
                    cursor.execute("UPDATE faces SET label = ? WHERE id = ?", (person_name, face_id))
                    updated_count += 1
            except Exception:
                continue
                
        conn.commit()
        return updated_count
    finally:
        conn.close()

# Serve Frontend static assets
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# ----------------- AUTH ROUTES -----------------
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
        
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    finally:
        conn.close()
    
    if not user or not werkzeug.security.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401
        
    token = generate_token(user["id"], user["username"])
    return jsonify({
        "token": token,
        "username": user["username"],
        "message": "Login successful"
    })

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
        
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username already taken"}), 400
            
        password_hash = werkzeug.security.generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
    except Exception as e:
        print(f"Registration database error: {e}")
        return jsonify({"error": "Failed to create user account"}), 500
    finally:
        conn.close()
        
    return jsonify({"message": "Registration successful. You can now log in!"}), 201

# ----------------- COMMAND CENTER METRICS -----------------
@app.route("/api/dashboard/metrics", methods=["GET"])
@login_required
def get_metrics():
    conn = get_db()
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        
        cursor.execute("SELECT COUNT(*) FROM photos WHERE user_id = ?", (user_id,))
        total_photos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT name) FROM people WHERE user_id = ?", (user_id,))
        total_people = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM delivery_history WHERE user_id = ? AND status = 'success'", (user_id,))
        total_delivered = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM delivery_history WHERE user_id = ? AND delivery_method = 'email'", (user_id,))
        emails_sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM delivery_history WHERE user_id = ? AND delivery_method = 'whatsapp'", (user_id,))
        wa_sent = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM faces f 
            JOIN photos p ON f.photo_id = p.id 
            WHERE p.user_id = ? AND f.label = 'Unknown'
        """, (user_id,))
        untagged_faces = cursor.fetchone()[0]
        
        return jsonify({
            "total_photos": total_photos,
            "total_people": total_people,
            "total_delivered": total_delivered,
            "emails_sent": emails_sent,
            "whatsapp_deliveries": wa_sent,
            "untagged_faces": untagged_faces
        })
    finally:
        conn.close()

# ----------------- PHOTOS & UPLOADS -----------------
@app.route("/api/photos", methods=["GET"])
@login_required
def get_photos():
    person = request.args.get("person", "").strip()
    date = request.args.get("date", "").strip()
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, GROUP_CONCAT(f.label) as face_labels
            FROM photos p
            LEFT JOIN faces f ON f.photo_id = p.id
        """
        params = [request.user["user_id"]]
        conditions = ["p.user_id = ?"]
        
        if person:
            conditions.append("(f.label LIKE ? OR p.recognized_person LIKE ? OR p.original_filename LIKE ?)")
            params.extend([f"%{person}%", f"%{person}%", f"%{person}%"])
        if date:
            conditions.append("p.upload_date = ?")
            params.append(date)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " GROUP BY p.id ORDER BY p.id DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        photos_list = []
        all_faces = []
        for r in rows:
            labels = list(set(r["face_labels"].split(","))) if r["face_labels"] else []
            # Filter out duplicates and empty labels
            labels = [l for l in labels if l and l != 'None']
            
            # Load faces coordinates for overlays and confidence calculations
            cursor.execute("SELECT id, label, embedding, x, y, w, h FROM faces WHERE photo_id = ?", (r["id"],))
            faces = [dict(f) for f in cursor.fetchall()]
            all_faces.extend(faces)
            
            photos_list.append({
                "id": r["id"],
                "public_id": r["public_id"],
                "secure_url": r["secure_url"],
                "original_filename": r["original_filename"],
                "upload_date": r["upload_date"],
                "recognized_person": r["recognized_person"],
                "created_at": r["created_at"],
                "labels": labels,
                "faces": faces,
                "event": r["event"] if "event" in r.keys() else "General"
            })
            
        if all_faces:
            calculate_face_confidences(all_faces)
            for face in all_faces:
                if "embedding" in face:
                    del face["embedding"]
                    
        return jsonify(photos_list)
    finally:
        conn.close()

def identify_face_with_gemini(file_bytes, x, y, w, h, filename):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment. Skipping celebrity check.")
        return "Non-celebrity"
        
    try:
        from PIL import Image
        import io
        from google import genai
        from google.genai import types
        
        # 1. Crop face from image bytes
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x, width))
        y1 = max(0, min(y, height))
        x2 = max(0, min(x + w, width))
        y2 = max(0, min(y + h, height))
        
        if x2 <= x1 or y2 <= y1:
            return "Non-celebrity"
            
        face_image = image.crop((x1, y1, x2, y2))
        
        # Save cropped face to bytes
        img_byte_arr = io.BytesIO()
        face_image.save(img_byte_arr, format='JPEG')
        face_bytes = img_byte_arr.getvalue()
        
        # 2. Call Gemini API
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=face_bytes,
                    mime_type='image/jpeg'
                ),
                "Identify the person in this face photo. If they are a well-known public figure, celebrity, or historical figure, reply ONLY with their name. Otherwise, reply ONLY with 'Non-celebrity'."
            ]
        )
        
        result = response.text.strip()
        print(f"Gemini celebrity check result for face in {filename}: {result}")
        
        # Perform sanity check on response
        if result and len(result) < 50 and "non-celebrity" not in result.lower() and "error" not in result.lower():
            return result
            
        return "Non-celebrity"
    except Exception as e:
        print(f"Failed to identify face using Gemini: {e}")
        return "Non-celebrity"


@app.route("/api/upload", methods=["POST"])

@login_required
def upload_photos():
    if 'photos' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
        
    files = request.files.getlist('photos')
    uploaded_photos = []
    
    # Pre-fetch known profiles to compare against
    known_profiles = []
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.label, f.embedding 
            FROM faces f 
            JOIN photos p ON f.photo_id = p.id 
            WHERE p.user_id = ? AND f.label != 'Unknown'
        """, (request.user["user_id"],))
        known_profiles = [{"label": row["label"], "embedding": json.loads(row["embedding"])} for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching known face profiles: {e}")
    finally:
        if conn:
            conn.close()
            
    # Process files (uploads + face representation) outside of the DB lock
    prepared_items = []
    
    for file in files:
        if file.filename == '':
            continue
            
        file_bytes = file.read()
        filename = file.filename
        upload_date = time.strftime("%Y-%m-%d")
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 1. Upload to Cloudinary with secure option
        try:
            upload_result = cloudinary.uploader.upload(
                file_bytes,
                folder="drishyamitra/uploads",
                secure=True
            )
            public_id = upload_result.get("public_id")
            secure_url = upload_result.get("secure_url")
        except Exception as e:
            # Fallback to local storage if credentials are placeholder
            print(f"Cloudinary upload failed: {e}. Falling back to local storage.")
            os.makedirs("static/uploads", exist_ok=True)
            local_filename = f"{int(time.time())}_{filename}"
            local_path = os.path.join("static/uploads", local_filename)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            public_id = f"local_{local_filename}"
            secure_url = f"/static/uploads/{local_filename}"
            
        # 2. Write photo bytes to temp file for DeepFace analysis
        os.makedirs("temp", exist_ok=True)
        temp_path = os.path.join("temp", f"scan_{int(time.time())}_{filename}")
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
            
        # 3. Run SCRFD face detection & ArcFace recognition
        detected_faces = []
        event_name = "Casual"
        event_confidence = 1.0
        event_occasion = "Non_Occasion"
        try:
            representations = detect_and_represent(temp_path, enforce_detection=False)
            
            for rep in representations:
                box = rep.get("facial_area", {})
                emb = rep.get("embedding", [])
                
                # Check for face matches using FAISS flat index search
                matched_label = match_face_faiss(emb, known_profiles, threshold=COSINE_SIM_THRESHOLD)
                            
                if matched_label == "Unknown":
                    # Check with Gemini LLM for celebrity identification
                    celebrity_name = identify_face_with_gemini(file_bytes, box.get("x"), box.get("y"), box.get("w"), box.get("h"), filename)
                    if celebrity_name != "Non-celebrity":
                        matched_label = celebrity_name
                            
                detected_faces.append({
                    "label": matched_label,
                    "embedding": emb,
                    "x": box.get("x"),
                    "y": box.get("y"),
                    "w": box.get("w"),
                    "h": box.get("h")
                })
                
            try:
                event_name, event_confidence, event_occasion = classify_photo_event(temp_path, num_faces=len(representations))
            except Exception as ce:
                print(f"Event classification failed during upload: {ce}")
        except Exception as ex:
            print(f"SCRFD/ArcFace analysis failed for {filename}: {ex}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_err:
                    print(f"Failed to delete temp file {temp_path}: {cleanup_err}")
                    
        prepared_items.append({
            "public_id": public_id,
            "secure_url": secure_url,
            "filename": filename,
            "upload_date": upload_date,
            "created_at": created_at,
            "faces": detected_faces,
            "event": event_name,
            "event_confidence": event_confidence,
            "event_occasion": event_occasion
        })
        
    # 4. Save Photo metadata to SQLite in a quick, single transaction
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        for item in prepared_items:
            cursor.execute("""
                INSERT INTO photos (user_id, public_id, secure_url, original_filename, upload_date, created_at, event, event_confidence, event_occasion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (request.user["user_id"], item["public_id"], item["secure_url"], item["filename"], item["upload_date"], item["created_at"], item["event"], item["event_confidence"], item["event_occasion"]))
            photo_id = cursor.lastrowid
            
            recognized_people_list = []
            for face in item["faces"]:
                cursor.execute("""
                    INSERT INTO faces (photo_id, label, embedding, x, y, w, h)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (photo_id, face["label"], json.dumps(face["embedding"]), face["x"], face["y"], face["w"], face["h"]))
                if face["label"] != "Unknown":
                    recognized_people_list.append(face["label"])
                    cursor.execute("SELECT id FROM people WHERE user_id = ? AND name = ?", (request.user["user_id"], face["label"]))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO people (user_id, name) VALUES (?, ?)", (request.user["user_id"], face["label"]))
                    
            if recognized_people_list:
                recognized_person_str = ", ".join(list(set(recognized_people_list)))
                cursor.execute("UPDATE photos SET recognized_person = ? WHERE id = ?", (recognized_person_str, photo_id))

                
            uploaded_photos.append({
                "id": photo_id,
                "filename": item["filename"],
                "secure_url": item["secure_url"]
            })
            
        conn.commit()
    except Exception as db_err:
        print(f"Database save failed: {db_err}")
        return jsonify({"error": f"Database save failed: {db_err}"}), 500
    finally:
        if conn:
            conn.close()
            
    return jsonify({"message": f"Successfully uploaded {len(uploaded_photos)} photos", "photos": uploaded_photos})


@app.route("/api/photos/<int:photo_id>", methods=["DELETE"])
@login_required
def delete_photo(photo_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # 1. Fetch photo public_id
        cursor.execute("SELECT public_id, user_id FROM photos WHERE id = ?", (photo_id,))
        photo = cursor.fetchone()
        
        if not photo:
            return jsonify({"error": "Photo not found"}), 404
            
        if photo["user_id"] != request.user["user_id"]:
            return jsonify({"error": "Unauthorized to delete this photo"}), 403
            
        public_id = photo["public_id"]
        
        # 2. Delete from Cloudinary
        if not public_id.startswith("local_"):
            try:
                cloudinary.uploader.destroy(public_id)
            except Exception as e:
                print(f"Failed to delete {public_id} from Cloudinary: {e}")
                
        # 3. Delete local file if it is stored locally
        else:
            local_filename = public_id.replace("local_", "")
            local_path = os.path.join("static/uploads", local_filename)
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception as e:
                    print(f"Failed to delete local file {local_path}: {e}")
            
        # 4. Delete photo & cascade faces from SQLite
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()
        
        return jsonify({"message": "Photo deleted successfully"})
    finally:
        conn.close()

# ----------------- FACE LABELING & PROPAGATION -----------------
@app.route("/api/faces/<int:face_id>/label", methods=["POST"])
@login_required
def label_face(face_id):
    data = request.get_json() or {}
    label = data.get("label", "").strip()
    
    if not label:
        return jsonify({"error": "Missing label name"}), 400
        
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        # Check if face exists and query ownership
        cursor.execute("""
            SELECT f.photo_id, f.embedding, p.user_id 
            FROM faces f 
            JOIN photos p ON f.photo_id = p.id 
            WHERE f.id = ?
        """, (face_id,))
        face = cursor.fetchone()
        if not face:
            return jsonify({"error": "Face record not found"}), 404
            
        if face["user_id"] != request.user["user_id"]:
            return jsonify({"error": "Unauthorized to label this face"}), 403
            
        embedding_vector = json.loads(face["embedding"])
        
        # Update current face label
        cursor.execute("UPDATE faces SET label = ? WHERE id = ?", (label, face_id))
        
        # Add new person to people (contacts) directory if not exists
        cursor.execute("SELECT id FROM people WHERE user_id = ? AND name = ?", (request.user["user_id"], label))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO people (user_id, name) VALUES (?, ?)", (request.user["user_id"], label))
            
        # Cascade updates to recognized_person fields in photos
        cursor.execute("UPDATE photos SET recognized_person = ? WHERE id = ?", (label, face["photo_id"]))
        
        conn.commit()
    finally:
        conn.close()
        
    # Run tag propagation: auto-recognize all similar unknown faces belonging to this user
    propagated_count = propagate_labels(label, embedding_vector, request.user["user_id"])
    
    return jsonify({
        "message": f"Face labeled successfully.",
        "propagated_count": propagated_count
    })

# ----------------- CONTACT MANAGEMENT -----------------
@app.route("/api/contacts", methods=["GET", "POST"])
@login_required
def manage_contacts():
    conn = get_db()
    try:
        cursor = conn.cursor()
        
        if request.method == "POST":
            data = request.get_json() or {}
            name = data.get("name", "").strip()
            email = data.get("email", "").strip()
            whatsapp = data.get("whatsapp_number", "").strip()
            
            if not name:
                return jsonify({"error": "Missing contact name"}), 400
                
            cursor.execute("""
                INSERT INTO people (user_id, name, email, whatsapp_number)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET email=excluded.email, whatsapp_number=excluded.whatsapp_number
            """, (request.user["user_id"], name, email, whatsapp))
            conn.commit()
            return jsonify({"message": "Contact saved successfully"})
            
        cursor.execute("SELECT id, name, email, whatsapp_number FROM people WHERE user_id = ? ORDER BY name ASC", (request.user["user_id"],))
        contacts = [dict(c) for c in cursor.fetchall()]
        return jsonify(contacts)
    finally:
        conn.close()

# ----------------- DELIVERY DISPATCHES -----------------
def dispatch_delivery(method, recipient, photo_ids):
    conn = get_db()
    photo_data = []
    try:
        cursor = conn.cursor()
        for pid in photo_ids:
            cursor.execute("SELECT secure_url, original_filename FROM photos WHERE id = ?", (pid,))
            p = cursor.fetchone()
            if p:
                photo_data.append((p["secure_url"], p["original_filename"]))
    finally:
        conn.close()
        
    if not photo_data:
        return "failed", "No photos found to deliver."
        
    # Suppress insecure SSL warnings for requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    if method == "email":
        brevo_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "dsrishtidimri@gmail.com")
        sender_name = os.getenv("BREVO_SENDER_NAME", "Drishyamitra AI")
        verify_ssl = os.getenv("BREVO_VERIFY_SSL", "True").lower() in ["true", "1", "yes"]
        
        if brevo_key:
            try:
                import base64
                import requests
                
                # Build attachments list for Brevo API
                attachments = []
                for secure_url, original_filename in photo_data:
                    file_bytes = None
                    if secure_url.startswith("/static/"):
                        local_path = secure_url.lstrip("/")
                        if os.path.exists(local_path):
                            with open(local_path, "rb") as f:
                                file_bytes = f.read()
                    else:
                        r = requests.get(secure_url, timeout=15, verify=verify_ssl)
                        if r.status_code == 200:
                            file_bytes = r.content
                            
                    if file_bytes:
                        b64_content = base64.b64encode(file_bytes).decode('utf-8')
                        attachments.append({
                            "name": original_filename,
                            "content": b64_content
                        })
                        
                # Send email using Brevo REST API v3
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": brevo_key,
                    "content-type": "application/json"
                }
                
                payload = {
                    "sender": {"name": sender_name, "email": sender_email},
                    "to": [{"email": recipient}],
                    "subject": f"{sender_name} - Photo Delivery",
                    "textContent": f"Hello,\n\nHere are your {len(photo_data)} photo(s) retrieved from {sender_name}.\n\nBest regards,\n{sender_name} Team"
                }
                
                if attachments:
                    payload["attachment"] = attachments
                    
                res = requests.post(url, headers=headers, json=payload, timeout=20, verify=verify_ssl)
                if res.status_code not in [200, 201, 202]:
                    raise Exception(f"Brevo API returned HTTP {res.status_code}: {res.text}")
                    
                return "success", f"Email delivered successfully to {recipient} via Brevo API with {len(attachments)} attachment(s)."
            except Exception as brevo_err:
                print(f"Brevo mail dispatch failed: {brevo_err}")
                return "failed", f"Brevo email dispatch failed: {brevo_err}"
        else:
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_username)
            
            if not (smtp_server and smtp_username and smtp_password):
                return "success", f"Simulated: Email sent to {recipient} with {len(photo_data)} photo(s). (Configure SMTP in .env for actual delivery)"
                
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.base import MIMEBase
                from email import encoders
                import requests
                
                msg = MIMEMultipart()
                msg['From'] = smtp_from
                msg['To'] = recipient
                msg['Subject'] = "Drishyamitra AI - Photo Delivery"
                
                body = f"Hello,\n\nHere are your {len(photo_data)} photo(s) retrieved from Drishyamitra AI.\n\nBest regards,\nDrishyamitra AI Team"
                msg.attach(MIMEText(body, 'plain'))
                
                for secure_url, original_filename in photo_data:
                    file_bytes = None
                    
                    # Check if local file
                    if secure_url.startswith("/static/"):
                        local_path = secure_url.lstrip("/")
                        if os.path.exists(local_path):
                            with open(local_path, "rb") as f:
                                file_bytes = f.read()
                    else:
                        # Download Cloudinary file
                        try:
                            r = requests.get(secure_url, timeout=15, verify=False)
                            if r.status_code == 200:
                                file_bytes = r.content
                        except Exception as download_err:
                            print(f"Failed to download remote photo {secure_url}: {download_err}")
                            
                    if file_bytes:
                        part = MIMEBase('application', "octet-stream")
                        part.set_payload(file_bytes)
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{original_filename}"')
                        msg.attach(part)
                        
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_from, recipient, msg.as_string())
                server.quit()
                
                return "success", f"Email sent successfully to {recipient} with {len(photo_data)} attachment(s)."
            except Exception as mail_err:
                print(f"Failed to send email to {recipient}: {mail_err}")
                return "failed", f"Email delivery failed: {mail_err}"
            
    elif method == "whatsapp":
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
        
        wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        
        import re
        
        # 1. Prioritize Twilio WhatsApp if credentials are set (supports local media upload via tmpfiles fallback)
        if twilio_sid and twilio_token and twilio_from:
            try:
                import requests
                from requests.auth import HTTPBasicAuth
                
                # Format Twilio number formats: remove whatsapp: prefix if present
                clean_from = twilio_from.strip()
                if clean_from.startswith("whatsapp:"):
                    clean_from = clean_from.replace("whatsapp:", "")
                    
                clean_recipient = recipient.strip()
                if clean_recipient.startswith("whatsapp:"):
                    clean_recipient = clean_recipient.replace("whatsapp:", "")
                    
                # Format to E.164 with a leading plus sign
                digits_only = re.sub(r"\D", "", clean_recipient)
                if len(digits_only) == 10:
                    clean_recipient = "+91" + digits_only
                else:
                    if not clean_recipient.startswith("+"):
                        clean_recipient = "+" + digits_only
                    else:
                        clean_recipient = "+" + digits_only
                        
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                
                # Compile photo URLs
                photo_urls = [url for url, _ in photo_data]
                links_str = "\n".join([f"- {url}" if url.startswith("http") else f"- http://localhost:5000{url}" for url in photo_urls])
                body_text = f"Hello! Here are your photo(s) from Drishyamitra AI:\n\n{links_str}"
                
                # Prepare payload
                payload = [
                    ("From", f"whatsapp:{clean_from}"),
                    ("To", f"whatsapp:{clean_recipient}"),
                    ("Body", body_text)
                ]
                
                # Attach remote Cloudinary URLs as MediaUrl parameters, or upload local files to tmpfiles.org
                sent_media_count = 0
                for secure_url, original_filename in photo_data:
                    # If it's a remote public URL (not local and not localhost)
                    if secure_url.startswith("http") and "localhost" not in secure_url:
                        payload.append(("MediaUrl", secure_url))
                        sent_media_count += 1
                    else:
                        try:
                            local_path = secure_url.lstrip("/")
                            if os.path.exists(local_path):
                                with open(local_path, "rb") as f:
                                    local_bytes = f.read()
                                mime_type = "image/jpeg"
                                if secure_url.lower().endswith(".png"):
                                    mime_type = "image/png"
                                elif secure_url.lower().endswith(".gif"):
                                    mime_type = "image/gif"
                                
                                upload_res = requests.post(
                                    "https://tmpfiles.org/api/v1/upload",
                                    files={"file": (original_filename, local_bytes, mime_type)},
                                    timeout=15
                                )
                                if upload_res.status_code in [200, 201]:
                                    tmp_url = upload_res.json().get("data", {}).get("url")
                                    if tmp_url:
                                        direct_url = tmp_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                                        payload.append(("MediaUrl", direct_url))
                                        sent_media_count += 1
                                        print(f"Twilio local file upload to tmpfiles: {direct_url}")
                        except Exception as upload_err:
                            print(f"Failed to upload local file to tmpfiles.org for Twilio dispatch: {upload_err}")
                        
                res = requests.post(url, data=payload, auth=HTTPBasicAuth(twilio_sid, twilio_token), timeout=20, verify=False)
                if res.status_code not in [200, 201]:
                    try:
                        res_json = res.json()
                    except Exception:
                        res_json = {}
                        
                    if res.status_code == 401:
                        raise Exception(
                            "Twilio authentication failed (Error Code: 20003). \n\n"
                            "👉 **How to fix this:**\n"
                            "1. Log into your **Twilio Console** dashboard.\n"
                            "2. Locate and copy the **Account SID** and **Auth Token**.\n"
                            "3. Make sure the credentials in your `.env` file match the Twilio Console exactly."
                        )
                    else:
                        msg = res_json.get("message", res.text)
                        raise Exception(f"Twilio API returned HTTP {res.status_code}: {msg}")
                    
                details = f"WhatsApp message sent successfully to {recipient} via Twilio."
                if sent_media_count > 0:
                    details += f" Sent {sent_media_count} media attachment(s) directly."
                return "success", details
            except Exception as twilio_err:
                print(f"Twilio WhatsApp dispatch failed: {twilio_err}")
                return "failed", f"WhatsApp delivery failed: {twilio_err}"
                
        # 2. Fallback to Meta WhatsApp Business Cloud API if credentials are set
        elif wa_token and wa_phone_id:
            try:
                import requests
                
                # Format Meta recipient number: digits only (no leading +)
                clean_recipient = re.sub(r"\D", "", recipient.strip())
                if len(clean_recipient) == 10:
                    clean_recipient = "91" + clean_recipient
                    
                # Compile list of photo URLs
                photo_urls = [url for url, _ in photo_data]
                links_str = "\n".join([f"- {url}" if url.startswith("http") else f"- http://localhost:5000{url}" for url in photo_urls])
                body_text = f"Hello! Here are your photo(s) from Drishyamitra AI:\n\n{links_str}"
                
                url = f"https://graph.facebook.com/v25.0/{wa_phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {wa_token}",
                    "Content-Type": "application/json"
                }
                
                # First, send the 'hello_world' template handshake to open the 24-hour conversation window
                payload_template = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_recipient,
                    "type": "template",
                    "template": {
                        "name": "hello_world",
                        "language": {
                            "code": "en_US"
                        }
                    }
                }
                requests.post(url, headers=headers, json=payload_template, timeout=20, verify=False)
                
                # Next, send the text message with the links
                payload_text = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": body_text
                    }
                }
                
                # Bypassing SSL verification due to machine-specific certificate trust store issues
                res = requests.post(url, headers=headers, json=payload_text, timeout=20, verify=False)
                
                try:
                    res_json = res.json()
                except Exception:
                    res_json = {}
                    
                if res.status_code not in [200, 201]:
                    if res_json and "error" in res_json:
                        err = res_json["error"]
                        code = err.get("code")
                        msg = err.get("message", "")
                        if code == 131030 or "allowed list" in msg.lower():
                            raise Exception(
                                f"Recipient phone number (+{clean_recipient}) is not in the allowed list for your WhatsApp Sandbox account. \n\n"
                                "👉 **How to fix this:**\n"
                                "1. Log into your **Meta for Developers** dashboard.\n"
                                "2. Navigate to your app and go to **WhatsApp -> API Setup**.\n"
                                f"3. Locate the **'To'** field on the right sidebar and click **'Manage Phone Numbers'**.\n"
                                f"4. Add **+{clean_recipient}** as a verified test phone number and confirm the verification code."
                            )
                        elif code == 131047 or "24 hours" in msg.lower():
                            raise Exception(
                                f"Cannot send message to +{clean_recipient} because more than 24 hours have passed since they last messaged you. \n\n"
                                "👉 **How to fix this:**\n"
                                "WhatsApp Cloud API sandbox requires a session to be open. Send any test message from the recipient's phone number to your sandbox number to re-open the 24-hour customer service window, and try again."
                            )
                        else:
                            raise Exception(f"{msg} (Error Code: {code})")
                    raise Exception(f"WhatsApp Text API returned HTTP {res.status_code}: {res.text}")
                
                # Next, send each image as a real WhatsApp media message (Cloudinary link or local upload media ID)
                sent_media_count = 0
                for secure_url, original_filename in photo_data:
                    if secure_url.startswith("http"):
                        # For remote Cloudinary URLs, send directly using the public link
                        payload_img = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": clean_recipient,
                            "type": "image",
                            "image": {
                                "link": secure_url
                            }
                        }
                        img_res = requests.post(url, headers=headers, json=payload_img, timeout=20, verify=False)
                        if img_res.status_code in [200, 201]:
                            sent_media_count += 1
                        else:
                            print(f"Failed to send remote image link {secure_url}: {img_res.text}")
                    else:
                        try:
                            local_path = secure_url.lstrip("/")
                            if os.path.exists(local_path):
                                with open(local_path, "rb") as f:
                                    file_bytes = f.read()
                                
                                mime_type = "image/jpeg"
                                if secure_url.lower().endswith(".png"):
                                    mime_type = "image/png"
                                elif secure_url.lower().endswith(".gif"):
                                    mime_type = "image/gif"
                                
                                upload_url = f"https://graph.facebook.com/v25.0/{wa_phone_id}/media"
                                files = {
                                    "file": (original_filename, file_bytes, mime_type),
                                    "messaging_product": (None, "whatsapp")
                                }
                                media_headers = {
                                    "Authorization": f"Bearer {wa_token}"
                                }
                                
                                upload_res = requests.post(upload_url, headers=media_headers, files=files, timeout=20, verify=False)
                                if upload_res.status_code in [200, 201]:
                                    media_id = upload_res.json().get("id")
                                    payload_img = {
                                        "messaging_product": "whatsapp",
                                        "recipient_type": "individual",
                                        "to": clean_recipient,
                                        "type": "image",
                                        "image": {
                                            "id": media_id
                                        }
                                    }
                                    img_res = requests.post(url, headers=headers, json=payload_img, timeout=20, verify=False)
                                    if img_res.status_code in [200, 201]:
                                        sent_media_count += 1
                                    else:
                                        print(f"Failed to send local image via media ID {media_id}: {img_res.text}")
                                else:
                                    print(f"Failed to upload local image to Meta WhatsApp media endpoint: {upload_res.text}")
                        except Exception as upload_err:
                            print(f"Error uploading and sending local WhatsApp image: {upload_err}")
                
                details = f"WhatsApp message sent successfully to {recipient}."
                if sent_media_count > 0:
                    details += f" Sent {sent_media_count} media attachment(s) directly."
                return "success", details
            except Exception as wa_err:
                print(f"Meta WhatsApp Cloud API dispatch failed: {wa_err}")
                return "failed", f"WhatsApp delivery failed: {wa_err}"
                
        # 3. Fallback to Simulation
        else:
            return "success", f"Simulated: WhatsApp message sent to {recipient} with {len(photo_data)} photo(s). (Configure Twilio or Meta WhatsApp Business API in .env for actual delivery)"
            
    return "failed", f"Unknown delivery method: {method}"

@app.route("/api/delivery/email", methods=["POST"])
@login_required
def send_email():
    data = request.get_json() or {}
    recipient = data.get("recipient", "").strip()
    photo_ids = data.get("photo_ids", [])
    
    if not recipient or not photo_ids:
        return jsonify({"error": "Missing recipient or photo selection"}), 400
        
    # Verify photos ownership
    conn = get_db()
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(photo_ids))
        cursor.execute(f"SELECT COUNT(*) FROM photos WHERE user_id = ? AND id IN ({placeholders})", [request.user["user_id"]] + photo_ids)
        if cursor.fetchone()[0] != len(photo_ids):
            return jsonify({"error": "Unauthorized photo selection"}), 403
    finally:
        conn.close()
        
    status, details = dispatch_delivery("email", recipient, photo_ids)
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO delivery_history (user_id, timestamp, delivery_method, recipient, photo_ids, status, details)
            VALUES (?, ?, 'email', ?, ?, ?, ?)
        """, (request.user["user_id"], timestamp, recipient, json.dumps(photo_ids), status, details))
        conn.commit()
    finally:
        conn.close()
        
    if status == "failed":
        return jsonify({"error": details}), 500
    return jsonify({"message": "Email request processed", "details": details})

@app.route("/api/delivery/whatsapp", methods=["POST"])
@login_required
def send_whatsapp():
    data = request.get_json() or {}
    recipient = data.get("recipient", "").strip()
    photo_ids = data.get("photo_ids", [])
    
    if not recipient or not photo_ids:
        return jsonify({"error": "Missing recipient or photo selection"}), 400
        
    # Verify photos ownership
    conn = get_db()
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(photo_ids))
        cursor.execute(f"SELECT COUNT(*) FROM photos WHERE user_id = ? AND id IN ({placeholders})", [request.user["user_id"]] + photo_ids)
        if cursor.fetchone()[0] != len(photo_ids):
            return jsonify({"error": "Unauthorized photo selection"}), 403
    finally:
        conn.close()
        
    status, details = dispatch_delivery("whatsapp", recipient, photo_ids)
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO delivery_history (user_id, timestamp, delivery_method, recipient, photo_ids, status, details)
            VALUES (?, ?, 'whatsapp', ?, ?, ?, ?)
        """, (request.user["user_id"], timestamp, recipient, json.dumps(photo_ids), status, details))
        conn.commit()
    finally:
        conn.close()
        
    if status == "failed":
        return jsonify({"error": details}), 500
    return jsonify({"message": "WhatsApp request processed", "details": details})

@app.route("/api/delivery/history", methods=["GET"])
@login_required
def get_delivery_history():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, delivery_method, recipient, photo_ids, status, details 
            FROM delivery_history 
            WHERE user_id = ? 
            ORDER BY id DESC
        """, (request.user["user_id"],))
        history = [dict(h) for h in cursor.fetchall()]
        return jsonify(history)
    finally:
        conn.close()

# ----------------- AI CHAT BOT STATE MACHINE -----------------
@app.route("/api/agent", methods=["POST"])
@login_required
def chat_agent():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    user_id = request.user["user_id"]
    
    if not query:
        return jsonify({"error": "Empty query"}), 400
        
    # Get or initialize user session
    session = AGENT_SESSIONS.get(user_id, {"state": "IDLE", "photos": [], "method": None, "person": None, "recipient": None})
    AGENT_SESSIONS[user_id] = session
    
    logs = []
    reply = ""
    action_type = "chat"
    
    # 1. State: IDLE
    if session["state"] == "IDLE":
        logs.append(f"Intent Agent: Processing query: '{query}'")
        q_lower = query.lower()
        
        # Check Cancel
        if q_lower in ["cancel", "exit", "stop", "abort"]:
            AGENT_SESSIONS[user_id] = {"state": "IDLE", "photos": [], "method": None, "person": None, "recipient": None}
            return jsonify({
                "reply": "Request cancelled. How else can I help you?",
                "logs": ["Session reset by user"],
                "photos": [],
                "state": "IDLE"
            })
            
        # Check Organize Photos command
        if any(keyword in q_lower for keyword in ["organize", "group", "folder", "structure"]):
            logs.append("Intent Agent: Detected photo organization request.")
            logs.append("Coordinator Agent: Invoking Organization Agent...")
            import shutil
            conn = get_db()
            copied_count = 0
            created_folders = set()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.secure_url, p.original_filename, p.event, p.event_occasion, GROUP_CONCAT(f.label) as face_labels
                    FROM photos p
                    LEFT JOIN faces f ON f.photo_id = p.id
                    WHERE p.user_id = ?
                    GROUP BY p.id
                """, (user_id,))
                photos = cursor.fetchall()
                
                base_dir = os.path.join(os.getcwd(), "organized_photos")
                people_dir = os.path.join(base_dir, "People")
                events_dir = os.path.join(base_dir, "Events")
                
                os.makedirs(people_dir, exist_ok=True)
                os.makedirs(events_dir, exist_ok=True)
                
                for photo in photos:
                    filename = photo["original_filename"]
                    secure_url = photo["secure_url"]
                    event_name = photo["event"] or "Casual"
                    event_occasion = photo["event_occasion"] or "Non_Occasion"
                    
                    labels_str = photo["face_labels"]
                    labels = list(set(labels_str.split(","))) if labels_str else []
                    labels = [l for l in labels if l and l != 'None' and l != 'Unknown']
                    
                    file_bytes = None
                    if secure_url.startswith("/static/"):
                        local_path = secure_url.lstrip("/")
                        if os.path.exists(local_path):
                            with open(local_path, "rb") as f:
                                file_bytes = f.read()
                    else:
                        import requests
                        try:
                            r = requests.get(secure_url, timeout=10)
                            if r.status_code == 200:
                                file_bytes = r.content
                        except Exception:
                            pass
                    
                    if not file_bytes:
                        continue
                        
                    # Copy to Event Folder
                    safe_event_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in event_name])
                    event_folder = os.path.join(events_dir, safe_event_name)
                    os.makedirs(event_folder, exist_ok=True)
                    created_folders.add(f"Events/{safe_event_name}/")
                    with open(os.path.join(event_folder, filename), "wb") as f:
                        f.write(file_bytes)
                    copied_count += 1
                    
                    # Copy to People Folders
                    for label in labels:
                        safe_person_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in label])
                        safe_occasion = "".join([c if c.isalnum() or c in " _-" else "_" for c in event_occasion])
                        
                        person_folder = os.path.join(people_dir, safe_person_name, safe_occasion, safe_event_name)
                        os.makedirs(person_folder, exist_ok=True)
                        created_folders.add(f"People/{safe_person_name}/{safe_occasion}/{safe_event_name}/")
                        with open(os.path.join(person_folder, filename), "wb") as f:
                            f.write(file_bytes)
                        copied_count += 1
                        
                conn.close()
                logs.append(f"Organization Agent: Successfully structured files. Copied {copied_count} items.")
                reply = f"📂 **Organization Completed!**\n\nI have successfully organized all your photos into the following folders under `organized_photos/`:\n"
                for folder in sorted(list(created_folders)):
                    reply += f"- {folder}\n"
                reply += f"\nTotal file copies created: **{copied_count}**."
                
                return jsonify({
                    "reply": reply,
                    "logs": logs,
                    "photos": [],
                    "state": "IDLE"
                })
            except Exception as ex:
                if conn: conn.close()
                return jsonify({
                    "reply": f"❌ Failed to organize photos: {ex}",
                    "logs": logs,
                    "photos": [],
                    "state": "IDLE"
                })
            
        # Extract Entities (Heuristics + Dynamic DB Contacts/Groups)
        person = None
        conn_temp = get_db()
        try:
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT name FROM people WHERE user_id = ?", (user_id,))
            all_names = [row["name"] for row in cursor_temp.fetchall()]
        except Exception as e:
            print(f"Failed to fetch people names for chatbot extraction: {e}")
            all_names = []
        finally:
            conn_temp.close()

        # Sort names by length descending to match longer names first (e.g. Person_10 before Person_1)
        all_names.sort(key=len, reverse=True)
        for name in all_names:
            if name.lower() in q_lower:
                person = name
                break
        
        event = None
        if "wedding" in q_lower or "marriage" in q_lower or "shaadi" in q_lower: event = "Wedding"
        elif "birthday" in q_lower or "bday" in q_lower: event = "Birthday"
        elif "graduation" in q_lower: event = "Graduation"
        elif "tour" in q_lower or "trip" in q_lower or "vacation" in q_lower or "trek" in q_lower or "manali" in q_lower: event = "Tour/Trip"
        elif "festival" in q_lower or "diwali" in q_lower or "holi" in q_lower: event = "Festival"
        elif "family" in q_lower or "gathering" in q_lower: event = "Family"
        elif "party" in q_lower or "event" in q_lower: event = "Event"
        
        # Query Photos matching entities
        conn = get_db()
        try:
            cursor = conn.cursor()
            
            db_query = """
                SELECT p.id, p.secure_url, p.original_filename
                FROM photos p
                LEFT JOIN faces f ON f.photo_id = p.id
            """
            conditions = ["p.user_id = ?"]
            params = [user_id]
            
            if person:
                conditions.append("(f.label = ? OR p.recognized_person LIKE ? OR p.original_filename LIKE ?)")
                params.extend([person, f"%{person}%", f"%{person}%"])
            if event:
                conditions.append("(p.event LIKE ? OR p.original_filename LIKE ?)")
                params.extend([f"%{event}%", f"%{event}%"])
                
            if conditions:
                db_query += " WHERE " + " AND ".join(conditions)
            db_query += " GROUP BY p.id"
            
            cursor.execute(db_query, params)
            photos = [dict(row) for row in cursor.fetchall()]

            
            if not photos:
                logs.append("Search Agent: No matching photos found in database.")
                return jsonify({
                    "reply": f"I couldn't find any photos for '{person or event or 'selected criteria'}'. Please try uploading them first!",
                    "logs": logs,
                    "photos": [],
                    "state": "IDLE"
                })
                
            photo_ids = [p["id"] for p in photos]
            session["photos"] = photo_ids
            session["person"] = person
            logs.append(f"Search Agent: Retrieved {len(photos)} photo(s) from database.")
            
            # Check if they also asked to deliver in query
            asked_delivery = False
            method = None
            if "email" in q_lower or "gmail" in q_lower:
                asked_delivery = True
                method = "email"
            elif "whatsapp" in q_lower:
                asked_delivery = True
                method = "whatsapp"
                
            if asked_delivery:
                session["method"] = method
                logs.append(f"Intent Agent: Extracted delivery method: '{method}'")
                
                # Check for saved contact
                cursor.execute("SELECT email, whatsapp_number FROM people WHERE user_id = ? AND name = ?", (user_id, person))
                contact = cursor.fetchone()
                
                if contact and ((method == "email" and contact["email"]) or (method == "whatsapp" and contact["whatsapp_number"])):
                    recipient = contact["email"] if method == "email" else contact["whatsapp_number"]
                    session["recipient"] = recipient
                    session["state"] = "AWAITING_CONTACT_CONFIRMATION"
                    reply = f"I found a saved contact for {person}: **{recipient}**.\n\nWould you like to use this contact? (Yes / Choose Another)"
                else:
                    session["state"] = "AWAITING_RECIPIENT"
                    reply = f"I found {len(photos)} photos. Please enter the recipient's " + ("email address:" if method == "email" else "WhatsApp number (with country code, e.g. +919876543210):")
            else:
                session["state"] = "AWAITING_METHOD"
                reply = f"I found **{len(photos)}** photo(s). How would you like to send them?\n\n1. **Email**\n2. **WhatsApp**\n\nPlease select a delivery method (or type 'Cancel')."
        finally:
            conn.close()
            
        return jsonify({
            "reply": reply,
            "logs": logs,
            "photos": photos,
            "state": session["state"]
        })
        
    # 2. State: AWAITING_METHOD
    elif session["state"] == "AWAITING_METHOD":
        q_lower = query.lower()
        if q_lower in ["cancel", "exit", "abort"]:
            AGENT_SESSIONS[user_id] = {"state": "IDLE", "photos": [], "method": None, "person": None, "recipient": None}
            return jsonify({
                "reply": "Delivery aborted. How else can I help you?",
                "logs": ["Workflow aborted by user"],
                "photos": [],
                "state": "IDLE"
            })
            
        method = None
        if "1" in q_lower or "email" in q_lower:
            method = "email"
        elif "2" in q_lower or "whatsapp" in q_lower:
            method = "whatsapp"
            
        if not method:
            return jsonify({
                "reply": "Invalid input. Please choose **1. Email** or **2. WhatsApp** (or type 'Cancel').",
                "logs": ["Intent Agent: Unrecognized delivery method choice"],
                "photos": [],
                "state": "AWAITING_METHOD"
            })
            
        session["method"] = method
        logs.append(f"Intent Agent: Selected method: '{method}'")
        
        # Check for saved contact
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT email, whatsapp_number FROM people WHERE user_id = ? AND name = ?", (user_id, session["person"]))
            contact = cursor.fetchone()
        finally:
            conn.close()
        
        if contact and ((method == "email" and contact["email"]) or (method == "whatsapp" and contact["whatsapp_number"])):
            recipient = contact["email"] if method == "email" else contact["whatsapp_number"]
            session["recipient"] = recipient
            session["state"] = "AWAITING_CONTACT_CONFIRMATION"
            reply = f"I found a saved contact for {session['person']}: **{recipient}**.\n\nWould you like to use this contact? (Yes / Choose Another)"
        else:
            session["state"] = "AWAITING_RECIPIENT"
            reply = "Please enter the recipient's " + ("email address:" if method == "email" else "WhatsApp number (including country code, e.g. +919876543210):")
            
        return jsonify({
            "reply": reply,
            "logs": logs,
            "photos": [],
            "state": session["state"]
        })
        
    # 3. State: AWAITING_CONTACT_CONFIRMATION
    elif session["state"] == "AWAITING_CONTACT_CONFIRMATION":
        q_lower = query.lower()
        if "yes" in q_lower or "y" == q_lower:
            session["state"] = "AWAITING_TRANSACTION_CONFIRMATION"
            reply = f"You are about to send **{len(session['photos'])}** photo(s) to **{session['recipient']}**.\n\nProceed? (Yes / No)"
        else:
            session["state"] = "AWAITING_RECIPIENT"
            reply = "Okay, please enter the recipient's " + ("email address:" if session["method"] == "email" else "WhatsApp number (including country code, e.g. +919876543210):")
            
        return jsonify({
            "reply": reply,
            "logs": logs,
            "photos": [],
            "state": session["state"]
        })
        
    # 4. State: AWAITING_RECIPIENT
    elif session["state"] == "AWAITING_RECIPIENT":
        method = session["method"]
        recipient = query.strip()
        
        # Validation
        if method == "email":
            email_pattern = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$"
            if not re.match(email_pattern, recipient):
                return jsonify({
                    "reply": "Invalid email address format. Please enter a valid email address (e.g. user@example.com):",
                    "logs": ["Validation Agent: Email validation check failed"],
                    "photos": [],
                    "state": "AWAITING_RECIPIENT"
                })
        else:
            # WhatsApp E.164 pattern
            wa_pattern = r"^\+?[1-9]\d{1,14}$"
            if not re.match(wa_pattern, recipient):
                return jsonify({
                    "reply": "Invalid WhatsApp number format. Please enter the number including country code (e.g., +919876543210):",
                    "logs": ["Validation Agent: Phone number validation check failed"],
                    "photos": [],
                    "state": "AWAITING_RECIPIENT"
                })
                
        session["recipient"] = recipient
        session["state"] = "AWAITING_TRANSACTION_CONFIRMATION"
        logs.append(f"Validation Agent: Recipient '{recipient}' validated successfully.")
        
        reply = f"You are about to send **{len(session['photos'])}** photo(s) to **{recipient}**.\n\nProceed? (Yes / No)"
        return jsonify({
            "reply": reply,
            "logs": logs,
            "photos": [],
            "state": session["state"]
        })
        
    # 5. State: AWAITING_TRANSACTION_CONFIRMATION
    elif session["state"] == "AWAITING_TRANSACTION_CONFIRMATION":
        q_lower = query.lower()
        if "yes" in q_lower or "y" == q_lower:
            logs.append("Coordinator Agent: Transaction approved by user. Dispatching...")
            
            method = session["method"]
            recipient = session["recipient"]
            photo_ids = session["photos"]
            
            # Execute delivery (real SMTP or Twilio WhatsApp if configured, fallback to simulation)
            status, details = dispatch_delivery(method, recipient, photo_ids)
            
            conn = get_db()
            try:
                cursor = conn.cursor()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO delivery_history (user_id, timestamp, delivery_method, recipient, photo_ids, status, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, timestamp, method, recipient, json.dumps(photo_ids), status, details))
                conn.commit()
            finally:
                conn.close()
            
            logs.append(f"Audit Agent: Transaction saved in delivery logs. Status: {status}")
            
            # Reset session
            AGENT_SESSIONS[user_id] = {"state": "IDLE", "photos": [], "method": None, "person": None, "recipient": None}
            
            if status == "success":
                reply = f"🎉 **Success!** {len(photo_ids)} photos have been delivered to **{recipient}** via {method.capitalize()}."
                action_type = "delivery_success"
            else:
                reply = f"❌ **Delivery Failed:** {details}"
                action_type = "delivery_failed"
        else:
            AGENT_SESSIONS[user_id] = {"state": "IDLE", "photos": [], "method": None, "person": None, "recipient": None}
            reply = "Delivery cancelled. Session reset."
            logs.append("Coordinator Agent: Transaction aborted by user.")
            
        return jsonify({
            "reply": reply,
            "logs": logs,
            "photos": [],
            "state": "IDLE",
            "action_type": action_type
        })
        
    return jsonify({"error": "Unknown agent state"}), 500

@app.route("/api/people/clusters", methods=["GET"])
@login_required
def get_people_clusters():
    conn = get_db()
    clusters = []
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        
        # Fetch all faces and calculate average confidence
        cursor.execute("""
            SELECT f.id, f.label, f.embedding, f.photo_id
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        db_faces = [dict(row) for row in cursor.fetchall()]
        calculate_face_confidences(db_faces)
        
        by_label_conf = {}
        for f in db_faces:
            lbl = f["label"]
            if lbl != "Unknown":
                if lbl not in by_label_conf:
                    by_label_conf[lbl] = []
                by_label_conf[lbl].append(f["confidence"])
                
        # Query unique labeled people and select a sample face image box for preview crop
        cursor.execute("""
            SELECT f.label, p.secure_url, f.x, f.y, f.w, f.h, COUNT(DISTINCT f.photo_id) as photo_count
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE f.label != 'Unknown' AND p.user_id = ?
            GROUP BY f.label
            ORDER BY photo_count DESC
        """, (user_id,))
        rows = cursor.fetchall()
        for r in rows:
            lbl = r["label"]
            confs = by_label_conf.get(lbl, [1.0])
            avg_conf = float(np.mean(confs))
            
            clusters.append({
                "label": lbl,
                "secure_url": r["secure_url"],
                "x": r["x"],
                "y": r["y"],
                "w": r["w"],
                "h": r["h"],
                "photo_count": r["photo_count"],
                "avg_confidence": round(avg_conf, 3)
            })
    finally:
        conn.close()
    return jsonify(clusters)

@app.route("/api/search-by-face", methods=["POST"])
@login_required
def search_by_face():
    if 'face_image' not in request.files:
        return jsonify({"error": "No face image file part in request"}), 400
        
    file = request.files['face_image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    file_bytes = file.read()
    
    # 1. Write query photo bytes to temp file
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", f"query_search_{int(time.time())}_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    # 2. Extract embedding using SCRFD face detection & ArcFace model
    try:
        representations = detect_and_represent(temp_path, enforce_detection=True)
        if not representations:
            raise Exception("No face detected in the query image.")
        query_embedding = representations[0]["embedding"]
    except Exception as ex:
        print(f"SCRFD/ArcFace query analysis failed: {ex}")
        return jsonify({"error": f"Face detection failed: {ex}"}), 400
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
    # 3. Retrieve all face records from database and calculate cosine distance
    conn = get_db()
    matching_photos = []
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        cursor.execute("""
            SELECT f.photo_id, f.label, f.embedding
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        db_faces = cursor.fetchall()
        
        matched_photo_ids = set()
        if db_faces:
            try:
                embeddings = []
                face_mapping = []
                for face in db_faces:
                    try:
                        emb = json.loads(face["embedding"])
                        embeddings.append(normalize_embedding(emb))
                        face_mapping.append(face["photo_id"])
                    except Exception:
                        continue
                        
                if embeddings:
                    embeddings_matrix = np.vstack(embeddings).astype(np.float32)
                    
                    # FAISS flat index for Inner Product (Cosine Similarity)
                    index = faiss.IndexFlatIP(512)
                    index.add(embeddings_matrix)
                    
                    query_vector = normalize_embedding(query_embedding).reshape(1, -1)
                    k = len(embeddings)
                    distances, indices = index.search(query_vector, k)
                    
                    # ArcFace similarity threshold (Inner Product >= COSINE_SIM_THRESHOLD matches)
                    for sim, idx in zip(distances[0], indices[0]):
                        if idx != -1 and sim >= COSINE_SIM_THRESHOLD:
                            matched_photo_ids.add(face_mapping[idx])
            except Exception as e:
                print(f"FAISS search-by-face failed: {e}")
                
        if matched_photo_ids:
            # Query photo records for matched IDs
            placeholders = ",".join(["?"] * len(matched_photo_ids))
            query = f"""
                SELECT p.*, GROUP_CONCAT(f.label) as face_labels
                FROM photos p
                LEFT JOIN faces f ON f.photo_id = p.id
                WHERE p.user_id = ? AND p.id IN ({placeholders})
                GROUP BY p.id
                ORDER BY p.id DESC
            """
            cursor.execute(query, [user_id] + list(matched_photo_ids))
            rows = cursor.fetchall()
            
            for r in rows:
                labels = list(set(r["face_labels"].split(","))) if r["face_labels"] else []
                labels = [l for l in labels if l and l != 'None']
                
                # Load face positions and confidence calculations
                cursor.execute("SELECT id, label, embedding, x, y, w, h FROM faces WHERE photo_id = ?", (r["id"],))
                faces = [dict(f) for f in cursor.fetchall()]
                
                matching_photos.append({
                    "id": r["id"],
                    "public_id": r["public_id"],
                    "secure_url": r["secure_url"],
                    "original_filename": r["original_filename"],
                    "upload_date": r["upload_date"],
                    "recognized_person": r["recognized_person"],
                    "created_at": r["created_at"],
                    "labels": labels,
                    "faces": faces
                })
    finally:
        conn.close()
        
    all_faces = []
    for photo in matching_photos:
        all_faces.extend(photo["faces"])
        
    if all_faces:
        calculate_face_confidences(all_faces)
        for face in all_faces:
            if "embedding" in face:
                del face["embedding"]
                
    return jsonify(matching_photos)



@app.route("/api/organize-photos", methods=["POST"])
@login_required
def organize_photos_endpoint():
    conn = get_db()
    copied_count = 0
    created_folders = set()
    user_id = request.user["user_id"]
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.secure_url, p.original_filename, p.event, p.event_occasion, GROUP_CONCAT(f.label) as face_labels
            FROM photos p
            LEFT JOIN faces f ON f.photo_id = p.id
            WHERE p.user_id = ?
            GROUP BY p.id
        """, (user_id,))
        photos = cursor.fetchall()
        
        base_dir = os.path.join(os.getcwd(), "organized_photos")
        people_dir = os.path.join(base_dir, "People")
        events_dir = os.path.join(base_dir, "Events")
        
        os.makedirs(people_dir, exist_ok=True)
        os.makedirs(events_dir, exist_ok=True)
        
        for photo in photos:
            filename = photo["original_filename"]
            secure_url = photo["secure_url"]
            event_name = photo["event"] or "Casual"
            event_occasion = photo["event_occasion"] or "Non_Occasion"
            
            labels_str = photo["face_labels"]
            labels = list(set(labels_str.split(","))) if labels_str else []
            labels = [l for l in labels if l and l != 'None' and l != 'Unknown']
            
            file_bytes = None
            if secure_url.startswith("/static/"):
                local_path = secure_url.lstrip("/")
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        file_bytes = f.read()
            else:
                import requests
                try:
                    r = requests.get(secure_url, timeout=10)
                    if r.status_code == 200:
                        file_bytes = r.content
                except Exception:
                    pass
            
            if not file_bytes:
                continue
                
            # Copy to Event Folder
            safe_event_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in event_name])
            event_folder = os.path.join(events_dir, safe_event_name)
            os.makedirs(event_folder, exist_ok=True)
            created_folders.add(f"Events/{safe_event_name}/")
            with open(os.path.join(event_folder, filename), "wb") as f:
                f.write(file_bytes)
            copied_count += 1
            
            # Copy to People Folders
            for label in labels:
                safe_person_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in label])
                safe_occasion = "".join([c if c.isalnum() or c in " _-" else "_" for c in event_occasion])
                
                person_folder = os.path.join(people_dir, safe_person_name, safe_occasion, safe_event_name)
                os.makedirs(person_folder, exist_ok=True)
                created_folders.add(f"People/{safe_person_name}/{safe_occasion}/{safe_event_name}/")
                with open(os.path.join(person_folder, filename), "wb") as f:
                    f.write(file_bytes)
                copied_count += 1
                
        return jsonify({
            "message": f"Successfully organized photos. Created {copied_count} file copies.",
            "copied_count": copied_count,
            "folders": sorted(list(created_folders))
        })
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        conn.close()


def auto_tune_dbscan(embeddings_matrix):
    from sklearn.metrics import silhouette_score
    from sklearn.cluster import DBSCAN
    
    n_samples = embeddings_matrix.shape[0]
    if n_samples < 3:
        # Not enough samples to tune, return default
        return 0.40
        
    best_eps = 0.40
    best_score = -1.0
    
    # Grid search eps values (ArcFace distance metric threshold range 0.30 - 0.55)
    eps_grid = [0.30, 0.35, 0.38, 0.40, 0.42, 0.45, 0.48, 0.50, 0.55]
    for eps in eps_grid:
        dbscan = DBSCAN(eps=eps, min_samples=1, metric='cosine')
        labels = dbscan.fit_predict(embeddings_matrix)
        
        n_unique_labels = len(set(labels))
        if 1 < n_unique_labels < n_samples:
            try:
                score = silhouette_score(embeddings_matrix, labels, metric='cosine')
                if score > best_score:
                    best_score = score
                    best_eps = eps
            except Exception:
                continue
                
    print(f"Auto-tuned DBSCAN: Selected best eps={best_eps} with Silhouette score={best_score:.4f}")
    return best_eps

@app.route("/api/people/cluster-dbscan", methods=["POST"])
@login_required
def run_dbscan_clustering():
    from sklearn.cluster import DBSCAN, HDBSCAN
    import collections
    
    # 0. Read optional body parameters
    data = request.get_json(silent=True) or {}
    algorithm = data.get("algorithm", "auto").strip().lower() # auto, dbscan, hdbscan
    manual_eps = data.get("eps")
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        
        # 1. Fetch all faces for this user
        cursor.execute("""
            SELECT f.id, f.label, f.embedding, f.photo_id
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        
        if not rows:
            return jsonify({"message": "No faces found in database to cluster.", "clusters_count": 0})
            
        # Parse embeddings
        face_list = []
        embeddings = []
        for r in rows:
            try:
                emb = json.loads(r["embedding"])
                embeddings.append(normalize_embedding(emb))
                face_list.append({
                    "id": r["id"],
                    "label": r["label"],
                    "photo_id": r["photo_id"]
                })
            except Exception:
                continue
                
        if not embeddings:
            return jsonify({"message": "No valid face embeddings found.", "clusters_count": 0})
            
        embeddings_matrix = np.vstack(embeddings).astype(np.float32)
        n_samples = embeddings_matrix.shape[0]
        
        # --- Debugging Logs: Print Pairwise Similarity Scores ---
        print("\n--- DEBUGGING LOGS: Pairwise Cosine Similarity Matrix ---")
        sim_matrix = np.dot(embeddings_matrix, embeddings_matrix.T)
        for i in range(n_samples):
            for j in range(i + 1, n_samples):
                sim = float(sim_matrix[i, j])
                print(f"[Similarity Log] Face ID {face_list[i]['id']} ({face_list[i]['label']}) <-> Face ID {face_list[j]['id']} ({face_list[j]['label']}): similarity={sim:.4f} (distance={1.0 - sim:.4f})")
        print("---------------------------------------------------------\n")
        
        # Determine clustering algorithm to run
        if algorithm == "auto":
            if n_samples >= 6:
                selected_algo = "hdbscan"
            else:
                selected_algo = "dbscan"
        else:
            selected_algo = algorithm
            
        cluster_labels = None
        
        if selected_algo == "hdbscan":
            print("Running HDBSCAN Clustering...")
            try:
                hdb = HDBSCAN(min_cluster_size=2, metric='cosine', min_samples=1)
                cluster_labels = hdb.fit_predict(embeddings_matrix)
                print(f"HDBSCAN raw labels: {cluster_labels}")
            except Exception as hdb_err:
                print(f"HDBSCAN failed: {hdb_err}, falling back to DBSCAN")
                selected_algo = "dbscan"
                
        if selected_algo == "dbscan":
            if manual_eps is not None:
                eps = float(manual_eps)
                print(f"Running DBSCAN with manual eps={eps}...")
            else:
                eps = auto_tune_dbscan(embeddings_matrix)
                print(f"Running DBSCAN with auto-tuned eps={eps}...")
                
            dbscan = DBSCAN(eps=eps, min_samples=1, metric='cosine')
            cluster_labels = dbscan.fit_predict(embeddings_matrix)
            print(f"DBSCAN labels: {cluster_labels}")
            
        # Group face indices by cluster label
        clusters = collections.defaultdict(list)
        
        # For HDBSCAN, noise points are labeled -1. Assign each to its own unique singleton cluster
        next_fake_lbl = max(cluster_labels) + 1 if len(cluster_labels) > 0 else 1
        for idx, cl_lbl in enumerate(cluster_labels):
            if cl_lbl == -1:
                cl_lbl = next_fake_lbl
                next_fake_lbl += 1
            clusters[cl_lbl].append(face_list[idx])
            
        cursor.execute("SELECT name FROM people WHERE user_id = ?", (user_id,))
        existing_names = set([row["name"] for row in cursor.fetchall()])
        
        person_counter = 1
        updated_count = 0
        new_names_created = []
        
        assigned_labels = set()
        cluster_assignments = []
        
        manual_people = set()
        for name in existing_names:
            if not re.match(r"^Person_\d+$", name) and name != "Unknown":
                manual_people.add(name)
                
        unassigned_clusters = []
        for cl_lbl, cluster_faces in clusters.items():
            manual_labels_in_cluster = [f["label"] for f in cluster_faces if f["label"] in manual_people]
            if manual_labels_in_cluster:
                final_label = collections.Counter(manual_labels_in_cluster).most_common(1)[0][0]
                cluster_assignments.append((cluster_faces, final_label))
                assigned_labels.add(final_label)
            else:
                unassigned_clusters.append(cluster_faces)
                
        for cluster_faces in unassigned_clusters:
            old_auto_labels = [f["label"] for f in cluster_faces if re.match(r"^Person_\d+$", f["label"])]
            final_label = None
            if old_auto_labels:
                for candidate in old_auto_labels:
                    if candidate not in assigned_labels:
                        final_label = candidate
                        break
            if final_label is None:
                while True:
                    candidate = f"Person_{person_counter}"
                    if candidate not in existing_names and candidate not in assigned_labels:
                        final_label = candidate
                        break
                    person_counter += 1
            cluster_assignments.append((cluster_faces, final_label))
            assigned_labels.add(final_label)
            
        for cluster_faces, final_label in cluster_assignments:
            for face in cluster_faces:
                if face["label"] != final_label:
                    cursor.execute("UPDATE faces SET label = ? WHERE id = ?", (final_label, face["id"]))
                    updated_count += 1
            cursor.execute("SELECT id FROM people WHERE user_id = ? AND name = ?", (user_id, final_label))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO people (user_id, name) VALUES (?, ?)", (user_id, final_label))
                new_names_created.append(final_label)
                
        # 4. Synchronize photos recognized_person tags for the current user
        cursor.execute("SELECT id FROM photos WHERE user_id = ?", (user_id,))
        photos = cursor.fetchall()
        for p in photos:
            cursor.execute("SELECT label FROM faces WHERE photo_id = ? AND label != 'Unknown'", (p["id"],))
            labels = list(set([row[0] for row in cursor.fetchall()]))
            if labels:
                cursor.execute("UPDATE photos SET recognized_person = ? WHERE id = ?", (", ".join(labels), p["id"]))
            else:
                cursor.execute("UPDATE photos SET recognized_person = NULL WHERE id = ?", (p["id"],))
                
        conn.commit()
        
        msg = f"Clustering complete ({selected_algo.upper()}). Updated {updated_count} face labels. Grouped faces into {len(clusters)} cluster(s)."
        if selected_algo == "dbscan" and manual_eps is None:
            msg += f" (Auto-tuned eps={eps:.3f})"
            
        return jsonify({
            "message": msg,
            "algorithm": selected_algo,
            "clusters_count": len(clusters),
            "updated_count": updated_count,
            "new_names_created": new_names_created
        })
        
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        conn.close()

@app.route("/api/people/clustering-evaluation", methods=["GET"])
@login_required
def evaluate_clustering():
    from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
    import collections
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        cursor.execute("""
            SELECT f.id, f.label, f.embedding
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        
        if not rows:
            return jsonify({"error": "No faces found in database to evaluate."}), 400
            
        embeddings = []
        labels = []
        for r in rows:
            try:
                emb = json.loads(r["embedding"])
                embeddings.append(normalize_embedding(emb))
                labels.append(r["label"])
            except Exception:
                continue
                
        if len(embeddings) < 3:
            return jsonify({
                "message": "Not enough samples to run evaluation. Need at least 3 valid face records.",
                "total_faces": len(embeddings)
            })
            
        embeddings_matrix = np.vstack(embeddings).astype(np.float32)
        
        # Count clusters
        lbl_counts = collections.Counter(labels)
        n_clusters = len(lbl_counts)
        
        unique_labels = list(set(labels))
        n_unique = len(unique_labels)
        
        silhouette = None
        db_index = None
        ch_index = None
        
        # Map labels to integers for metrics
        label_map = {lbl: idx for idx, lbl in enumerate(unique_labels)}
        int_labels = np.array([label_map[l] for l in labels])
        
        if 1 < n_unique < len(embeddings):
            try:
                silhouette = float(silhouette_score(embeddings_matrix, int_labels, metric='cosine'))
                db_index = float(davies_bouldin_score(embeddings_matrix, int_labels))
                ch_index = float(calinski_harabasz_score(embeddings_matrix, int_labels))
            except Exception as e:
                print(f"Failed to calculate metrics: {e}")
                
        # Calculate cluster cohesion (average pairwise similarity within clusters)
        cohesions = {}
        for lbl in unique_labels:
            indices = [idx for idx, l in enumerate(labels) if l == lbl]
            if len(indices) > 1:
                group_embs = embeddings_matrix[indices]
                sim_matrix = np.dot(group_embs, group_embs.T)
                n = len(indices)
                avg_sim = float((np.sum(sim_matrix) - n) / (n * (n - 1)))
                cohesions[lbl] = round(avg_sim, 4)
            else:
                cohesions[lbl] = 1.0
                
        return jsonify({
            "total_faces": len(embeddings),
            "clusters_count": n_clusters,
            "silhouette_score": silhouette,
            "davies_bouldin_index": db_index,
            "calinski_harabasz_index": ch_index,
            "cluster_sizes": dict(lbl_counts),
            "cluster_cohesions": cohesions
        })
    finally:
        conn.close()

@app.route("/api/people/merge-clusters", methods=["POST"])
@login_required
def merge_clusters():
    data = request.get_json(silent=True) or {}
    src_label = data.get("src_label", "").strip()
    dest_label = data.get("dest_label", "").strip()
    
    if not src_label or not dest_label:
        return jsonify({"error": "Missing src_label or dest_label"}), 400
        
    if src_label == dest_label:
        return jsonify({"error": "Source and destination labels cannot be the same"}), 400
        
    conn = get_db()
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        
        # Verify both labels exist in faces belonging to current user
        cursor.execute("""
            SELECT COUNT(*) FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ? AND f.label = ?
        """, (user_id, src_label))
        src_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ? AND f.label = ?
        """, (user_id, dest_label))
        dest_count = cursor.fetchone()[0]
        
        if src_count == 0:
            return jsonify({"error": f"Source cluster '{src_label}' not found or empty."}), 404
        if dest_count == 0:
            return jsonify({"error": f"Destination cluster '{dest_label}' not found or empty."}), 404
            
        # Update labels in faces for this user's photos
        cursor.execute("""
            UPDATE faces
            SET label = ?
            WHERE label = ? AND id IN (
                SELECT f.id FROM faces f
                JOIN photos p ON f.photo_id = p.id
                WHERE p.user_id = ?
            )
        """, (dest_label, src_label, user_id))
        
        # Delete src_label from people for this user
        cursor.execute("DELETE FROM people WHERE user_id = ? AND name = ?", (user_id, src_label))
        
        # Ensure dest_label is in people for this user
        cursor.execute("SELECT id FROM people WHERE user_id = ? AND name = ?", (user_id, dest_label))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO people (user_id, name) VALUES (?, ?)", (user_id, dest_label))
            
        # Re-sync recognized_person in photos for this user
        cursor.execute("SELECT id FROM photos WHERE user_id = ?", (user_id,))
        photos = cursor.fetchall()
        for p in photos:
            cursor.execute("SELECT label FROM faces WHERE photo_id = ? AND label != 'Unknown'", (p["id"],))
            labels = list(set([row[0] for row in cursor.fetchall()]))
            if labels:
                cursor.execute("UPDATE photos SET recognized_person = ? WHERE id = ?", (", ".join(labels), p["id"]))
            else:
                cursor.execute("UPDATE photos SET recognized_person = NULL WHERE id = ?", (p["id"],))
                
        conn.commit()
        return jsonify({
            "message": f"Successfully merged cluster '{src_label}' into '{dest_label}'. Updated {src_count} faces.",
            "merged_count": src_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/people/split-cluster", methods=["POST"])
@login_required
def split_cluster():
    data = request.get_json(silent=True) or {}
    face_ids = data.get("face_ids", [])
    new_label = data.get("new_label", "").strip()
    
    if not face_ids or not new_label:
        return jsonify({"error": "Missing face_ids or new_label"}), 400
        
    conn = get_db()
    try:
        cursor = conn.cursor()
        user_id = request.user["user_id"]
        
        # Verify face_ids exist and belong to current user
        placeholders = ",".join(["?"] * len(face_ids))
        cursor.execute(f"""
            SELECT COUNT(*) FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE p.user_id = ? AND f.id IN ({placeholders})
        """, [user_id] + list(face_ids))
        count = cursor.fetchone()[0]
        
        if count != len(face_ids):
            return jsonify({"error": "One or more face IDs are invalid or unauthorized."}), 404
            
        # Update labels of these face_ids
        cursor.execute(f"UPDATE faces SET label = ? WHERE id IN ({placeholders})", [new_label] + list(face_ids))
        
        # Insert new_label into people for this user if not exists
        cursor.execute("SELECT id FROM people WHERE user_id = ? AND name = ?", (user_id, new_label))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO people (user_id, name) VALUES (?, ?)", (user_id, new_label))
            
        # Re-sync recognized_person in photos for this user
        cursor.execute("SELECT id FROM photos WHERE user_id = ?", (user_id,))
        photos = cursor.fetchall()
        for p in photos:
            cursor.execute("SELECT label FROM faces WHERE photo_id = ? AND label != 'Unknown'", (p["id"],))
            labels = list(set([row[0] for row in cursor.fetchall()]))
            if labels:
                cursor.execute("UPDATE photos SET recognized_person = ? WHERE id = ?", (", ".join(labels), p["id"]))
            else:
                cursor.execute("UPDATE photos SET recognized_person = NULL WHERE id = ?", (p["id"],))
                
        conn.commit()
        return jsonify({
            "message": f"Successfully split {len(face_ids)} faces into new cluster '{new_label}'.",
            "split_count": len(face_ids)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/organized_photos/<path:filename>")
def organized_photo(filename):
    return send_from_directory(
        os.path.join(app.root_path, "organized_photos"),
        filename
    )


@app.route("/api/organized", methods=["GET"])
@login_required
def organized():
    root = os.path.join(app.root_path, "organized_photos")

    if not os.path.exists(root):
        return jsonify([])

    return jsonify(build_tree(root, ""))


def build_tree(path, relative_path):
    nodes = []

    for name in sorted(os.listdir(path)):
        full_path = os.path.join(path, name)

        if os.path.isdir(full_path):
            nodes.append({
                "type": "folder",
                "name": name,
                "children": build_tree(
                    full_path,
                    os.path.join(relative_path, name)
                )
            })

        else:
            if name.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                nodes.append({
                    "type": "photo",
                    "name": name,
                    "url": "/organized_photos/" +
                           os.path.join(relative_path, name)
                           .replace("\\", "/")
                })

    return nodes

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

