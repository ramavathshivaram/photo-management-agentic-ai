import os
import cv2
import numpy as np
from PIL import Image
import scrfd

def main():
    model_path = os.path.join("assets", "models", "scrfd_2.5g_bnkps.onnx")
    detector = scrfd.SCRFD.from_path(model_path)
    
    img_path = os.path.join("assets", "priya.png")
    img_cv = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    
    faces = detector.detect(img_pil)
    print(f"Found {len(faces)} face(s).")
    
    if not faces:
        return
        
    face = faces[0]
    kps = face.keypoints
    
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
        aligned_face = cv2.warpAffine(img_cv, M, (112, 112))
        print(f"Aligned face shape: {aligned_face.shape}")
        # Save aligned face for inspection
        os.makedirs("scratch", exist_ok=True)
        cv2.imwrite("scratch/priya_aligned.png", aligned_face)
        print("Saved aligned face to scratch/priya_aligned.png")
    else:
        print("Failed to estimate affine transformation matrix.")

if __name__ == "__main__":
    main()
