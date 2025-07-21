from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime

from app.dependencies import (
    get_data_loader,
    get_embedding_store_instance,
    get_drive_sync,
    get_app_config,
)


router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        data_loader = get_data_loader()
        chunks = data_loader.load_all_chunks()
        chunks_available = len(chunks) > 0

        logger.info(f"✅ Health check: {len(chunks)} chunks available")
        embedding_store = get_embedding_store_instance()
        drive_sync = get_drive_sync()
        config = get_app_config()

        return {
            "status": "healthy" if chunks_available else "degraded",
            "storage_mode": config.embedding_storage,
            "embedding_store": "available" if embedding_store else "unavailable",
            "google_drive_sync": "available" if drive_sync else "unavailable",
            "chunked_data_ready": chunks_available,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")
