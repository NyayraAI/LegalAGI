# Contributing to NyayraAI Legal RAG

Thank you for your interest in contributing! This project is built in public and welcomes contributions from everyone—developers, lawyers, designers, and enthusiasts.

---

## 🛠️ Ways to Contribute

- **Code**: Improve the backend, add features, fix bugs, or refactor code.
- **Legal Data**: Add or update statutes, case law, or other legal documents (JSON format preferred).
- **Documentation**: Improve guides, write tutorials, or clarify instructions.
- **Design & UX**: Suggest or contribute to UI/UX for future frontend integrations.
- **Testing**: Write or improve tests, report issues, or help with QA.

---

## 🧑‍💻 Local Setup

1. **Fork and clone the repo**
2. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Copy `.env.example` to `.env` and fill in required variables**
4. **Run the backend**
   ```bash
   uvicorn main:app --reload
   ```
5. **Run tests**
   ```bash
   python test_embed.py
   ```

---

## 📝 Code Style & Guidelines

- Follow [PEP8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use clear, descriptive commit messages.
- Write docstrings for public functions and classes.
- Keep code modular and well-commented.
- Add or update tests for new features or bugfixes.

---

## 🚀 Pull Request Process

1. Fork the repo and create your branch from `main`.
2. Make your changes and commit them.
3. Push to your fork and open a Pull Request (PR) on GitHub.
4. Describe your changes clearly in the PR description.
5. Link related issues if applicable.
6. Wait for review and address any feedback.

---

## 📚 Adding Legal Data

- Place new legal data files (statutes, case law, etc.) in the `data/` directory as JSON.
- Use a clear, consistent schema (see existing files for examples).
- Run `python store.py` to embed and store new data in Supabase.

---

## 🐛 Reporting Bugs & Suggesting Features

- Use [GitHub Issues](https://github.com/NyayraAI/rag-backend-python/issues) to report bugs or request features.
- Please provide as much detail as possible (steps to reproduce, expected behavior, etc.).

---

## 📜 License & Commercial Use

- This project is under the **Business Source License 1.1** (see `LICENSE.md`).
- **Non-commercial use only** until 2027-01-01, after which it becomes Apache 2.0.
- For commercial use or SaaS, see [COMMERCIAL.md](COMMERCIAL.md).

---

## 🙏 Thanks for helping build open legal AI!
