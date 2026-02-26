# ARCHITECTURE - How PR-chat Works

## System Overview

PR-chat is a knowledge base search system that combines multiple technologies:

```
INPUT
  ↓
[MP3] → Whisper (transcription)
[PDF] → PyPDF2 (text extraction)
[URL] → Download + process
  ↓
TEXT
  ↓
SQLite Database (documents + metadata)
  ↓
INDEXING & SEARCH
  ├─ Keyword Index: SQLite FTS5 (full-text search)
  ├─ Semantic Index: FAISS + embeddings
  ├─ Chunks Table: Text segments linked to documents
  └─ Metadata: Document references
  ↓
RETRIEVAL & RESPONSE
  ├─ Semantic Search: Find similar passages
  ├─ Keyword Search: Find exact matches
  └─ AI Chat: Combine results + OpenAI for answer
  ↓
USER INTERFACE (Streamlit)
```

## Components

### 1. Database (SQLite)

**Schema:**
```
documents
├── doc_id (primary key)
├── source_type (upload/url/text)
├── source_path (file path or URL)
├── title
├── content_type (mp3/pdf/text)
├── full_text
└── created_at

documents_fts (Full-Text Search virtual table)
├── doc_id
├── title
└── full_text

chunks
├── chunk_id (primary key)
├── doc_id (foreign key)
├── chunk_order
├── chunk_text
└── created_at

chat_history
├── message_id
├── session_id
├── role (user/assistant)
├── content
├── sources
└── created_at
```

### 2. Text Processing Pipeline

```
Input File
    ↓
┌─────────────────────────────────────┐
│ File Type Detection                 │
└─────────────────────────────────────┘
    ↓
    ├─→ MP3 ──→ [Whisper] ──→ Raw Text
    │
    ├─→ PDF ──→ [PyPDF2] ──→ Raw Text
    │
    └─→ URL ──→ [Download] ──→ (repeat above)
    ↓
    Raw Text
    ↓
┌─────────────────────────────────────┐
│ Text Normalization                  │
│ - Strip whitespace                  │
│ - Remove artifacts                  │
│ - Verify minimum length             │
└─────────────────────────────────────┘
    ↓
    Cleaned Text
    ↓
    Store in documents.full_text
    ↓
┌─────────────────────────────────────┐
│ Chunking (1000 char, 200 overlap)   │
│ - Split on 1000-char boundaries     │
│ - 200-char overlap between chunks   │
│ - Preserve context                  │
└─────────────────────────────────────┘
    ↓
    Chunks (inserted into chunks table)
```

### 3. Indexing

#### Keyword Search (FTS5)
```
Raw Text
    ↓
[SQLite FTS5 Tokenizer]
    ↓
Inverted Index
    ↓
Enables: SELECT WHERE full_text MATCH 'query'
```

#### Semantic Search (FAISS)
```
Chunks (from chunks table)
    ↓
[Sentence Transformers: all-MiniLM-L6-v2]
    ↓
Vector Embeddings (384 dimensions)
    ↓
[FAISS Index]
    ├─ IndexFlatL2 (Euclidean distance)
    └─ Serialized to faiss_index.faiss
    ↓
Metadata: chunk_id → doc_id → title
    (saved as embeddings_meta.json)
```

### 4. Search Execution

#### Keyword Search
```
User Query
    ↓
[SQLite FTS5 Query]
    ↓
SELECT FROM documents_fts WHERE MATCH 'query'
    ↓
Return: doc_id, title, chunk_text
    ↓
Display Results
```

#### Semantic Search
```
User Query
    ↓
[Sentence Transformers]
    ↓
Query Vector (384 dimensions)
    ↓
[FAISS Index Search]
    ├─ k=top_k (usually 5)
    ├─ Compute distances
    └─ Return top indices
    ↓
[Look up in embeddings_meta.json]
    ├─ chunk_id → doc_id
    └─ doc_id → title
    ↓
[Fetch from chunks table]
    └─ Retrieve actual chunk text
    ↓
Display Results + Relevance
```

#### AI Chat (RAG Pattern)
```
User Query
    ↓
[Semantic Search] → Top 5 passages
    ↓
Context Assembly
    ├─ Passage 1: "[From: Document 1] text..."
    ├─ Passage 2: "[From: Document 2] text..."
    └─ ...
    ↓
Prompt Construction
    ├─ Context (top passages)
    ├─ Query (user question)
    └─ Instructions (system prompt)
    ↓
[OpenAI API: gpt-4o-mini]
    ├─ POST to chat/completions
    ├─ max_tokens: 1200
    └─ temperature: 0.7
    ↓
Generated Answer
    ├─ Natural language response
    └─ Based on document context
    ↓
Display Answer + Sources
```

