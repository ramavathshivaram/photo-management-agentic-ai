import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests
import os

def main():
    model_name = "openai/clip-vit-base-patch32"
    print("Loading CLIP model and processor...")
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    print("CLIP model loaded successfully.")

    # Candidate classes
    classes = [
        "Wedding",
        "Birthday",
        "Engagement",
        "Reception",
        "Graduation",
        "Festival",
        "Religious Event",
        "Office Event",
        "Travel",
        "Casual",
        "Selfie",
        "Daily Life"
    ]
    prompts = [f"a photo of a {c}" for c in classes]

    # Test image (mom portrait)
    img_path = r"C:\Users\dsris\.gemini\antigravity\brain\b2e17b5a-3d4f-4514-97cb-7b4a738e703e\mom_portrait_1780978014989.png"
    if not os.path.exists(img_path):
        print(f"Image not found at {img_path}")
        return

    image = Image.open(img_path).convert("RGB")
    
    print("Processing image and text...")
    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
        probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get probabilities
        
    print("\nClassification results:")
    for c, p in zip(classes, probs[0]):
        print(f"{c}: {p.item() * 100:.2f}%")

    best_idx = probs.argmax().item()
    best_class = classes[best_idx]
    best_prob = probs[0][best_idx].item()
    print(f"\nBest predicted class: {best_class} ({best_prob * 100:.2f}%)")

if __name__ == "__main__":
    main()
