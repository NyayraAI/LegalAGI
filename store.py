# from sentence_transformers import SentenceTransformer
# from supabase_client import supabase
# import json

# # Load the MiniLM model
# model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# # Load your JSON data
# with open('data/bare_acts.json', 'r', encoding='utf-8') as f:
#     docs = json.load(f)

# # Go through each document
# for doc in docs:
#     content = doc["content"]
    
#     # Optional: Chunk long content (here, skipping for simplicity)
#     # Get embedding
#     embedding = model.encode(content).tolist()
    
#     # Insert into Supabase
#     try:
#         response = supabase.table("documents").insert({
#             "content": content,
#             "embedding": embedding
#         }).execute()
#         print("✅ Inserted:", content[:60], "...")
#     except Exception as e:
#         print("❌ Error inserting:", e)

import os
import json
from pathlib import Path
from utils.supabase_client import supabase, TABLE_NAME
from utils.embed import embed_text

DATA_FOLDER = "data"

def load_documents_from_json(folder_path):
    documents = []
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            file_path = os.path.join(folder_path, file)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    text = item.get("text") or item.get("section") or ""
                    if text:
                        documents.append({
                            "text": text,
                            "source": file,
                        })
    return documents

def store_embeddings(documents):
    for doc in documents:
        try:
            vector = embed_text(doc["text"])
            response = supabase.table(TABLE_NAME).insert({
                "content": doc["text"],
                "source": doc["source"],
                "embedding": vector,
            }).execute()
            print(f"✅ Stored: {doc['text'][:50]}...")
        except Exception as e:
            print(f"❌ Failed to store: {e}")

if __name__ == "__main__":
    print("📦 Loading documents from:", DATA_FOLDER)
    docs = load_documents_from_json(DATA_FOLDER)
    print(f"🔢 Total documents: {len(docs)}")

    print("🧠 Generating and storing embeddings...")
    store_embeddings(docs)
