from fastapi import APIRouter, Header, HTTPException, Depends
from loguru import logger
from typing import Optional

from app.dependencies import (
    get_bot_api_key,
    get_embedding_stats,
)
from utils.core.embed import clear_stored_embeddings
from app.models.requests import EmbeddingRequest
from app.services.embedding_service import get_or_create_embedding
from app.services.embedding_service import (
    debug_stored_embeddings,
    index_documents_properly,
    sync_embeddings,
)

router = APIRouter()


def verify_api_key(
    x_api_key: str = Header(None), bot_api_key: str = Depends(get_bot_api_key)
):
    if x_api_key != bot_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key


@router.post("/embeddings/create")
async def create_embedding(request: EmbeddingRequest, _: str = Depends(verify_api_key)):
    # Only allow storing if store_key is provided AND text is not a question
    is_document = (
        bool(request.store_key)
        and len(request.text) > 100
        and not request.text.strip().endswith("?")
    )
    embedding = await get_or_create_embedding(
        request.text,
        use_storage=is_document,
        store_key=request.store_key if is_document else None,
    )
    logger.info(f"✅ Embedding created for text: '{request.text[:50]}...'")
    return {
        "text": request.text,
        "embedding": embedding,
        "dimension": len(embedding) if embedding else 0,
        "stored": is_document,
    }


@router.get("/embeddings/stats")
async def embedding_stats(_: str = Depends(verify_api_key)):
    """Get embedding storage statistics"""
    return get_embedding_stats()


@router.delete("/embeddings/clear")
async def clear_embeddings(
    file_path: Optional[str] = None, _: str = Depends(verify_api_key)
):
    """Clear stored embeddings"""
    success = clear_stored_embeddings(file_path)
    logger.info(f"✅ Embeddings cleared: {file_path or 'all'}")
    return {"success": success, "cleared": file_path if file_path else "all"}


@router.post("/sync-embeddings")
async def sync_embeddings_route(_: str = Depends(verify_api_key)):
    """Synchronize all local embeddings to the remote database"""
    result = await sync_embeddings()
    return result


@router.get("/debug/stored-embeddings")
async def debug_stored_embeddings_endpoint(_: str = Depends(verify_api_key)):
    """Debug what's stored in your embedding store"""
    result = await debug_stored_embeddings()
    return result


@router.post("/debug/reindex-documents")
async def reindex_documents_endpoint(_: str = Depends(verify_api_key)):
    """Properly reindex your documents"""
    result = await index_documents_properly()
    return result
