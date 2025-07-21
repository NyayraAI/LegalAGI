"""Pydantic models for API requests and responses"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    question: str


class EmbeddingRequest(BaseModel):
    text: str
    store_key: Optional[str] = None


class SyncRequest(BaseModel):
    folder_id: Optional[str] = None
    download_dir: Optional[str] = "data/raw_pdfs"


class QueryResponse(BaseModel):
    answer: str
    matches: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class EmbeddingResponse(BaseModel):
    text: str
    embedding: List[float]
    dimension: int
    stored: bool
    storage_mode: str
    timestamp: str


class SyncResponse(BaseModel):
    message: str
    folder_id: Optional[str] = None
    download_dir: str
    status: str


class HealthResponse(BaseModel):
    status: str
    storage_mode: str
    cache: Dict[str, Any]
    embedding_store: str
    google_drive_sync: str
    chunked_data_ready: bool
    timestamp: str


class SystemInfoResponse(BaseModel):
    system: Dict[str, Any]
    storage: Dict[str, Any]
    data: Dict[str, Any]
    cache: Dict[str, Any]
    recommendations: Dict[str, Any]
