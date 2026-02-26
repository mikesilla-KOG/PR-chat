import os
import sqlite3
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import numpy as np
from urllib.parse import quote

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')
UPLOADS_DIR = os.getenv('UPLOADS_DIR', 'data/uploads')
TRANSCRIPTS_DIR = os.getenv('TRANSCRIPTS_DIR', 'data/transcripts')
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index.faiss')
EMBEDDINGS_META = os.getenv('EMBEDDINGS_META', 'embeddings_meta.json')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Streamlit page config
st.set_page_config(
    page_title="PR-chat - Knowledge Base Search",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling
st.markdown("""
<style>
    .main {
        padding: 0;
    }
    .search-result {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    .source-badge {
        display: inline-block;
        background-color: #667eea;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .source-type {
        font-size: 11px;
        opacity: 0.8;
    }
    .transcript-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
    }
    .audio-player-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0 15px 0;
        border: 2px solid #4caf50;
    }
    .answer-box {
        background-color: #e6f2ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .chunk-highlight {
        background-color: #fff59d;
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_db():
    """Initialize database if not exists."""
    if not os.path.exists(DB_PATH):
        st.info("Initializing database...")
        os.system(f"python scripts/setup_db.py")


def get_document_info(doc_id):
    """Get document metadata."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT doc_id, title, content_type, source_path, created_at, full_text
            FROM documents
            WHERE doc_id = ?
        ''', (doc_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'doc_id': row[0],
                'title': row[1],
                'content_type': row[2],
                'source_path': row[3],
                'created_at': row[4],
                'full_text': row[5]
            }
        return None
    except:
        return None


def get_document_audio(doc_id):
    """Get audio file path for a document."""
    doc_info = get_document_info(doc_id)
    if not doc_info:
        return None
    
    if doc_info['content_type'].lower() == 'mp3':
        source_path = doc_info['source_path']
        # Check if file exists
        if os.path.exists(source_path):
            return source_path
    
    return None


def display_audio_player(doc_id, title):
    """Display audio player for MP3 documents."""
    audio_path = get_document_audio(doc_id)
    
    if audio_path and os.path.exists(audio_path):
        st.markdown(f'<div class="audio-player-box">', unsafe_allow_html=True)
        st.markdown(f'**🎙️ Audio: {title}**')
        
        try:
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format='audio/mp3')
        except Exception as e:
            st.warning(f"Could not load audio file: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_transcript(doc_id, title, highlight_chunk=None):
    """Display full transcript of a document."""
    doc_info = get_document_info(doc_id)
    
    if not doc_info or not doc_info['full_text']:
        st.info("No transcript available")
        return
    
    st.markdown("### 📜 Full Transcript")
    
    # Create expandable transcript section
    with st.expander("View complete transcript", expanded=False):
        full_text = doc_info['full_text']
        
        # Highlight the chunk if provided
        if highlight_chunk:
            # Simple highlight - wrap the chunk in special markers
            display_text = full_text.replace(
                highlight_chunk[:100],
                f"**[>>> MATCH: {highlight_chunk[:100]}... <<<]**"
            )
        else:
            display_text = full_text
        
        st.markdown(f'<div class="transcript-box">{display_text}</div>', unsafe_allow_html=True)
        
        # Option to download transcript
        st.download_button(
            label="📥 Download Transcript",
            data=full_text,
            file_name=f"{title}_transcript.txt",
            mime="text/plain",
            key=f"download_{doc_id}"
        )


def get_db_stats():
    """Get database statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM documents')
        doc_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM chunks')
        chunk_count = c.fetchone()[0]
        
        conn.close()
        return doc_count, chunk_count
    except:
        return 0, 0


def keyword_search(query, limit=10):
    """Search using FTS5."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # FTS5 search - now also returns doc_id and content_type
        c.execute('''
            SELECT DISTINCT d.doc_id, d.title, d.content_type, c.chunk_text, c.chunk_id
            FROM documents_fts f
            JOIN documents d ON f.doc_id = d.doc_id
            JOIN chunks c ON d.doc_id = c.doc_id
            WHERE documents_fts MATCH ?
            LIMIT ?
        ''', (query, limit))
        
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        st.error(f"Search error: {e}")
        return []


def semantic_search(query, top_k=5):
    """Search using FAISS embeddings."""
    try:
        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(EMBEDDINGS_META):
            st.error("🔍 Semantic search not available. Please run: `python scripts/build_embeddings.py`")
            return []
        
        import faiss
        from sentence_transformers import SentenceTransformer
        
        # Get query embedding
        model = SentenceTransformer('all-MiniLM-L6-v2')
        qvec = model.encode([query])[0].astype('float32')
        
        # Search FAISS
        index = faiss.read_index(FAISS_INDEX_PATH)
        D, I = index.search(np.array([qvec]), top_k)
        
        # Get metadata
        with open(EMBEDDINGS_META, 'r') as f:
            meta = json.load(f)
        
        # Fetch chunks from database with content_type
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        results = []
        for idx in I[0]:
            if 0 <= idx < len(meta):
                chunk_id = meta[idx]['chunk_id']
                doc_id = meta[idx]['doc_id']
                title = meta[idx]['title']
                
                c.execute('SELECT chunk_text FROM chunks WHERE chunk_id = ?', (chunk_id,))
                row = c.fetchone()
                
                # Get content type
                c.execute('SELECT content_type FROM documents WHERE doc_id = ?', (doc_id,))
                doc_row = c.fetchone()
                content_type = doc_row[0] if doc_row else 'unknown'
                
                if row:
                    results.append((doc_id, title, content_type, row[0], chunk_id))
        
        conn.close()
        return results
    except Exception as e:
        st.error(f"Semantic search error: {e}")
        return []


def ingest_file(uploaded_file):
    """Ingest uploaded file."""
    try:
        # Save to temp location
        temp_path = os.path.join(UPLOADS_DIR, uploaded_file.name)
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Run ingest script
        os.system(f"python scripts/ingest.py {temp_path}")
        
        return True
    except Exception as e:
        st.error(f"Upload error: {e}")
        return False


def ingest_url(url, title=None):
    """Ingest from URL."""
    try:
        os.system(f"python scripts/ingest.py {url} --type url --title {title or 'downloaded'}")
        return True
    except Exception as e:
        st.error(f"URL error: {e}")
        return False


def generate_answer(query, context_chunks, context_titles):
    """Generate answer using OpenAI."""
    if not OPENAI_API_KEY:
        return "OpenAI API key not set. Please set OPENAI_API_KEY environment variable."
    
    try:
        import requests
        
        context = "\n\n".join([
            f"[From: {title}]\n{chunk}"
            for chunk, title in zip(context_chunks, context_titles)
        ])
        
        prompt = f"""You are a helpful assistant that answers questions based on provided documents.
Use the following document excerpts to answer the question. Be thorough and cite the source document.

Document Context:
{context}

Question: {query}

Answer:"""
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error generating answer: {e}"


# Main UI
st.markdown("<h1 style='text-align: center;'>📚 PR-chat Knowledge Base</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6c757d;'>Upload documents and search with AI</p>", unsafe_allow_html=True)

initialize_db()

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Statistics")
    doc_count, chunk_count = get_db_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", doc_count)
    with col2:
        st.metric("Chunks", chunk_count)
    
    st.markdown("---")
    st.markdown("### 📤 Upload Documents")
    
    upload_type = st.radio("Upload Type", ["File", "URL"])
    
    if upload_type == "File":
        uploaded_file = st.file_uploader(
            "Choose file (MP3 or PDF)",
            type=["mp3", "pdf"],
            help="Upload MP3 for transcription or PDF for text extraction"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Upload & Process"):
                with st.spinner("Processing file..."):
                    if ingest_file(uploaded_file):
                        st.success(f"✅ Processed: {uploaded_file.name}")
                        st.rerun()
    
    else:  # URL
        url = st.text_input("Enter MP3 URL")
        title = st.text_input("Document title (optional)")
        
        if url and st.button("📥 Download & Process"):
            with st.spinner("Downloading and processing..."):
                if ingest_url(url, title):
                    st.success("✅ Processed URL")
                    st.rerun()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Ask Question", "🔍 Keyword Search", "🧠 Semantic Search", "📜 Browse Docs"])

# Tab 1: AI Chat with RAG
with tab1:
    st.markdown("### 💬 Ask a Question")
    st.markdown("Ask any question about your documents and get AI-powered answers with sources.")
    
    if not OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API key not set. AI chat requires `OPENAI_API_KEY` in .env")
    else:
        query = st.text_input("Your question:", placeholder="What is this document about?", key="ai_question")
        col1, col2 = st.columns([3, 1])
        with col2:
            top_k = st.slider("Results", 3, 10, 5)
        
        if query and st.button("🔍 Get Answer", type="primary"):
            with st.spinner("Searching and generating answer..."):
                # Get relevant chunks
                results = semantic_search(query, top_k)
                
                if results:
                    # Extract data from new result format
                    doc_ids = [r[0] for r in results]
                    context_chunks = [r[3] for r in results]  # chunk is at index 3
                    context_titles = [r[1] for r in results]  # title is at index 1
                    content_types = [r[2] for r in results]   # content_type is at index 2
                    
                    # Generate answer
                    answer = generate_answer(query, context_chunks, context_titles)
                    
                    # Display answer
                    st.markdown("### 🤖 Answer")
                    st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown(f"### 📚 Source Documents ({len(results)} referenced)")
                    
                    # Display each source with audio and transcript
                    for i, (doc_id, title, content_type, chunk) in enumerate(results, 1):
                        with st.expander(f"{i}. 🎙️ {title} ({content_type.upper()})"):
                            # Show source badge
                            icon = "🎙️" if content_type == "mp3" else "📄"
                            st.markdown(f'<span class="source-badge">{icon} From: {title}</span>', unsafe_allow_html=True)
                            
                            # Audio player if MP3
                            if content_type == "mp3":
                                display_audio_player(doc_id, title)
                            
                            # Show the relevant passage used in answer
                            st.markdown("**Passage used in answer:**")
                            st.markdown(f'<div class="search-result"><p>{chunk[:300]}...</p></div>', unsafe_allow_html=True)
                            
                            # Show full transcript
                            display_transcript(doc_id, title, highlight_chunk=chunk)
                else:
                    st.info("No relevant documents found.")

# Tab 2: Keyword Search
with tab2:
    st.markdown("### 🔎 Keyword Search")
    st.markdown("Fast full-text search across all documents")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Search keywords:", placeholder="Search documents...", key="kw_search")
    with col2:
        limit = st.number_input("Results", 1, 50, 10, key="kw_limit")
    
    if query and query.strip():
        results = keyword_search(query, limit)
        if results:
            st.success(f"✨ Found {len(results)} results")
            
            for i, (doc_id, title, content_type, snippet, chunk_id) in enumerate(results, 1):
                with st.expander(f"{i}. 🎙️ {title} ({content_type.upper()})", expanded=False):
                    # Show source badge
                    icon = "🎙️" if content_type == "mp3" else "📄"
                    st.markdown(f'<span class="source-badge">{icon} From: {title}</span>', unsafe_allow_html=True)
                    
                    # Audio player if MP3
                    if content_type == "mp3":
                        display_audio_player(doc_id, title)
                    
                    # Show the chunk
                    st.markdown("**Found in:**")
                    st.markdown(f'<div class="search-result"><p>{snippet[:300]}...</p></div>', unsafe_allow_html=True)
                    
                    # Show full transcript
                    display_transcript(doc_id, title, highlight_chunk=snippet)
        else:
            st.info("No results found.")

# Tab 3: Semantic Search
with tab3:
    st.markdown("### 🧠 Semantic Search")
    st.markdown("Find documents by meaning, not just keywords")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Describe what you're looking for:", placeholder="What do you want to find?", key="sem_search")
    with col2:
        top_k = st.number_input("Results", 1, 20, 5, key="sem_top_k")
    
    if query:
        with st.spinner("🔍 Searching..."):
            results = semantic_search(query, top_k)
            
            if results:
                st.success(f"✨ Found {len(results)} relevant passages")
                
                for i, (doc_id, title, content_type, chunk, chunk_id) in enumerate(results, 1):
                    with st.expander(f"{i}. 🎙️ {title} ({content_type.upper()})", expanded=False):
                        # Show source badge
                        icon = "🎙️" if content_type == "mp3" else "📄"
                        st.markdown(f'<span class="source-badge">{icon} From: {title}</span>', unsafe_allow_html=True)
                        
                        # Audio player if MP3
                        if content_type == "mp3":
                            display_audio_player(doc_id, title)
                        
                        # Show the relevant chunk
                        st.markdown("**Relevant passage:**")
                        st.markdown(f'<div class="search-result"><p>{chunk}</p></div>', unsafe_allow_html=True)
                        
                        # Show full transcript
                        display_transcript(doc_id, title, highlight_chunk=chunk)
            else:
                st.info("No relevant documents found.")

# Tab 4: Browse Documents
with tab4:
    st.markdown("### 📜 Browse All Documents")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT doc_id, title, content_type, created_at
            FROM documents
            ORDER BY created_at DESC
        ''')
        
        docs = c.fetchall()
        conn.close()
        
        if docs:
            for doc_id, title, content_type, created_at in docs:
                icon = "🎙️" if content_type == "mp3" else "📄"
                with st.expander(f"{icon} {title} ({content_type.upper()})"):
                    st.caption(f"Added: {created_at}")
                    
                    # Show chunk count
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('SELECT COUNT(*) FROM chunks WHERE doc_id = ?', (doc_id,))
                    chunk_count = c.fetchone()[0]
                    conn.close()
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.metric("Chunks", chunk_count)
                    
                    # Audio player if MP3
                    if content_type == "mp3":
                        display_audio_player(doc_id, title)
                    
                    # Show transcript
                    display_transcript(doc_id, title)
        else:
            st.info("No documents uploaded yet. Use the sidebar to add documents!")
    except Exception as e:
        st.error(f"Error loading documents: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 12px;">
    <p>💡 <b>Tip:</b> Run `python scripts/build_embeddings.py` after uploading documents to enable semantic search</p>
    <p>📚 PR-chat Knowledge Base | Built with Streamlit • OpenAI • FAISS</p>
</div>
""", unsafe_allow_html=True)
