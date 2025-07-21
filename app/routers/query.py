"""Query-related API endpoints"""

from fastapi import APIRouter, Header, HTTPException, Depends
from datetime import datetime
from loguru import logger

from app.models.requests import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.dependencies import get_bot_api_key

router = APIRouter()


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key"""
    bot_api_key = get_bot_api_key()
    if x_api_key != bot_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest, _: str = Depends(verify_api_key)):
    """Ask a question using the Legal RAG system"""
    start_time = datetime.now()

    try:
        logger.info(f"🤔 Question received: '{request.question}'")

        query_service = QueryService()
        result = await query_service.process_query(request.question, start_time)

        return result

    except Exception as e:
        logger.error(f"❌ Unexpected error in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test_embedding")
async def test_embedding_pipeline(text: str, _: str = Depends(verify_api_key)):
    """Test the embedding pipeline with sample text"""
    try:
        query_service = QueryService()
        result = await query_service.test_embedding_pipeline(text)
        return result

    except Exception as e:
        logger.error(f"❌ Embedding pipeline test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
