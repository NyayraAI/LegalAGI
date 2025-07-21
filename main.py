import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_file = Path(".env")
if env_file.exists():
    load_dotenv(override=True)

# Import components
from app.core.lifespan import lifespan
from app.core.core_middleware import setup_logging
from app.routers import health, query, sync, admin, embeddings

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Legal RAG Backend",
    version="2.0.0",
    description="Enhanced Legal RAG system with hybrid embedding search",
)

# Add CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(sync.router, prefix="/api", tags=["sync"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(embeddings.router, prefix="/api", tags=["embeddings"])


@app.get("/")
async def root():
    from utils.core.config import get_config
    from app.dependencies import get_data_loader, get_drive_sync

    config = get_config()
    data_loader = get_data_loader()
    drive_sync = get_drive_sync()

    return {
        "message": "Welcome to the NyayraAI Backend v2.0",
        "storage_mode": config.embedding_storage,
        "features": {
            "google_drive_sync": drive_sync is not None,
            "chunked_data_ready": len(data_loader.load_all_chunks()) > 0,
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
