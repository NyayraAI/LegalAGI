"""Shared dependencies for the application"""

import os
from functools import lru_cache
from utils.core.config import get_config
from utils.core.embed import get_embedding_store
from utils.data.data_loader import ChunkedDataLoader
from utils.external.google_drive_sync import DriveSync
from loguru import logger
from utils.core.embed import get_embedding_stats as _get_embedding_stats
from utils.core.embed import check_embeddings_exist as _check_embeddings_exist
from pathlib import Path
from utils.core.embed import (
    search_stored_embeddings_async as _search_stored_embeddings_async,
    embed_text_async as _embed_text_async,
)
from utils.core.config import (
    is_local_storage as _is_local_storage,
    is_database_storage as _is_database_storage,
)
from utils.data.supabase_client import get_supabase_client as _get_supabase_client
import json
from utils.processing.chunker import PDFProcessor
from utils.processing.metadata_extractor import MetadataExtractor

from utils.core.embed import SyncEmbeddingStore

import hashlib

_embedding_store_instance = None


@lru_cache()
def get_data_loader():
    """Get the data loader instance"""
    return ChunkedDataLoader()


def get_embedding_store_instance():
    """Get the embedding store instance with detailed error logging (singleton per process)"""
    global _embedding_store_instance
    if _embedding_store_instance is not None:
        return _embedding_store_instance
    try:
        store = get_embedding_store()
        if store is None:
            logger.error("❌ Embedding store returned None")
            return None
        logger.info(
            f"✅ Embedding store initialized successfully: {type(store).__name__}"
        )
        _embedding_store_instance = store
        return store
    except ImportError as e:
        logger.error(f"❌ Import error in embedding store: {e}")
        logger.error("📦 Check if all required packages are installed")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to initialize embedding store: {e}")
        logger.error(f"📍 Error type: {type(e).__name__}")
        import traceback

        logger.error(f"📍 Full traceback: {traceback.format_exc()}")
        return None


@lru_cache()
def get_drive_sync():
    """Robustly get the Google Drive sync instance, or None if not configured/available."""
    drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    if not drive_folder_id:
        logger.info(
            "ℹ️  Google Drive sync not configured (GOOGLE_DRIVE_FOLDER_ID not set)"
        )
        return None

    # Check for credentials.json
    if not Path("credentials.json").exists():
        logger.warning("⚠️  Google Drive sync configured but credentials.json not found")
        logger.warning(
            "   📋 Place your Google Drive API credentials.json file in the project root"
        )
        return None

    try:
        drive_sync = DriveSync(drive_folder_id)
        logger.info(f"✅ Google Drive sync initialized for folder: {drive_folder_id}")
        return drive_sync
    except ImportError as e:
        logger.warning(f"⚠️  Google Drive dependencies missing: {e}")
        logger.warning(
            "   📋 Install with: pip install google-api-python-client google-auth-oauthlib"
        )
        return None
    except Exception as e:
        logger.warning(f"⚠️  Google Drive sync initialization failed: {e}")
        return None


@lru_cache()
def get_bot_api_key():
    """Get the bot API key"""
    return os.getenv("BOT_API_KEY")


@lru_cache()
def get_app_config():
    """Get the app configuration"""
    return get_config()


@lru_cache()
def get_embedding_stats():
    """Dependency wrapper for retrieving embedding statistics"""
    return _get_embedding_stats()


@lru_cache()
def get_chunked_data_dir() -> Path:
    return Path("data/chunked_legal_data")


# Check if embeddings exist
def check_embeddings_exist(query_hash: str):
    return _check_embeddings_exist(query_hash)


# Async embedding operations
async def search_stored_embeddings_async(text: str, top_k=1, threshold=0.99):
    return await _search_stored_embeddings_async(text, top_k, threshold)


async def embed_text_async(text: str, store_key: str = ""):
    return await _embed_text_async(text, store_key)


# Storage configuration
@lru_cache()
def is_local_storage() -> bool:
    return _is_local_storage()


@lru_cache()
def is_database_storage() -> bool:
    return _is_database_storage()


# Supabase client
@lru_cache()
def get_supabase_client():
    return _get_supabase_client()


# Hash generator
@lru_cache()
def generate_query_hash(text: str) -> str:
    """Generate a unique hash for a query"""
    return hashlib.md5(text.encode()).hexdigest()


# -----------------------------
# Background Tasks
# -----------------------------


async def run_embedding_sync():
    """Periodically sync embeddings if using SyncEmbeddingStore"""
    try:
        store = get_embedding_store_instance()
        if isinstance(store, SyncEmbeddingStore):
            before = len(store.sync_queue)
            logger.info(f"🔄 Starting embedding sync ({before} items in queue)")
            store.sync_pending()
            after = len(store.sync_queue)
            logger.info(
                f"✅ Embedding sync: synced {before - after} items, {after} remaining"
            )
        else:
            logger.debug("Skipping embedding sync (not using SyncEmbeddingStore)")
    except Exception as e:
        logger.error(f"❌ Embedding sync failed: {e}")


async def run_drive_sync():
    """Periodic Google Drive sync"""
    try:
        # Import here to avoid circular import
        from app.services.sync_service import sync_drive_background

        drive_sync = get_drive_sync()
        if drive_sync:
            logger.info("🔄 Starting Google Drive sync...")
            await sync_drive_background(drive_sync.folder_id, "data/raw_pdfs")
            logger.info("✅ Google Drive sync completed")
        else:
            logger.debug("Skipping Google Drive sync (not configured)")
    except Exception as e:
        logger.error(f"❌ Google Drive sync failed: {e}")


async def scan_and_process_files():
    """Periodically scan directory for new files and process them"""
    try:
        scan_dir = Path("data/raw_pdfs")
        chunked_data_dir = get_chunked_data_dir()
        processor = PDFProcessor()
        extractor = MetadataExtractor()

        current_files = {f.name: f.stat().st_mtime for f in scan_dir.glob("*.pdf")}

        if not hasattr(scan_and_process_files, "last_files"):
            scan_and_process_files.last_files = {}

        new_files = [
            f
            for f, mtime in current_files.items()
            if f not in scan_and_process_files.last_files
            or mtime > scan_and_process_files.last_files[f]
        ]

        if new_files:
            logger.info(f"📄 Found {len(new_files)} new/changed PDF(s)")
            for file_name in new_files:
                file_path = scan_dir / file_name
                try:
                    metadata = extractor.extract_from_filename(file_name)
                    chunks = processor.process_pdf(file_path)

                    if chunks:
                        for chunk in chunks:
                            chunk["metadata"] = metadata

                        output_path = chunked_data_dir / f"{file_path.stem}.json"
                        with open(output_path, "w") as f:
                            json.dump(chunks, f)

                        logger.info(f"✅ Processed {file_name} -> {len(chunks)} chunks")
                except Exception as e:
                    logger.error(f"❌ Failed to process {file_name}: {e}")

        scan_and_process_files.last_files = current_files

    except Exception as e:
        logger.error(f"❌ File scan failed: {e}")
