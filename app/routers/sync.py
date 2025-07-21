from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Depends
from loguru import logger
from typing import Optional

from app.models.requests import SyncRequest
from app.services.sync_service import sync_drive_background
from app.dependencies import get_bot_api_key, get_drive_sync

router = APIRouter()


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key"""
    bot_api_key = get_bot_api_key()
    if x_api_key != bot_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key


@router.post("/sync/drive")
async def sync_google_drive(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    """Sync PDFs from Google Drive"""
    drive_sync = get_drive_sync()
    folder_id = request.folder_id or (drive_sync.folder_id if drive_sync else None)
    download_dir = request.download_dir or "data/raw_pdfs"

    if not folder_id:
        raise HTTPException(
            status_code=400,
            detail="No folder_id provided and no Google Drive sync configured.",
        )

    try:
        background_tasks.add_task(sync_drive_background, folder_id, download_dir)
        logger.info(f"🔄 Google Drive sync started for folder: {folder_id}")
        return {
            "message": "Google Drive sync started",
            "folder_id": folder_id,
            "download_dir": download_dir,
            "status": "running_in_background",
        }
    except Exception as e:
        logger.error(f"❌ Failed to start Google Drive sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/poll_drive")
async def poll_drive_sync(
    background_tasks: BackgroundTasks,
    folder_id: Optional[str] = None,
    _: str = Depends(verify_api_key),
):
    """Poll Google Drive for new files and trigger ingestion"""
    drive_sync = get_drive_sync()
    sync_folder_id = folder_id or (drive_sync.folder_id if drive_sync else None)

    if not sync_folder_id:
        raise HTTPException(
            status_code=400,
            detail="No folder_id provided and no Google Drive sync configured.",
        )

    try:
        background_tasks.add_task(sync_drive_background, sync_folder_id)
        logger.info(f"📡 Drive polling task queued for folder: {sync_folder_id}")
        return {
            "message": "Drive polling and ingestion started",
            "status": "background_task_queued",
        }
    except Exception as e:
        logger.error(f"❌ Failed to queue drive polling: {e}")
        raise HTTPException(status_code=500, detail=str(e))
