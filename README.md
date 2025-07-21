# NyayraAI Legal RAG Backend

[![License](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-enabled-green.svg)](https://supabase.com)

> **A Retrieval-Augmented Generation (RAG) backend for open legal AI, focused on Indian law**

NyayraAI Legal RAG Backend is an open-source system that democratizes legal knowledge by providing context-aware answers to legal questions using Indian law documents. Built with modern technologies like FastAPI, Supabase, and local embeddings, it serves as a foundation for building comprehensive legal AI assistants.

## 🌟 Key Features

- **🔍 Intelligent Legal Querying** - Ask complex legal questions and receive contextual answers based on Indian law
- **⚡ RAG Pipeline** - Advanced retrieval-augmented generation combining vector search with LLM responses
- **🧠 Local Embedding Support** - Efficient offline embeddings using SentenceTransformers
- **🔗 Supabase Integration** - Scalable document and embedding storage with hosted Postgres
- **🚀 FastAPI Architecture** - High-performance async REST API with interactive documentation
- **🔄 Flexible LLM Integration** - Default Groq API with easy provider switching
- **⚙️ Redis Caching** - Optional in-memory caching for improved performance
- **📊 Automated Data Pipeline** - Seamless data ingestion and embedding synchronization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Google Drive  │───▶│   Ingestion     │───▶│    Chunking     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Supabase Sync  │◀───│  Local Storage  │◀───│   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Vector Database │───▶│  Vector Search  │───▶│ LLM Generation  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend Framework** | FastAPI | High-performance async API |
| **Database** | Supabase (PostgreSQL) | Document and vector storage |
| **Caching** | Redis | Query and embedding caching |
| **Embeddings** | SentenceTransformers | Local text embeddings |
| **LLM Provider** | Groq API | Language model inference |
| **Runtime** | Python 3.9+ | Core application runtime |
| **Server** | Uvicorn | ASGI web server |

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- Access to Supabase project
- Groq API key (or alternative LLM provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/NyayraAI/rag-backend-python.git
   cd rag-backend-python
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Database Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   
   # LLM Configuration
   GROQ_API_KEY=your-groq-api-key
   
   # Optional: Caching
   REDIS_URL=redis://localhost:6379
   
   # Security
   BOT_API_KEY=your-internal-api-key
   ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com
   ```

4. **Start the application**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API**
   - **Interactive Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

## 📊 Data Ingestion Workflow

### 1. Document Collection
- **Google Drive Integration**: Automated polling of configured folders
- **File Processing**: Downloads PDFs to `data/raw_pdfs/`
- **Format Support**: PDF documents (JSON support planned)

### 2. Processing Pipeline
```bash
# Process and embed documents
python store.py

# Test embeddings functionality
python test_embed.py
```

### 3. Data Synchronization
- **Local Storage**: Fast retrieval from local embeddings
- **Supabase Sync**: Async background synchronization
- **Incremental Updates**: Only processes new/modified documents

## 🔧 Development Commands

### Running the Application
```bash
# Development server with auto-reload
uvicorn main:app --reload

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Data Management
```bash
# Store and embed new documents
python store.py

# Test embedding functionality
python test_embed.py

# Query the system via CLI
python query.py
```

### Testing
```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=app tests/
```

## 📁 Project Structure

```
rag-backend-python/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API routes
│   ├── core/                   # Core configuration
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic
│   └── utils/                  # Utility functions
├── data/
│   ├── raw_pdfs/              # Source PDF documents
│   └── processed/             # Processed document chunks
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── README.md                 # This file
└── LICENSE                   # License information
```

## 🔒 Security & Authentication

- **API Key Authentication**: Secure internal API access
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Environment Variables**: Sensitive data protection
- **Input Validation**: Pydantic model validation

## 🚀 Deployment

### Docker Deployment
```bash
# Build container
docker build -t nyayra-rag-backend .

# Run container
docker run -p 8000:8000 --env-file .env nyayra-rag-backend
```

### Environment-Specific Configuration
- **Development**: Auto-reload enabled, debug logging
- **Staging**: Performance optimizations, error tracking
- **Production**: Security hardening, monitoring integration

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Ways to Contribute
- **🔧 Code**: Backend development, API improvements, performance optimization
- **📚 Legal Data**: Indian statutes, case law, legal documents
- **📝 Documentation**: Tutorials, API docs, deployment guides
- **🎨 UI/UX**: Frontend integration, user experience improvements
- **🧪 Testing**: Unit tests, integration tests, performance testing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the **Business Source License 1.1**:

- ❌ **Non-commercial use only** until January 1, 2027
- ✅ **Converts to Apache 2.0** after the change date
- 💼 **Commercial licensing** available - [contact us](mailto:shubhamarora2306@gmail.com)

See the [LICENSE](LICENSE) file for full details.

## 📞 Support & Community

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/NyayraAI/rag-backend-python/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/NyayraAI/rag-backend-python/discussions)
- **📧 Direct Contact**: [shubhamarora2306@gmail.com](mailto:shubhamarora2306@gmail.com)
- **🌐 Website**: [NyayraAI](https://nyayra.ai) *(coming soon)*

## 🙏 Acknowledgements

We're grateful to the open-source community and these amazing projects:

- [Supabase](https://supabase.com) - Backend-as-a-Service platform
- [Groq](https://groq.com) - High-performance LLM inference
- [SentenceTransformers](https://www.sbert.net) - State-of-the-art embeddings
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework

---

<div align="center">

**Built with ❤️ by [Shubham Arora](https://github.com/shubhamarora) and the NyayraAI community**

[⭐ Star this project](https://github.com/NyayraAI/LegalAGI) | [🍴 Fork it](https://github.com/NyayraAI/LegalAGI/fork) | [📝 Contribute](CONTRIBUTING.md)

</div>