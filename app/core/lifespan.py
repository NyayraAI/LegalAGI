"""Application lifespan management"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from watchdog.observers import Observer
from pathlib import Path

from app.core.background import (
    run_embedding_sync,
    run_drive_sync,
    scan_and_process_files,
)
from utils.processing.chunker import PDFWatcher
from app.dependencies import get_app_config


async def periodic_task(func, interval: int, name: str):
    """Run a function periodically with interval"""
    try:
        while True:
            try:
                logger.debug(f"🏃 Starting {name} task")
                await func()
            except Exception as e:
                logger.error(f"{name} task failed: {e}")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info(f"⏹️ {name} task cancelled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async context manager for FastAPI lifespan events"""
    config = get_app_config()

    # Startup code
    tasks = {
        "embedding_sync": asyncio.create_task(
            periodic_task(
                run_embedding_sync, config.embedding_sync_interval, "Embedding Sync"
            )
        ),
        "drive_sync": asyncio.create_task(
            periodic_task(
                run_drive_sync, config.drive_sync_interval, "Google Drive Sync"
            )
        ),
        "file_scan": asyncio.create_task(
            periodic_task(
                scan_and_process_files, config.file_scan_interval, "File Scanner"
            )
        ),
    }

    async def watchdog_shutdown_task(observer):
        """Shutdown watchdog observer on app exit"""
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            observer.stop()
            observer.join()
            logger.info("👋 PDF file watcher stopped")

    # File watcher setup (if in development)
    if config.debug:
        observer = Observer()
        event_handler = PDFWatcher(processor=scan_and_process_files)
        observer.schedule(event_handler, "data/raw_pdfs", recursive=False)
        observer.start()
        logger.info("👀 PDF file watcher started")
        tasks["file_watcher"] = asyncio.create_task(watchdog_shutdown_task(observer))

    try:
        yield  # App runs here
    finally:
        # Shutdown code
        for name, task in tasks.items():
            task.cancel()
            logger.info(f"⏹️ Cancelling {name} task")

        await asyncio.gather(*tasks.values(), return_exceptions=True)
        logger.info("📴 All background tasks stopped")
