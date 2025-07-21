from fastapi import APIRouter, Header, HTTPException, Depends
from loguru import logger

from app.dependencies import (
    get_bot_api_key,
    get_data_loader,
    get_app_config,
    scan_and_process_files,
)

router = APIRouter()


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key"""
    bot_api_key = get_bot_api_key()
    if x_api_key != bot_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key


@router.get("/system/info")
async def system_info(_: str = Depends(verify_api_key)):
    """Get comprehensive system information"""
    data_loader = get_data_loader()
    config = get_app_config()
    chunks = data_loader.load_all_chunks()
    chunked_ready = len(chunks) > 0

    return {
        "system": {
            "version": "2.0.0",
            "storage_mode": config.embedding_storage,
            "debug": config.debug,
            "cache_enabled": config.use_cache,
            "chunked_data_ready": chunked_ready,
        },
        "data": {
            "total_chunks": len(chunks),
        },
    }


@router.get("/data/stats")
async def data_stats(_: str = Depends(verify_api_key)):
    """Get detailed data statistics"""
    data_loader = get_data_loader()
    chunks = data_loader.load_all_chunks()
    law_type_stats = {}
    for chunk in chunks:
        law_type = chunk["metadata"].get("law_type", "Unknown")
        law_type_stats[law_type] = law_type_stats.get(law_type, 0) + 1

    return {
        "total_chunks": len(chunks),
        "law_type_breakdown": law_type_stats,
    }


@router.post("/data/reload")
async def reload_data(_: str = Depends(verify_api_key)):
    """Reload data from chunked files"""
    data_loader = get_data_loader()
    data_loader._chunks = None
    chunks = data_loader.load_all_chunks()
    logger.info(f"📊 Data reloaded: {len(chunks)} chunks")
    return {"message": "Data reloaded successfully", "total_chunks": len(chunks)}


@router.post("/test/scan")
async def test_scan(_: str = Depends(verify_api_key)):
    """Manually trigger scan_and_process_files for testing"""
    await scan_and_process_files()
    return {"status": "scan_and_process_files completed"}
