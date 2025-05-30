from sentence_transformers import SentenceTransformer
import os

print("🔄 Loading SentenceTransformer model...")

# Load the model once at the top
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model = None

def embed_question(text: str) -> list:
    if model is None:
        print("❌ Model not loaded, cannot create embedding")
        return []
    
    try:
        print(f"🔄 Creating embedding for: '{text[:50]}...'")
        embedding = model.encode(text)
        print(f"✅ Embedding created with shape: {embedding.shape}")
        return embedding.tolist()
    except Exception as e:
        print("❌ Local embedding error:", e)
        import traceback
        traceback.print_exc()
        return []