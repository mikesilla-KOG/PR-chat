# QUICK REFERENCE - CLI Commands

## Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/setup_db.py
```

## Ingest Documents

```bash
# Local MP3 (will be transcribed)
python scripts/ingest.py /path/to/file.mp3 --title "Title"

# Local PDF (text extraction)
python scripts/ingest.py /path/to/file.pdf --title "Title"

# From URL
python scripts/ingest.py https://example.com/file.mp3 --type url --title "Title"

# Batch process
for file in *.mp3; do python scripts/ingest.py "$file"; done
```

## Build Embeddings & Search

```bash
# Build FAISS index for semantic search
python scripts/build_embeddings.py

# Rebuild if you add many new documents
python scripts/build_embeddings.py
```

## Run

```bash
# Launch web interface
streamlit run app/streamlit_app.py

# Open: http://localhost:8501
```

## Status & Debugging

```bash
# Show statistics
python scripts/demo.py --stats

# List all documents
python scripts/demo.py --list

# Verify dependencies
python scripts/verify_deps.py

# Add sample data (for testing)
python scripts/add_samples.py
```

## Database Queries

```bash
# Connect to database
sqlite3 pr_chat.db

# See all documents
SELECT doc_id, title, content_type FROM documents;

# See chunks
SELECT chunk_id, doc_id FROM chunks LIMIT 10;

# See stats
SELECT COUNT(*) as total_chunks FROM chunks;

# Exit
.quit
```

## Configuration

```bash
# Copy template
cp .env.example .env

# Edit .env with your settings:
# - OpenAI API key (optional)
# - Whisper model size
# - File paths
```

## Environment Variables

```bash
DB_PATH=pr_chat.db
UPLOADS_DIR=data/uploads
TRANSCRIPTS_DIR=data/transcripts
FAISS_INDEX_PATH=faiss_index.faiss
EMBEDDINGS_META=embeddings_meta.json
LOCAL_WHISPER_MODEL=base
OPENAI_API_KEY=sk-...  # optional
```

## Troubleshooting

```bash
# Check what went wrong
python scripts/verify_deps.py

# Rebuild everything
rm pr_chat.db faiss_index.faiss embeddings_meta.json
python scripts/setup_db.py
python scripts/build_embeddings.py
```

---

**Full docs:** See README.md and WORKFLOW.md
