# RAG Backend: Production Data & API Flow

## 1. Automated Data Ingestion Pipeline

- **Google Drive Polling:**

  - The backend periodically polls your configured Google Drive folder for new PDF files (using `DriveSync` in `utils/external/google_drive_sync.py`).
  - New PDFs are downloaded to `data/raw_pdfs/`.

- **Chunking & Embedding:**

  - Each new/changed PDF is automatically chunked into manageable text segments (`PDFProcessor` in `utils/processing/chunker.py`).
  - Chunks are saved to `data/chunked_legal_data/`.
  - Vector embeddings are created for each chunk and stored locally (`data/embeddings/`).

- **Asynchronous Embedding Sync:**
  - If configured in "sync" mode, all local embeddings are periodically synchronized with a remote Supabase database (see `app/services/embedding_service.py`).
  - Only new or changed embeddings are uploaded, making the process efficient.

## 2. API Endpoints (FastAPI)

- **Querying:**

  - `/ask` — Ask questions and get context-aware answers using RAG.
  - `/test_embedding` — Test the embedding and retrieval pipeline for a sample text.

- **Embeddings:**

  - `/embeddings/create` — Create and (optionally) store a new embedding.
  - `/embeddings/stats` — Get embedding storage statistics.
  - `/embeddings/clear` — Clear stored embeddings.
  - `/sync-embeddings` — Sync local embeddings to Supabase.

- **Admin & Data:**

  - `/system/info` — Get system and storage info.
  - `/data/stats` — Get detailed data statistics.
  - `/data/reload` — Reload chunked data from disk.
  - `/test/scan` — Manually trigger a scan for new PDFs (for testing/ops).

- **Debug:**

  - `/debug/stored-embeddings` — Inspect stored embeddings.
  - `/debug/reindex-documents` — Force re-chunking and re-embedding of all PDFs.

- **Health:**
  - `/health` — Health check endpoint.

## 3. Core Files in Production

- `app/` — Main FastAPI app, routers, services, and dependencies
- `utils/core/` — Embedding, config, and model logic
- `utils/processing/` — Chunking and metadata extraction
- `utils/data/` — Embedding store implementations (local, sync, database)
- `utils/external/` — Google Drive sync logic
- `data/` — Local storage for PDFs, chunked data, and embeddings
- `README.md`, `flow.md`, `requirements.txt`, `setup.py` — Docs and setup

## 4. Security & Best Practices

- Sensitive files (`.env`, `token.json`, `credentials.json`, etc.) are in `.gitignore` and not pushed.
- All legacy, dev, and test scripts are excluded from the production repo.

## 5. Planned Feature: Caching

- Caching (for embeddings and search results) is planned for a future update to further improve performance and reduce redundant computation.

---

**This flow ensures your legal document data is always up to date, searchable, and ready for RAG with minimal manual effort.**
