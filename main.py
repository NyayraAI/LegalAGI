from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils.embed import embed_text
from utils.supabase_client import supabase, TABLE_NAME
from utils.llm import ask_llm
import os

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

@app.post("/ask")
async def ask_question(request: QueryRequest, x_api_key: str = Header(None)):
    if x_api_key != BOT_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    question = request.question
    try:
        embedding = embed_text(question)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to create embedding")

        response = supabase.rpc("match_documents", {
            "match_count": 1,
            "match_threshold": 0.78,
            "query_embedding": embedding
        }).execute()

        matches = response.data
        if not matches:
            return {"answer": "No relevant documents found.", "matches": []}

        # Combine matched contexts
        context = "\n\n".join([doc["content"] for doc in matches])

        # Ask LLM using context
        answer = ask_llm(context, question)

        return {"answer": answer, "matches": matches}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
