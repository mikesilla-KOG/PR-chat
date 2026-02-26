# WORKFLOW - How to Use PR-chat

This guide walks you through the typical workflow for using PR-chat.

## 1️⃣ SETUP (One-time)

```bash
# Create environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/setup_db.py

# Copy .env template
cp .env.example .env
```

If you have an OpenAI API key, add it to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

## 2️⃣ INGEST DOCUMENTS

### From File (Local)

```bash
# Transcribe an MP3 file
python scripts/ingest.py /path/to/recording.mp3 --title "My Recording"

# Extract text from a PDF
python scripts/ingest.py /path/to/document.pdf --title "My PDF"
```

### From URL

```bash
# Download and process an MP3 from a URL
python scripts/ingest.py https://prayer-resolution.com/wp-content/uploads/2021/10/Reconciliation-2021-04-28_otter_ai.mp3 --type url --title "Reconciliation"
```

### Batch Processing

```bash
# Process multiple files
for file in data/imports/*.mp3; do
    python scripts/ingest.py "$file"
done
```

## 3️⃣ BUILD SEMANTIC SEARCH INDEX

After ingesting documents, build embeddings for semantic search:

```bash
python scripts/build_embeddings.py
```

This creates:
- `faiss_index.faiss` - Vector search index
- `embeddings_meta.json` - Chunk metadata

**Note:** Only do this once after loading a batch of documents. You can re-run it anytime to rebuild with newer documents.

## 4️⃣ RUN THE APP

Launch the Streamlit interface:

```bash
streamlit run app/streamlit_app.py
```

Open http://localhost:8501 in your browser.

## 5️⃣ SEARCH & INTERACT

### Three Search Modes:

#### 💬 Ask Question
- Ask natural language questions about your documents
- System finds relevant passages and returns an AI-generated answer
- Shows sources for transparency
- **Requires:** OpenAI API key

#### 🔍 Keyword Search
- Fast full-text search across all documents
- Good for finding specific terms or phrases
- **Works without:** Any API key

#### 🧠 Semantic Search
- Find documents by meaning, not exact words
- Example: "How do I pray?" finds documents about prayer
- **Requires:** Run `build_embeddings.py` first

## 📊 CHECK STATUS

View what's in your knowledge base:

```bash
# Show statistics and documents
python scripts/demo.py --stats

# List all documents
python scripts/demo.py --list

# Verify dependencies
python scripts/verify_deps.py
```

## 🔧 COMMON TASKS

### Adding More Documents Later

```bash
# 1. Add the document
python scripts/ingest.py new_document.mp3

# 2. Rebuild embeddings
python scripts/build_embeddings.py

# 3. Restart the app (it auto-reloads)
```

### Adjusting Transcription Quality

Edit `.env` to change Whisper model:
```
LOCAL_WHISPER_MODEL=base    # Default (good balance)
LOCAL_WHISPER_MODEL=tiny    # Fast, lower quality
LOCAL_WHISPER_MODEL=small   # Better quality, slower
LOCAL_WHISPER_MODEL=medium  # Excellent quality, much slower
```

### Using OpenAI API for Transcription

By default, we use local Whisper (free, fast, offline). With OpenAI key, you get better transcription quality. No code changes needed - just add the key to `.env`.

### Checking the Database

```bash
sqlite3 pr_chat.db

# See all documents
SELECT title, content_type, COUNT(*) as chunks FROM documents d 
JOIN chunks c ON d.doc_id = c.doc_id 
GROUP BY d.doc_id;

# See all chunks
SELECT chunk_id, chunk_text FROM chunks LIMIT 5;

# Exit
.quit
```

## 🚨 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "FAISS index not found" | Run: `python scripts/build_embeddings.py` |
| Transcription is slow | Use smaller model: `LOCAL_WHISPER_MODEL=tiny` |
| PDF text extraction failed | PDF may be image-based; try a different PDF |
| No search results | Make sure you ran `build_embeddings.py` after ingesting |
| Out of memory | Reduce Whisper model size or process fewer files at once |

## 📈 PERFORMANCE TIPS

1. **Transcription:**
   - Use `tiny` model for quick tests
   - Use `base` or `small` for production
   - `medium` and `large` need more RAM

2. **Embeddings:**
   - First build might take a minute
   - Subsequent builds are faster
   - Can run in background

3. **Search:**
   - Keyword search is instant
   - Semantic search completes in seconds
   - AI chat takes 10-30 seconds (depends on OpenAI API)

## 📚 EXAMPLE WORKFLOW

```bash
# 1. Setup (once)
./quickstart.sh

# 2. Add your documents
python scripts/ingest.py my_recording.mp3 --title "First Recording"
python scripts/ingest.py my_document.pdf --title "Reference Document"
python scripts/ingest.py https://example.com/audio.mp3 --type url

# 3. Build search
python scripts/build_embeddings.py

# 4. Use it!
streamlit run app/streamlit_app.py

# 5. Add more later
python scripts/ingest.py another_file.mp3
python scripts/build_embeddings.py  # Rebuild index
```

---

**Next:** Continue with README.md for detailed feature documentation
