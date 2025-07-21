"""Query service containing business logic for question answering"""

import asyncio
import concurrent.futures
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from utils.core.embed import (
    embed_text_async,
    check_embeddings_exist,
    search_stored_embeddings_async,
)
from utils.core.llm import ask_llm
from utils.core.config import get_config, is_local_storage, is_database_storage
from app.dependencies import get_data_loader, get_embedding_store_instance
from app.services.embedding_service import _search_hybrid


class QueryService:
    def __init__(self):
        self.config = get_config()
        self.data_loader = get_data_loader()
        self.embedding_store = get_embedding_store_instance()

    def generate_query_hash(self, question: str) -> str:
        """Generate a unique hash for a query to use as storage key"""
        return hashlib.md5(question.encode()).hexdigest()

    def get_llm_model_info(self) -> Dict[str, Any]:
        """Get information about the LLM model being used"""
        return {
            "provider": "groq",
            "model": "llama3-70b-8192",
            "timestamp": datetime.now().isoformat(),
        }

    async def get_or_create_embedding(
        self, question: str, use_storage: bool = True
    ) -> List[float]:
        """Get embedding from storage or create new one (no cache)"""
        try:
            # 1. Check storage if enabled (should only be True for document ingestion, not user queries)
            if use_storage and self.embedding_store:
                query_hash = self.generate_query_hash(question)
                if check_embeddings_exist(query_hash):
                    logger.info("✅ Found embedding in storage")
                    stored_results = await search_stored_embeddings_async(
                        question, top_k=1, threshold=0.99
                    )
                    if stored_results:
                        embedding = stored_results[0].get("embedding")
                        if embedding:
                            return embedding

            # 2. Generate new embedding
            logger.info("🔄 Generating new embedding")
            # For user questions, do NOT store the embedding persistently
            embedding = await embed_text_async(
                question, None
            )  # store_key=None disables storage

            if embedding:
                logger.info("✅ New embedding generated")

            return embedding

        except Exception as e:
            logger.error(f"❌ Error getting/creating embedding: {e}")
            return []

    async def fetch_matches(self, embedding: List[float]) -> Dict[str, Any]:
        """Fetch matches using hybrid approach"""
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, _search_hybrid, embedding)

    async def process_query(
        self, question: str, start_time: datetime
    ) -> Dict[str, Any]:
        """Process a query and return the response"""
        # Get or create embedding
        embedding = await self.get_or_create_embedding(question, use_storage=True)
        if not embedding:
            raise Exception("Failed to generate embedding")

        # Fetch matches
        response = await self.fetch_matches(embedding)
        matches = response.get("embedding_matches", [])
        matches_source = response.get("source", "unknown")
        document_matches = [
            m for m in matches if not m.get("content", "").strip().endswith("?")
        ]

        if not document_matches:
            logger.warning("❌ No valid document matches found")
            return {
                "answer": "No relevant documents found.",
                "matches": [],
                "metadata": {
                    "storage_mode": self.config.embedding_storage,
                    "embedding_source": "generated",
                    "matches_source": matches_source,
                    "llm_model": None,
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                },
            }

        # Proceed using filtered document matches only
        MAX_CHUNKS = 4  # Limit to top N chunks to avoid LLM token overflow
        MAX_WORDS_PER_CHUNK = 500  # Truncate each chunk for safety

        def truncate(text, max_words=MAX_WORDS_PER_CHUNK):
            words = text.split()
            return " ".join(words[:max_words])

        document_matches = document_matches[:MAX_CHUNKS]
        context = "\n\n".join([truncate(doc["content"]) for doc in document_matches])
        logger.info(
            f"🤖 Sending query to LLM with {len(document_matches)} context chunks (max {MAX_WORDS_PER_CHUNK} words each)"
        )
        answer = await ask_llm(context, question)

        # Prepare response
        llm_info = self.get_llm_model_info()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"✅ Question answered in {duration:.2f}s using {matches_source}")

        return {
            "answer": answer,
            "matches": matches,
            "metadata": {
                "storage_mode": self.config.embedding_storage,
                "embedding_source": "generated",
                "matches_source": matches_source,
                "matches_count": len(matches),
                "llm_model": llm_info,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
            },
        }

    async def test_embedding_pipeline(self, text: str) -> Dict[str, Any]:
        """Test the embedding pipeline with sample text"""
        start_time = datetime.now()

        # Test embedding creation
        embedding = await self.get_or_create_embedding(text, use_storage=True)
        if not embedding:
            raise Exception("Failed to create embedding")

        # Test search
        matches = await self.fetch_matches(embedding)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "test_text": text,
            "embedding_dimension": len(embedding),
            "matches_found": len(matches.get("embedding_matches", [])),
            "matches_source": matches.get("source", "unknown"),
            "duration_seconds": duration,
            "storage_mode": self.config.embedding_storage,
            "timestamp": start_time.isoformat(),
            "status": "success",
        }
