"""
Configuration system for RAG Backend
Handles environment variables and storage type determination
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Configuration class for the RAG backend"""

    def __init__(self):
        # Load environment variables
        self._load_env()

        # Core settings
        self.debug = self._get_bool("DEBUG", False)
        self.log_level = self._get_str("LOG_LEVEL", "INFO")

        # Storage configuration
        self.embedding_storage = self._get_str("EMBEDDING_STORAGE", "local")
        self.embedding_db_path = self._get_str("EMBEDDING_DB_PATH", "data/embeddings/")

        # Database configuration (for online storage)
        self.supabase_url = self._get_str("SUPABASE_URL", "")
        self.supabase_key = self._get_str("SUPABASE_KEY", "")

        # API Keys
        self.groq_api_key = self._get_str("GROQ_API_KEY", "")

        # Google Drive (optional)
        self.google_drive_folder_id = self._get_str("GOOGLE_DRIVE_FOLDER_ID", "")

        # Cache configuration
        self.redis_url = self._get_str("REDIS_URL", "")
        self.use_cache = self._get_bool("USE_CACHE", True)

        # async tasks
        self.embedding_sync_interval = int(os.getenv("EMBEDDING_SYNC_INTERVAL", 30))  # seconds
        self.drive_sync_interval = int(os.getenv("DRIVE_SYNC_INTERVAL", 300))  # seconds
        self.file_scan_interval = int(os.getenv("FILE_SCAN_INTERVAL", 60))  # seconds
        
        # Validate configuration
        self._validate_config()

    def _load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try .env.example as fallback
            example_path = Path(".env.example")
            if example_path.exists():
                load_dotenv(example_path)
                print("⚠️  Using .env.example - create .env file for custom settings")

    def _get_str(self, key: str, default: str = "") -> str:
        """Get string value from environment"""
        return os.getenv(key, default)

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        value = os.getenv(key, "").lower()
        return value in ("true", "1", "yes", "on") if value else default

    def _get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _validate_config(self):
        """Validate configuration settings"""
        # Validate storage type
        if self.embedding_storage not in ["local", "database", "sync"]:
            raise ValueError(
                f"Invalid EMBEDDING_STORAGE: {self.embedding_storage}. Must be 'local', 'database', or 'sync'"
            )

        # Validate database configuration if using database storage
        if self.embedding_storage in ["database", "sync"]:
            if not self.supabase_url or not self.supabase_key:
                logger.warning("Database config missing - will fallback to local only")

        # Validate local storage path
        if self.embedding_storage in ["local", "sync"]:
            Path(self.embedding_db_path).mkdir(parents=True, exist_ok=True)

    def is_local_storage(self) -> bool:
        """Check if using local storage"""
        return self.embedding_storage == "local"

    def is_database_storage(self) -> bool:
        """Check if using database storage"""
        return self.embedding_storage == "database"

    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage-specific configuration"""
        if self.is_local_storage():
            return {"type": "local", "path": self.embedding_db_path}
        elif self.is_sync_storage():
            return {
                "type": "sync",
                "local_path": self.embedding_db_path,
                "has_db": self.has_database_config(),
            }
        else:
            return {
                "type": "database",
                "url": self.supabase_url,
                "key": self.supabase_key,
            }

    def get_storage_mode(self) -> str:
        return self.embedding_storage

    def get_model_name(self) -> str:
        return os.getenv("RAG_MODEL", "llama")

    def get_api_host(self) -> str:
        return os.getenv("API_HOST", "127.0.0.1")

    def get_api_port(self) -> int:
        return int(os.getenv("API_PORT", "8000"))

    def get_debug_mode(self) -> bool:
        return self.debug

    def __str__(self) -> str:
        """String representation (safe for logging)"""
        return f"Config(storage={self.embedding_storage}, debug={self.debug})"

    def is_sync_storage(self) -> bool:
        """Check if using sync storage (local + database)"""
        return self.embedding_storage == "sync"

    def has_database_config(self) -> bool:
        """Check if database configuration is available"""
        return bool(self.supabase_url and self.supabase_key)


# Global config instance
config = Config()


# Helper functions for easy access
def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def is_local_storage() -> bool:
    """Check if using local storage"""
    return config.is_local_storage()


def is_database_storage() -> bool:
    """Check if using database storage"""
    return config.is_database_storage()


def get_storage_config() -> Dict[str, Any]:
    """Get storage configuration"""
    return config.get_storage_config()


def is_sync_storage() -> bool:
    """Check if using sync storage"""
    return config.is_sync_storage()


def has_database_config() -> bool:
    """Check if database config is available"""
    return config.has_database_config()
