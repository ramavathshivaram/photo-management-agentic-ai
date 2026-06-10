import os
import urllib.request
import time
from PIL import Image
import scrfd

def download_model(url, save_path):
    if os.path.exists(save_path):
        print(f"Model already exists at {save_path}")
        return
    print(f"Downloading model from {url}...")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    start_time = time.time()
    urllib.request.urlretrieve(url, save_path)
    duration = time.time() - start_time
    print(f"Downloaded model to {save_path} in {duration:.2f} seconds.")

def main():
    model_url = "https://huggingface.co/RuteNL/SCRFD-face-detection-ONNX/resolve/main/2.5g_bnkps.onnx"
    model_path = os.path.join("assets", "models", "scrfd_2.5g_bnkps.onnx")
    
    download_model(model_url, model_path)
    
    print("Initializing SCRFD detector...")
    detector = scrfd.SCRFD.from_path(model_path)
    print("Detector initialized successfully.")
    
    test_img_path = os.path.join("assets", "priya.png")
    if not os.path.exists(test_img_path):
        print(f"Test image not found at {test_img_path}")
        return
        
    print(f"Opening test image: {test_img_path}")
    image = Image.open(test_img_path).convert("RGB")
    
    print("Running face detection...")
    faces = detector.detect(image)
    print(f"Detection finished. Found {len(faces)} face(s).")
    
    for idx, face in enumerate(faces):
        bbox = face.bbox
        prob = face.probability
        print(f"Face {idx}: probability={prob:.4f}")
        print(f"  bbox: upper_left=({bbox.upper_left.x}, {bbox.upper_left.y}), lower_right=({bbox.lower_right.x}, {bbox.lower_right.y})")
        if face.keypoints:
            print(f"  keypoints: {len(face.keypoints)} points")

if __name__ == "__main__":
    main()