## File Processing Flow

### MP3 Upload
```
1. User uploads MP3
2. Save to data/uploads/
3. Load with Whisper model
4. Transcribe to text
5. Save JSON to data/transcripts/
6. Insert into documents table
7. Create chunks
8. Insert into chunks table
```

### PDF Upload
```
1. User uploads PDF
2. Save to data/uploads/
3. Read with PyPDF2
4. Extract text from pages
5. Combine into single document
6. Insert into documents table
7. Create chunks
8. Insert into chunks table
```

### URL Download
```
1. User provides URL
2. HTTP GET with streaming
3. Save to data/uploads/
4. Determine file type
5. Process as MP3 or PDF
```

## Performance Characteristics

### Ingestion
| Operation | Time | Notes |
|-----------|------|-------|
| MP3 Transcribe (tiny) | 30-60s | Fast model |
| MP3 Transcribe (base) | 1-3m | Good quality |
| PDF Extract | 5-15s | Depends on size |
| Chunking | <1s | Fast |
| DB Insert | 1-2s | Batch insert |

### Search
| Operation | Time | Notes |
|-----------|------|-------|
| Keyword search | 10-100ms | Instant (FTS5) |
| Semantic search | 1-3s | Vector similarity |
| AI Chat generation | 10-30s | OpenAI API |

### Storage
| Component | Size | Notes |
|-----------|------|-------|
| SQLite DB | ~10MB | Per 100 documents |
| FAISS Index | ~500MB | Per 100,000 chunks |
| Metadata JSON | ~2MB | Per 100,000 chunks |

## Data Flow Diagram

```
┌─ UPLOAD ─────────────────────────────────┐
│ MP3/PDF/URL                             │
└──────────────────────────────────────────┘
        ↓
┌─ PROCESS ────────────────────────────────┐
│ Transcribe/Extract/Download             │
└──────────────────────────────────────────┘
        ↓
┌─ STORE ───────────────────────────────────┐
│ SQLite: documents, chunks tables        │
└──────────────────────────────────────────┘
        ↓
┌─ BUILD ───────────────────────────────────┐
│ Embeddings + FAISS Index                │
└──────────────────────────────────────────┘
        ↓
    ┌───────────────────────────┐
    │    SEARCH REQUEST        │
    │ (UI: Keyword/Semantic)   │
    └───────────────────────────┘
        ↓↓↓
┌─────────────────────────────────────────┐
│ KEYWORD SEARCH          SEMANTIC SEARCH  │
│ FTS5 + SQLite           FAISS + Embeddings
│ ↓                       ↓                 │
│ Results                 Results           │
└─────────────────────────────────────────┘
        ↓
    ┌───────────────────────────┐
    │  AI CHAT REQUEST?         │
    │  (Generate Answer)        │
    └───────────────────────────┘
        ↓
┌─ GENERATE ────────────────────────────────┐
│ OpenAI: Combine results + prompt         │
└──────────────────────────────────────────┘
        ↓
┌─ RESPONSE ────────────────────────────────┐
│ Display answer + sources to user         │
└──────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Streamlit | Web interface |
| **Processing** | Whisper | Audio transcription |
| | PyPDF2 | PDF text extraction |
| | sentence-transformers | Embeddings |
| **Storage** | SQLite | Full database |
| | SQLite FTS5 | Keyword indexing |
| **Search** | FAISS | Semantic search |
| **AI** | OpenAI API | Chat/generation |
| **Infrastructure** | Python 3.8+ | Runtime |

## Extensibility

This architecture can be extended with:
1. **More file types:** Docx, images (OCR), videos, audio formats
2. **Better embeddings:** OpenAI embeddings for higher accuracy
3. **UI improvements:** Dark mode, filters, analytics
4. **Advanced search:** Filters by date, source, relevance
5. **Persistence:** Chat history, saved searches
6. **Multi-user:** Session management, permissions
7. **Deployment:** Docker, cloud hosting (Streamlit Cloud, Heroku)

---

**See also:** README.md, WORKFLOW.md, QUICK_REFERENCE.md
