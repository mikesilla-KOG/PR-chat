# PR-chat - AI-Powered Knowledge Base Search

Build a searchable knowledge base from your documents (MP3s, PDFs, URLs) with AI-powered semantic search and intelligent Q&A.

## Features

- **Multi-source Ingest**: Upload MP3s, PDFs, or provide URLs
- **Automatic Transcription**: Convert MP3s to text using local Whisper (free, offline)
- **PDF Extraction**: Automatically extract text from PDFs
- **Keyword Search**: Fast full-text search (SQLite FTS5)
- **Semantic Search**: Find documents by meaning using FAISS vector search
- **AI Chat with RAG**: Ask questions and get answers based on your documents
- **Streamlit UI**: Beautiful, interactive web interface

## Project Structure

```
PR-chat/
├── app/
│   └── streamlit_app.py          # Main web interface
├── scripts/
│   ├── setup_db.py               # Initialize database
│   ├── ingest.py                 # Ingest documents (MP3, PDF, URLs)
│   └── build_embeddings.py       # Build FAISS index for semantic search
├── data/
│   ├── uploads/                  # Uploaded files
│   └── transcripts/              # MP3 transcriptions (JSON)
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Quick Start

### 1. Setup

```bash
# Clone or navigate to the repo
cd PR-chat

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example .env
cp .env.example .env

# (Optional) If you have OpenAI API key, add it to .env:
# OPENAI_API_KEY=sk-...
```

### 3. Initialize Database

```bash
python scripts/setup_db.py
```

This creates the SQLite database with tables for documents, chunks, and chat history.

### 4. Ingest Documents

Choose one or more:

```bash
# Upload local MP3 (will be transcribed with Whisper)
python scripts/ingest.py data/my_file.mp3 --title "My Document"

# Upload local PDF (text will be extracted)
python scripts/ingest.py data/my_file.pdf --title "My PDF"

# Download and process MP3 from URL
python scripts/ingest.py https://example.com/audio.mp3 --type url --title "Downloaded Audio"
```

### 5. Build Embeddings (for Semantic Search)

After ingesting documents, build the FAISS index:

```bash
python scripts/build_embeddings.py
```

This creates:
- `faiss_index.faiss` - Vector search index
- `embeddings_meta.json` - Chunk metadata

### 6. Run the App

```bash
streamlit run app/streamlit_app.py
```

Open http://localhost:8501 in your browser.

## Usage

### Upload Documents (Sidebar)

1. Select upload type: **File** or **URL**
2. For files: Choose MP3 or PDF from your computer
3. For URLs: Paste the MP3 URL and optional title
4. Click upload button - processing happens automatically

### Search Modes

#### 💬 Ask Question
Ask natural language questions about your entire knowledge base. The system:
1. Finds relevant documents using semantic search
2. Feeds them to OpenAI GPT for intelligent answering
3. Shows sources for transparency

*Requires: OpenAI API key in `.env`*

#### 🔍 Keyword Search
Fast full-text search across all documents. Good for finding specific terms or phrases.

*No API key required*

#### 🧠 Semantic Search
Find documents by meaning, even with different wording. Example:
- Query: "How do I pray?"
- Returns: Documents about prayer, meditation, spiritual practices

*Requires: Run `build_embeddings.py` first*

## Configuration

### `.env` Variables

```bash
# Database
DB_PATH=pr_chat.db

# Directories
UPLOADS_DIR=data/uploads
TRANSCRIPTS_DIR=data/transcripts

# Embeddings
FAISS_INDEX_PATH=faiss_index.faiss
EMBEDDINGS_META=embeddings_meta.json

# Whisper transcription model (options: tiny, base, small, medium, large)
# Larger = better quality but slower
LOCAL_WHISPER_MODEL=base

# Optional: OpenAI for better features
OPENAI_API_KEY=sk-...
```

## Whisper Model Sizes

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `tiny` | 39M | ⚡⚡⚡ | Fair |
| `base` | 140M | ⚡⚡ | Good |
| `small` | 466M | ⚡ | Very Good |
| `medium` | 1.5G | 🐌 | Excellent |
| `large` | 2.9G | 🐌🐌 | Best |

For most use cases, `base` is a good balance. Use `tiny` for quick testing.

## Advanced

### Batch Ingest

Process multiple files:

```bash
for file in data/imports/*.mp3; do
    python scripts/ingest.py "$file"
done
```

### Rebuild Embeddings

If you add many documents, rebuild the index:

```bash
python scripts/build_embeddings.py
```

### Database Queries

Check what's in your knowledge base:

```bash
sqlite3 pr_chat.db
SELECT title, content_type, COUNT(*) as chunks FROM documents d 
JOIN chunks c ON d.doc_id = c.doc_id 
GROUP BY d.doc_id;
```

## Troubleshooting

### "FAISS index not found"
Run: `python scripts/build_embeddings.py`

### MP3 transcription is slow
- Use smaller Whisper model: `LOCAL_WHISPER_MODEL=tiny`
- Or set up OpenAI API for faster transcription

### PDF extraction failed
- Check if PDF is text-based (not scanned image)
- Try a different PDF tool or manually paste text

### "No relevant documents found"
- Make sure you've ingested documents and run `build_embeddings.py`
- Try keyword search first to verify documents exist

## Architecture

```
Upload (MP3/PDF/URL)
    ↓
[Whisper OR PDF Extractor] → Text
    ↓
SQLite Database (documents + FTS index)
    ↓
Text Chunking (1000 char chunks, 200 char overlap)
    ↓
Chunks Table
    ↓
[Sentence Transformers OR OpenAI] → Embeddings
    ↓
FAISS Index
    ↓
[Semantic Search ← Query]  [Keyword Search ← Query]
    ↓                            ↓
[OpenAI Chat] ← Top Results ← Results
    ↓
Answer with Sources
```

## Requirements

- Python 3.8+
- ~2GB disk space (for Whisper base model + databases)
- ~2GB RAM minimum
- Internet connection (for downloads, transcriptions, chat)

## Deployment

You can deploy this app to Streamlit Cloud just like SermonsKB. See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions; essentially you point Streamlit Cloud at `app/streamlit_app.py`, set any secrets (e.g. `OPENAI_API_KEY`), and optionally commit the `pr_chat.db` and FAISS index files to the repo so the site comes up pre‑populated.

For simple hosting, the free Streamlit Cloud tier works out of the box and gives you a public URL similar to `https://sermonskb.streamlit.app/`.

---

## API Keys

### Optional: OpenAI

For better transcriptions and AI chat:

1. Get API key from https://platform.openai.com/
2. Add to `.env`: `OPENAI_API_KEY=sk-...`

No API key needed for local features (Whisper transcription, keyword/semantic search).

## Next Steps

- [ ] Upload your first document
- [ ] Search across your knowledge base
- [ ] Try semantic search and Q&A
- [ ] Adjust Whisper model size based on speed/quality needs
- [ ] Consider adding OpenAI key for better chat experience

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review database queries to verify data
3. Check logs from `scripts/ingest.py` for detailed errors

## License

MIT

---

**Built with:** Streamlit • Whisper • FAISS • SQLite • Sentence Transformers • OpenAI
