"""Middleware and logging setup"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging():
    """Setup enhanced logging with loguru"""
    logger.remove()

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # File logging with rotation
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        compression="zip",
    )

    # Console logging
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
    )

    logger.info("✅ Logging setup complete")
