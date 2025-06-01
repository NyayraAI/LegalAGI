from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.embed import embed_text_async
from utils.supabase_client import supabase, TABLE_NAME
from utils.llm import ask_llm
from utils.cache import get_cached_embedding, set_cached_embedding, get_cached_match, set_cached_match
from loguru import logger
import sys
import os
import asyncio
import concurrent.futures

logger.remove()
logger.add(sys.stderr, level="INFO")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_API_KEY = os.getenv("BOT_API_KEY")

class QueryRequest(BaseModel):
    question: str

# Async wrapper for supabase.rpc
async def fetch_matches(embedding):
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        def call_rpc():
            return supabase.rpc("match_documents", {
                "match_count": 1,
                "match_threshold": 0.78,
                "query_embedding": embedding
            }).execute()
        return await loop.run_in_executor(pool, call_rpc)

@app.post("/ask")
async def ask_question(request: QueryRequest, x_api_key: str = Header(None)):
    if x_api_key != BOT_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    question = request.question
    try:
        # Check cache for embedding
        embedding = get_cached_embedding(question)
        if not embedding:
            # Get the actual embedding result, not the coroutine
            embedding = await embed_text_async(question)
            set_cached_embedding(question, embedding)

        # Check cache for matches using embedding as key
        matches = get_cached_match(tuple(embedding))
        if not matches:
            # Fetch matches asynchronously
            response = await fetch_matches(embedding)
            matches = response.data
            set_cached_match(tuple(embedding), matches)

        if not matches:
            return {"answer": "No relevant documents found.", "matches": []}

        context = "\n\n".join([doc["content"] for doc in matches])

        answer = await ask_llm(context, question)

        return {"answer": answer, "matches": matches}

    except Exception as e:
        logger.exception("❌ Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))