import asyncio
import concurrent.futures
import numpy as np
from loguru import logger
from typing import List, Dict, Any, Optional

from app.dependencies import (
    get_app_config,
    get_data_loader,
    get_embedding_store_instance,
    check_embeddings_exist,
    search_stored_embeddings_async,
    embed_text_async,
    get_supabase_client,
    generate_query_hash,
)

# Initialize dependencies
config = get_app_config()
data_loader = get_data_loader()
embedding_store = get_embedding_store_instance()
supabase = get_supabase_client()


async def get_or_create_embedding(
    text: str, use_storage: bool = True, store_key: Optional[str] = None
) -> List[float]:
    """Get or create embedding with storage only (no cache)"""

    # 1. Check persistent store
    if use_storage and embedding_store:
        query_hash = generate_query_hash(text)
        if check_embeddings_exist(query_hash):
            stored_results = await search_stored_embeddings_async(
                text, top_k=1, threshold=0.99
            )
            if stored_results:
                embedding = stored_results[0].get("embedding")
                if embedding:
                    return embedding

    # 2. Generate new embedding
    # Only allow storing if this is a document (not a question)
    is_document = bool(store_key) and len(text) > 100 and not text.strip().endswith("?")
    embedding = await embed_text_async(text)

    if embedding:
        # Only store if is_document
        if is_document and use_storage:
            # Re-embed with store_key to trigger storage if needed
            await embed_text_async(text, store_key or "")
    return embedding or []


async def fetch_matches(embedding: List[float]) -> Dict[str, Any]:
    """Hybrid approach to find matching documents"""
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, _search_hybrid, embedding)


