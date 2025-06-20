# RAG‑Pipeline Prototype

A **local‑first Retrieval‑Augmented‑Generation platform** for turning mixed organisational content (PDFs, office docs, presentations, emails, images, websites, etc.) into an interactive knowledge base.  
Built for librarians, researchers and other knowledge‑workers who need reliable answers from their in‑house documentation without sending private data to external services.

<p align="center">
  <img src="https://raw.githubusercontent.com/your‑org/rag‑pipeline/main/docs/architecture_simplified.png" width="600" alt="High‑level architecture"/>
</p>

---

## ✨ Key Features (v0.1)

* **Drag‑and‑drop ingestion** for TXT, PDF, PPTX, DOCX, XLSX/CSV, images, email files and public URLs (up to **1 GB** total).
* **Source‑aware chunking** – pluggable rule‑sets per file type.
* **Hybrid embeddings** – choose local HuggingFace models *or* OpenAI API with one click.
* **FAISS vector search** with late‑fusion across source types.
* **Streamlit UI** – create projects, upload data, run queries and view logs without touching the CLI.
* **Answer generation** with citations using your preferred chat‑LLM endpoint.
* 100 % offline data storage – raw files, vectors and logs stay on your machine.

See the full [Roadmap](docs/rag_prototype_roadmap.md) for detailed design and future milestones.

---

## 🚀 Quick Start

For detailed project setup, directory structure, and `config.yml` configuration, please see [Project Setup and Configuration](docs/project_setup.md).

```bash
# 1. Clone & install
git clone https://github.com/your‑org/rag‑pipeline.git
cd rag‑pipeline
# Poetry is the recommended method for managing dependencies and ensuring a consistent environment.
poetry install

# Alternatively, you can use pip with requirements.txt,
# but ensure it includes all necessary packages (see "Requirements" section below).
# pip install -r requirements.txt

# 2. Launch Streamlit UI
poetry run streamlit run app/ui_streamlit.py   # default browser opens

# 3. Create a new project in the UI, upload some PDFs, and ask a question!
```

> **Tip:** Prefer local embeddings? Select **bge‑large‑en** under *Settings → Embeddings* before indexing.

---

## 🗂️ Folder Structure (excerpt)

```text
rag‑pipeline/
├── app/                 # CLI & Streamlit entry‑points
├── scripts/             # Core library (ingestion, chunking, embeddings…)
├── configs/             # YAML templates for datasets & tasks
├── data/                # Your local datasets, chunks & indexes (git‑ignored)
├── docs/                # Technical docs & design diagrams
└── tests/               # Pytest suite
```

For a full tree and design conventions, check the [Codebase Structure](docs/rag_prototype_roadmap.md#10  repository--codebase-structure).
**(Note: This link currently appears to be broken as `docs/rag_prototype_roadmap.md` is missing.)**

---

## 🛠️ Requirements

**System & Python:**
* **Python 3.12** (pip should be available as part of your Python installation)
* **Tesseract OCR** (optional, for image ingestion). Install via your OS package manager. For example:
    * Debian/Ubuntu: `sudo apt-get install tesseract-ocr`
    * macOS (using Homebrew): `brew install tesseract`
* For OpenAI or other API models: set `OPENAI_API_KEY` or relevant environment variables.

**Python Dependencies:**
Poetry is the recommended tool for installing and managing Python dependencies. It ensures all required packages, including `streamlit` and `typer`, are installed correctly by using the `pyproject.toml` file.

If you choose to use `pip install -r requirements.txt` instead of Poetry:
* Be aware that `requirements.txt` may not always be up-to-date with all interactive dependencies like `streamlit` and `typer`. For full functionality, these packages would need to be included.
* It is recommended to generate `requirements.txt` from `pyproject.toml` if maintaining this installation path.

---

## 🤝 Contributing

Pull requests are welcome! Please read **CONTRIBUTING.md** (to be added) and open an issue before starting major work.

---

## 📜 License

This project is released under the MIT License © 2025 — see [LICENSE](LICENSE) for details.

---

> *Built with ❤️ and lots of coffee by the Library Innovation Lab.*  
> *“Organisational knowledge belongs at your fingertips.”*
