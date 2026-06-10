import os
import cv2
import numpy as np
from deepface import DeepFace

def main():
    test_img_path = os.path.join("assets", "priya.png")
    if not os.path.exists(test_img_path):
        print(f"Test image not found at {test_img_path}")
        return
        
    img = cv2.imread(test_img_path)
    if img is None:
        print("Failed to read image with OpenCV")
        return
        
    # Priya's bbox coordinates from previous output:
    # upper_left=(373.87, 150.39), lower_right=(648.63, 532.20)
    x1, y1 = 373, 150
    x2, y2 = 648, 532
    
    # Crop the face
    cropped_face = img[y1:y2, x1:x2]
    
    print(f"Cropped face shape: {cropped_face.shape}")
    
    try:
        print("Running DeepFace.represent with detector_backend='skip'...")
        representations = DeepFace.represent(
            img_path=cropped_face,
            model_name="ArcFace",
            detector_backend="skip"
        )
        print(f"Success! Got {len(representations)} representation(s).")
        emb = representations[0]["embedding"]
        print(f"Embedding length: {len(emb)}")
        print(f"First 5 elements: {emb[:5]}")
    except Exception as e:
        print(f"DeepFace.represent failed: {e}")

if __name__ == "__main__":
    main()