def _search_hybrid(embedding: List[float]) -> Dict[str, Any]:
    """
    SIMPLE FIX: Only search document content, ignore user questions
    """
    results = {
        "embedding_matches": [],
        "total_matches": 0,
        "search_method": "documents_only",
    }

    try:
        # Get your existing embedding store
        embedding_store = get_embedding_store_instance()
        if not embedding_store:
            logger.error("❌ No embedding store available")
            return results

        # Debug: Print number of embeddings in the store (if possible)
        try:
            stats = embedding_store.get_embedding_stats()
            logger.info(f"[DEBUG] Embedding store stats: {stats}")
        except Exception as e:
            logger.warning(f"[DEBUG] Could not get embedding stats: {e}")

        # Search with lower threshold
        all_matches = embedding_store.search_embeddings(
            np.array(embedding),
            top_k=20,
            threshold=0.3,  # Lower threshold for more matches
        )

        # Debug: Print number of matches before filtering
        logger.info(f"[DEBUG] Raw matches found: {len(all_matches)}")
        for i, match in enumerate(all_matches[:5]):
            sim = match.get("similarity", None)
            content = match.get("content", "")
            logger.info(f"[DEBUG] Match {i+1}: sim={sim}, preview='{content[:80]}'")

        # Improved filter: Only skip if it is a user question (store_key present AND content is short AND ends with '?')
        document_matches = []
        for match in all_matches:
            content = match.get("content", "").strip()
            store_key = match.get("metadata", {}).get("store_key")
            # Only skip if store_key is present AND content is short AND ends with '?'
            if store_key and len(content) < 100 and content.endswith("?"):
                continue
            # Skip if content is empty
            if not content:
                continue
            # This is actual document content - keep it
            document_matches.append(match)
            # Stop when we have enough good matches
            if len(document_matches) >= 10:
                break

        results["embedding_matches"] = document_matches
        results["total_matches"] = len(document_matches)

        logger.info(
            f"🎯 Found {len(document_matches)} document chunks from {len(all_matches)} total matches"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return results


# FIXED: Add a method to check what's actually stored
async def debug_stored_embeddings():
    """Debug what's actually stored in your embedding store"""
    try:
        store = get_embedding_store_instance()
        if not store:
            return {"error": "No embedding store available"}

        # Get all stored embeddings
        stats = store.get_embedding_stats()

        # Try to get some sample embeddings
        sample_embeddings = []

        dummy_embedding = np.random.random(384)  # Adjust dimension as needed

        try:
            all_matches = store.search_embeddings(
                dummy_embedding, top_k=50, threshold=0.0
            )

            for match in all_matches:
                content = match.get("content", "")
                sample_embeddings.append(
                    {
                        "content_preview": content[:100],
                        "content_length": len(content),
                        "is_question_like": len(content) < 100 and "?" in content,
                        "metadata": match.get("metadata", {}),
                        "id": match.get("id", "No ID"),
                    }
                )

        except Exception as e:
            logger.warning(f"Could not retrieve sample embeddings: {e}")

        return {
            "stats": stats,
            "sample_count": len(sample_embeddings),
            "samples": sample_embeddings[:10],  # First 10 samples
            "document_count": len(
                [s for s in sample_embeddings if not s["is_question_like"]]
            ),
            "question_count": len(
                [s for s in sample_embeddings if s["is_question_like"]]
            ),
        }

    except Exception as e:
        logger.error(f"❌ Error debugging stored embeddings: {e}")
        return {"error": str(e)}


# Add proper document indexing method
async def index_documents_properly():
    from datetime import datetime
    from utils.processing.chunker import PDFProcessor
    import os

    """Properly index your documents for RAG"""
    try:
        logger.info("🔄 Starting proper document indexing from raw PDFs...")

        # Re-chunk and re-embed all PDFs, forcing overwrite
        processor = PDFProcessor()
        processor.process_all_pdfs(force=True)

        # Optionally, reload chunks to report stats
        data_loader._chunks = None
        chunks = data_loader.load_all_chunks()
        logger.info(f"📚 Re-chunked and indexed {len(chunks)} chunks from PDFs")

        return {
            "success": True,
            "indexed_count": len(chunks),
            "source": "raw_pdfs",
        }
    except Exception as e:
        logger.error(f"❌ Error indexing documents: {e}")
        return {"error": str(e)}


async def sync_embeddings():
    """Synchronize all local embeddings to the remote database (if in sync/database mode)"""
    from utils.data.local_embedding_store import LocalEmbeddingStore
    from utils.data.database_embedding_store import DatabaseEmbeddingStore
    from utils.data.sync_embedding_store import SyncEmbeddingStore
    import numpy as np

    store = get_embedding_store_instance()
    if not store:
        return {"error": "No embedding store available"}

    # Only proceed if using sync or database mode
    if not (config.is_sync_storage() or config.is_database_storage()):
        return {"error": "Sync only supported in sync/database mode"}

    # Get local and remote stores
    if isinstance(store, SyncEmbeddingStore):
        local_store = store.local_store
        db_store = store.db_store
        if db_store is None:
            return {
                "error": "Remote database store is not configured. Please check your SUPABASE_URL and SUPABASE_KEY."
            }
    elif isinstance(store, LocalEmbeddingStore):
        return {"error": "No remote store configured (local mode)"}
    elif isinstance(store, DatabaseEmbeddingStore):
        return {"message": "Already using database as primary store"}
    else:
        return {"error": "Unknown embedding store type"}

    synced = 0
    failed = 0
    already_synced = 0

    # Iterate over all local chunks/embeddings
    for file_path, meta in local_store.metadata.items():
        print(f"[SYNC] Checking if {file_path} exists in remote DB...")
        exists = db_store.embedding_exists(file_path)
        print(f"[SYNC] Exists? {exists}")
        if exists:
            print(f"[SYNC] Skipping {file_path} (already synced)")
            already_synced += 1
            continue
        # Try to upload
        try:
            print(f"[SYNC] Syncing {file_path}...")
            start_idx = meta["start_idx"]
            end_idx = meta["end_idx"]
            chunks = [c for c in local_store.chunks if c.get("file_path") == file_path]
            embeddings = local_store.embeddings[start_idx : end_idx + 1]
            success = db_store.store_embeddings(embeddings, chunks, meta)
            if success:
                print(f"[SYNC] Synced {file_path} successfully.")
                synced += 1
            else:
                print(f"[SYNC] Failed to sync {file_path}.")
                failed += 1
        except Exception as e:
            failed += 1
            logger.error(f"❌ Failed to sync {file_path}: {e}")

    return {
        "synced": synced,
        "already_synced": already_synced,
        "failed": failed,
        "status": "success" if failed == 0 else "partial",
    }
