import json
from pathlib import Path
from loguru import logger

from utils.processing.chunker import PDFProcessor
from utils.processing.metadata_extractor import MetadataExtractor
from typing import Optional
from typing import Union


class SyncService:
    """Service class for handling Drive sync operations"""

    def __init__(self, drive_sync=None, chunked_data_dir: Optional[Path] = None):
        self.drive_sync = drive_sync
        self.chunked_data_dir = chunked_data_dir or Path("data/chunked_legal_data")
        self.processor = PDFProcessor()
        self.extractor = MetadataExtractor()

    async def sync_drive_background(
        self, folder_id: str, download_dir: str = "data/raw_pdfs"
    ):
        """Background task to sync and process Google Drive files"""
        if not self.drive_sync:
            logger.error("❌ Google Drive sync not initialized")
            return

        new_files = self.drive_sync.download_new_pdfs(download_dir)

        if not new_files:
            logger.info("ℹ️  No new files found in Google Drive")
            return

        logger.info(f"✅ Downloaded {len(new_files)} new files from Google Drive")

        for file_name in new_files:
            file_path = Path(download_dir) / file_name
            try:
                metadata = self.extractor.extract_from_filename(file_name)
                chunks = self.processor.process_pdf(file_path)

                if chunks:
                    for chunk in chunks:
                        chunk["metadata"] = metadata

                    output_path = self.chunked_data_dir / f"{file_path.stem}.json"
                    with open(output_path, "w") as f:
                        json.dump(chunks, f)
                    logger.info(f"✅ Processed {file_name} -> {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"❌ Failed to process {file_name}: {e}")


# Factory function to create service instance
def create_sync_service(
    drive_sync=None, chunked_data_dir: Union[str, Path, None] = None
) -> SyncService:
    if isinstance(chunked_data_dir, str):
        chunked_data_dir = Path(chunked_data_dir)
    return SyncService(drive_sync, chunked_data_dir)


# Legacy function for backward compatibility
async def sync_drive_background(folder_id: str, download_dir: str = "data/raw_pdfs"):
    """Legacy function - imports dependencies at runtime to avoid circular imports"""
    from app.dependencies import get_drive_sync, get_chunked_data_dir

    drive_sync = get_drive_sync()
    chunked_data_dir = get_chunked_data_dir()

    service = SyncService(drive_sync, chunked_data_dir)
    await service.sync_drive_background(folder_id, download_dir)
