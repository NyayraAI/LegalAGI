from sentence_transformers import SentenceTransformer
import os
import asyncio
import concurrent.futures

print("🔄 Loading SentenceTransformer model...")

# Load the model once at the top
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model = None

def embed_text(text: str) -> list:
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

async def embed_text_async(text: str) -> list:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        # Fix: Call embed_text, not embed_text_async (which would cause infinite recursion)
        return await loop.run_in_executor(pool, embed_text, text)