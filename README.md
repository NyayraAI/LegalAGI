# NyaayraAI Legal RAG Backend

A Retrieval-Augmented Generation (RAG) backend for open legal AI, built with Python, FastAPI, Supabase, Redis, and embeddings. This project aims to democratize access to legal knowledge and serve as the foundation for an open legal AGI assistant.

---

## 🚀 Project Overview

NyaayraAI Legal RAG is an open-source backend that answers legal questions using Indian law. It combines retrieval (from a legal database) and generation (via LLMs) to provide accurate, context-aware answers. The system is designed for extensibility, transparency, and public collaboration.

---

## ✨ Features

- **Ask Legal Questions**: Query Indian law and get context-rich, LLM-generated answers.
- **Retrieval-Augmented Generation**: Combines vector search with LLMs for grounded responses.
- **Supabase Integration**: Stores and retrieves legal documents and embeddings.
- **Redis Caching**: Fast, efficient cache for embeddings and search results.
- **Open, Modular Codebase**: Easy to extend, audit, and contribute.
- **API-first**: FastAPI endpoints for easy integration.
- **Local Embedding Support**: Uses SentenceTransformers for local embedding generation.

---

## 🛠️ Tech Stack

- **Python 3.9+**
- **FastAPI** (API framework)
- **Supabase** (Postgres + vector search)
- **Redis** (caching)
- **SentenceTransformers** (embeddings)
- **Groq LLM API** (default, can be swapped)
- **Uvicorn** (ASGI server)

---

## ⚡ Quickstart

### 1. Clone the repo
```bash
git clone https://github.com/NyayraAI/rag-backend-python.git
cd rag-backend-python
```

### 2. Install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 4. Run the backend
```bash
uvicorn main:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API docs.

---

## 🧩 Environment Variables

Create a `.env` file with the following variables:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon/public API key
- `REDIS_URL` - Redis connection string (optional, defaults to local Redis)
- `GROQ_API_KEY` - API key for Groq LLM (or your preferred LLM)
- `BOT_API_KEY` - API key for protecting endpoints
- `ALLOWED_ORIGINS` - (optional) CORS origins, comma-separated (default: http://localhost:3000)

See `.env.example` for a template.

---

## 🧑‍💻 Local Development

- **Run API**: `uvicorn main:app --reload`
- **Test Embeddings**: `python test_embed.py`
- **Add Legal Data**: Place JSON files in `data/` and run `python store.py` to embed and store them.
- **Query CLI**: Use `python query.py` for command-line queries.

---

## 📜 License

This project is licensed under the **Business Source License 1.1** (see `LICENSE.md`).
- **Non-commercial use only** until 2027-01-01, after which it becomes Apache 2.0.
- For commercial use or SaaS, [contact the author](COMMERCIAL.md).

---

## 🤝 Contributing

We welcome contributions from everyone! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
- Code (Python, API, infra)
- Legal data (statutes, case law, etc.)
- Documentation & tutorials
- UI/UX & design

---

## 📬 Contact & Community

- [GitHub Issues](https://github.com/NyayraAI/rag-backend-python/issues)
- Email: shubhamarora2306@gmail.com

---

## ⭐️ Acknowledgements

- [Supabase](https://supabase.com/)
- [Groq](https://groq.com/)
- [SentenceTransformers](https://www.sbert.net/)
- [FastAPI](https://fastapi.tiangolo.com/)

---

*Built in public by [Shubham Arora](https://github.com/shubhamarora2306) and the NyaayraAI community.*
