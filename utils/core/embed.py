import asyncio
import concurrent.futures
import traceback
from typing import List, Dict, Any, Optional, Union
from functools import lru_cache

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from utils.core.config import get_config
from utils.data.local_embedding_store import LocalEmbeddingStore
from utils.data.sync_embedding_store import SyncEmbeddingStore

# Global model instance (lazy loaded)
_model = None
_embedding_store = None


def _get_model() -> Optional[SentenceTransformer]:
    """Lazy load the SentenceTransformer model"""
    global _model
    if _model is None:
        try:
            logger.info("Loading SentenceTransformer model...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Model loaded successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            _model = None
    return _model


@lru_cache(maxsize=1)
def get_embedding_store():
    """Get embedding store with caching and detailed error logging"""
    global _embedding_store
    if _embedding_store is not None:
        return _embedding_store

    try:
        config = get_config()
        logger.info(f"🔧 Config loaded - Storage mode: {config.embedding_storage}")

        # Initialize local store
        local_store_config = {"path": config.embedding_db_path}
        local_store = LocalEmbeddingStore(local_store_config)
        logger.info(
            f"✅ Local embedding store initialized at: {config.embedding_db_path}"
        )

        if config.is_sync_storage():
            logger.info("🔄 Setting up sync storage mode")
            db_store = None

            if config.has_database_config():
                try:
                    logger.info("🔧 Attempting to initialize database store...")
                    from utils.data.database_embedding_store import (
                        DatabaseEmbeddingStore,
                    )

                    if not hasattr(config, "supabase_key") or not config.supabase_key:
                        logger.warning("⚠️  Missing supabase_key for database store")
                    else:
                        db_store = DatabaseEmbeddingStore(
                            {"url": config.supabase_url, "key": config.supabase_key}
                        )
                        logger.info("✅ Database embedding store initialized")
                except ImportError as e:
                    logger.warning(f"📦 Database embedding store import failed: {e}")
                except Exception as e:
                    logger.warning(f"❌ Database embedding store init failed: {e}")
            else:
                logger.info("ℹ️  No database config found, using local store only")

            _embedding_store = SyncEmbeddingStore(local_store, db_store)
            logger.info("✅ Sync embedding store initialized")

        elif config.is_local_storage():
            logger.info("💾 Using local storage mode")
            _embedding_store = local_store
        else:  # database mode
            logger.info("🗄️  Using database storage mode")
            if config.has_database_config():
                try:
                    from utils.data.database_embedding_store import (
                        DatabaseEmbeddingStore,
                    )

                    if not hasattr(config, "supabase_key") or not config.supabase_key:
                        logger.error("❌ Missing supabase_key for database mode")
                        logger.info("🔄 Falling back to local storage")
                        _embedding_store = local_store
                    else:
                        _embedding_store = DatabaseEmbeddingStore(
                            {"url": config.supabase_url, "key": config.supabase_key}
                        )
                        logger.info("✅ Database embedding store initialized")
                except Exception as e:
                    logger.error(f"❌ Database mode failed: {e}")
                    logger.info("🔄 Falling back to local storage")
                    _embedding_store = local_store
            else:
                logger.info("ℹ️  No database config, using local storage")
                _embedding_store = local_store

        return _embedding_store

    except Exception as e:
        logger.error(f"❌ Critical error in get_embedding_store: {e}")
        logger.error(f"📍 Error type: {type(e).__name__}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        raise


def embed_text(text: str, store_key: Optional[str] = None) -> list:
    """
    Create embedding for text and optionally store it

    Args:
        text: Text to embed
        store_key: Optional key for storage (e.g., file path or chunk ID)

    Returns:
        List representation of embedding vector
    """
    model = _get_model()
    if model is None:
        logger.error("❌ Model not loaded, cannot create embedding")
        return []

    try:
        logger.debug(f"🔄 Creating embedding for: '{text[:50]}...'")
        embedding = model.encode(text)
        logger.debug(f"✅ Embedding created with shape: {embedding.shape}")

        # Only store if this is a document (not a question)
        is_document = (
            bool(store_key) and len(text) > 100 and not text.strip().endswith("?")
        )
        if store_key and is_document:
            store_single_embedding(np.array(embedding), text, store_key)

        return embedding.tolist()
    except Exception as e:
        logger.error(f"❌ Local embedding error: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return []


def embed_texts_batch(
    texts: List[str],
    chunks: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    store_results: bool = False,
) -> List[list]:
    """
    Create embeddings for multiple texts and optionally store them

    Args:
        texts: List of texts to embed
        chunks: Optional list of chunk metadata (must match texts length)
        metadata: Optional metadata for storage (e.g., file info)
        store_results: Whether to store embeddings after generation

    Returns:
        List of embedding vectors
    """
    model = _get_model()
    if model is None:
        logger.error("❌ Model not loaded, cannot create embeddings")
        return []

    try:
        logger.info(f"🔄 Creating embeddings for {len(texts)} texts...")
        embeddings = model.encode(texts)
        logger.info(f"✅ {len(embeddings)} embeddings created")

        if store_results and metadata:
            store_embeddings_batch(embeddings, texts, chunks, metadata)

        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.error(f"❌ Batch embedding error: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return []


def store_single_embedding(
    embedding: np.ndarray,
    text: str,
    store_key: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Store a single embedding

    Args:
        embedding: Embedding vector
        text: Original text
        store_key: Storage key (e.g., file path or chunk ID)
        metadata: Optional metadata

    Returns:
        True if stored successfully
    """
    try:
        store = get_embedding_store()
        if store is None:
            logger.error("❌ No embedding store available")
            return False

        chunk = {
            "content": text,
            "id": store_key,
            "metadata": {"store_key": store_key, "text_length": len(text)},
        }

        if metadata is None:
            metadata = {
                "file_path": store_key,
                "chunk_count": 1,
                "source": "single_embed",
            }

        success = store.store_embeddings([embedding], [chunk], metadata)
        if success:
            logger.debug(f"✅ Embedding stored for key: {store_key}")
        else:
            logger.error(f"❌ Failed to store embedding for key: {store_key}")

        return success

    except Exception as e:
        logger.error(f"❌ Error storing single embedding: {e}")
        return False


def store_embeddings_batch(
    embeddings: Union[List[np.ndarray], np.ndarray],
    texts: List[str],
    chunks: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Store multiple embeddings

    Args:
        embeddings: List of embedding vectors or numpy array
        texts: List of original texts
        chunks: Optional list of chunk metadata
        metadata: Optional metadata for storage

    Returns:
        True if stored successfully
    """
    try:
        store = get_embedding_store()
        if store is None:
            logger.error("❌ No embedding store available")
            return False

        # Normalize embeddings to list of numpy arrays
        if isinstance(embeddings, np.ndarray):
            embeddings = [embeddings[i] for i in range(len(embeddings))]
        else:
            embeddings = [
                np.array(emb) if not isinstance(emb, np.ndarray) else emb
                for emb in embeddings
            ]

        # Create chunks if not provided
        if chunks is None:
            chunks = [
                {
                    "content": text,
                    "id": f"chunk_{i}",
                    "metadata": {"chunk_index": i, "text_length": len(text)},
                }
                for i, text in enumerate(texts)
            ]

        # Validate chunks length
        if len(chunks) != len(texts):
            logger.error(
                f"❌ Chunks length ({len(chunks)}) doesn't match texts length ({len(texts)})"
            )
            return False

        # Create default metadata if not provided
        if metadata is None:
            metadata = {
                "file_path": f"batch_{len(texts)}_chunks",
                "chunk_count": len(texts),
                "source": "batch_embed",
            }

        logger.debug(
            f"🔍 Storing {len(embeddings)} embeddings with metadata: {metadata}"
        )

        success = store.store_embeddings(embeddings, chunks, metadata)
        if success:
            logger.info(f"✅ {len(embeddings)} embeddings stored successfully")
        else:
            logger.error(f"❌ Failed to store {len(embeddings)} embeddings")

        return success

    except Exception as e:
        logger.error(f"❌ Error storing embeddings batch: {e}")
        return False


def check_embeddings_exist(file_path: str) -> bool:
    """
    Check if embeddings already exist for a file

    Args:
        file_path: Path to check

    Returns:
        True if embeddings exist
    """
    try:
        store = get_embedding_store()
        return store.embedding_exists(file_path) if store else False
    except Exception as e:
        logger.error(f"❌ Error checking embeddings existence: {e}")
        return False


def search_stored_embeddings(
    query: Union[str, List[float]], top_k: int = 5, threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search for similar embeddings in storage

    Args:
        query: Either query text or precomputed embedding
        top_k: Number of results to return
        threshold: Similarity threshold

    Returns:
        List of similar embeddings with metadata
    """
    try:
        if isinstance(query, str):
            query_embedding = embed_text(query)
        elif isinstance(query, list) and all(
            isinstance(x, (float, int)) for x in query
        ):
            query_embedding = query
        else:
            logger.error("❌ Invalid query input type")
            return []

        if not query_embedding:
            return []

        store = get_embedding_store()
        if store is None:
            return []

        results = store.search_embeddings(np.array(query_embedding), top_k, threshold)
        logger.info(f"✅ Found {len(results)} similar embeddings")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching stored embeddings: {e}")
        return []


def get_embedding_stats() -> Dict[str, Any]:
    """
    Get statistics about stored embeddings

    Returns:
        Dictionary with embedding statistics
    """
    try:
        store = get_embedding_store()
        return (
            store.get_embedding_stats()
            if store
            else {"error": "No embedding store available"}
        )
    except Exception as e:
        logger.error(f"❌ Error getting embedding stats: {e}")
        return {"error": str(e)}


def clear_stored_embeddings(file_path: Optional[str] = None) -> bool:
    """
    Clear stored embeddings

    Args:
        file_path: If provided, only clear embeddings for this file

    Returns:
        True if cleared successfully
    """
    try:
        store = get_embedding_store()
        if store is None:
            return False

        success = store.clear_embeddings(file_path)
        if success:
            if file_path:
                logger.info(f"✅ Cleared embeddings for file: {file_path}")
            else:
                logger.info("✅ Cleared all embeddings")
        else:
            logger.error("❌ Failed to clear embeddings")

        return success
    except Exception as e:
        logger.error(f"❌ Error clearing embeddings: {e}")
        return False


# Async wrappers
async def embed_text_async(text: str, store_key: Optional[str] = None) -> list:
    """Async wrapper for embed_text"""
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, embed_text, text, store_key)


async def embed_texts_batch_async(
    texts: List[str],
    chunks: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    store_results: bool = False,
) -> List[list]:
    """Async wrapper for embed_texts_batch"""
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(
            pool, embed_texts_batch, texts, chunks, metadata, store_results
        )


async def search_stored_embeddings_async(
    query_text: str, top_k: int = 5, threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Async wrapper for search_stored_embeddings"""
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(
            pool, search_stored_embeddings, query_text, top_k, threshold
        )
