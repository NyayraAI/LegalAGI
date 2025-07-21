import asyncio
from loguru import logger
from typing import Callable, Awaitable, Dict

from app.dependencies import (
    get_app_config,
    run_embedding_sync,
    run_drive_sync,
    scan_and_process_files,
)


async def periodic_task(
    func: Callable[[], Awaitable[None]], interval: int, name: str
) -> None:
    """Run a function periodically with a fixed interval."""
    try:
        while True:
            try:
                logger.debug(f"Starting {name} task")
                await func()
            except Exception as e:
                logger.error(f"{name} task failed: {e}")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info(f"{name} task cancelled")


async def run_background_tasks() -> Dict[str, asyncio.Task]:
    """Start all background periodic tasks and return the created tasks."""
    config = get_app_config()
    task_map = {
        "embedding_sync": periodic_task(
            run_embedding_sync, config.embedding_sync_interval, "Embedding Sync"
        ),
        "drive_sync": periodic_task(
            run_drive_sync, config.drive_sync_interval, "Google Drive Sync"
        ),
        "file_scan": periodic_task(
            scan_and_process_files, config.file_scan_interval, "File Scanner"
        ),
    }
    return {name: asyncio.create_task(task) for name, task in task_map.items()}
