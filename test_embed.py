import os
import sys

print("🚀 Starting test...")
print("🔑 API KEY:", os.getenv("GROQ_API_KEY"))

# Test imports first
try:
    print("📦 Testing sentence_transformers import...")
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers imported successfully")
except ImportError as e:
    print("❌ ImportError:", e)
    print("💡 Install with: pip install sentence-transformers")
    sys.exit(1)
except Exception as e:
    print("❌ Unexpected error importing sentence_transformers:", e)
    sys.exit(1)

# Test utils.embed import
try:
    print("📦 Testing utils.embed import...")
    from utils.embed import embed_question
    print("✅ utils.embed imported successfully")
except ImportError as e:
    print("❌ ImportError:", e)
    print("💡 Check if utils/embed.py exists and utils/__init__.py is present")
    sys.exit(1)
except Exception as e:
    print("❌ Unexpected error importing utils.embed:", e)
    sys.exit(1)

# Test embedding
print("🔄 Creating embedding...")
question = "What is the punishment for theft under Indian Penal Code?"

try:
    embedding = embed_question(question)
    
    if embedding:
        print("✅ Embedding created successfully!")
        print(f"📊 Embedding length: {len(embedding)}")
        print("🔢 First 10 values:", embedding[:10])
    else:
        print("❌ Embedding is empty - check embed.py for errors")
        
except Exception as e:
    print("❌ Error during embedding:", e)
    import traceback
    traceback.print_exc()

print("🏁 Test completed!")