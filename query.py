from utils.embed import embed_text
from utils.supabase_client import supabase, TABLE_NAME

def query_legal_docs(question: str, match_count: int = 5):
    print(f"\n🔍 Querying for: '{question}'")

    # Step 1: Get embedding of the question
    query_embedding = embed_text(question)
    if not query_embedding:
        print("❌ Failed to create embedding for the question.")
        return []

    # Step 2: Perform similarity search in Supabase
    try:
        response = supabase.rpc("match_documents", {
            "match_count": 5,
            "match_threshold": 0.75,
            "query_embedding": query_embedding
        }).execute()

        matches = response.data
        if not matches:
            print("⚠️ No matches found.")
            return []

        print(f"✅ Found {len(matches)} match(es):\n")
        for i, match in enumerate(matches, 1):
            print(f"{i}. Score: {match['similarity']:.4f}")
            print(f"   Text: {match['content'][:200]}...\n")

        return matches

    except Exception as e:
        print("❌ Query error:", e)
        import traceback
        traceback.print_exc()
        return []

# Run the query directly from CLI (for testing)
if __name__ == "__main__":
    question_input = input("📝 Ask your legal question: ")
    query_legal_docs(question_input)
