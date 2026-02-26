#!/usr/bin/env python3
"""
Build embeddings for document chunks and create a FAISS index.

Usage:
  python scripts/build_embeddings.py

Creates:
- faiss_index.faiss - Vector search index
- embeddings_meta.json - Metadata mapping chunks to documents
"""

import os
import json
import sqlite3
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index.faiss')
EMBEDDINGS_META = os.getenv('EMBEDDINGS_META', 'embeddings_meta.json')


def get_chunks():
    """Fetch all chunks from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT c.chunk_id, c.doc_id, c.chunk_text, d.title
        FROM chunks c
        JOIN documents d ON c.doc_id = d.doc_id
        ORDER BY c.chunk_id
    ''')
    rows = c.fetchall()
    conn.close()
    return rows


def embed_texts_openai(texts):
    """Get embeddings from OpenAI."""
    import requests
    
    print("🔗 Using OpenAI embeddings")
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/embeddings"
    model = "text-embedding-3-small"
    batch_size = 10
    embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]
        data = {"model": model, "input": batch}
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
        j = r.json()
        for item in j['data']:
            embeddings.append(item['embedding'])
    
    return embeddings


def embed_texts_local(texts):
    """Get embeddings using local sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    
    print("🧠 Using local sentence-transformers embeddings")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True).tolist()
    return embeddings


def build_faiss(embeddings):
    """Build FAISS index from embeddings."""
    import faiss
    import numpy as np
    
    print("📦 Building FAISS index...")
    vecs = np.array(embeddings).astype('float32')
    d = vecs.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(vecs)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"✓ FAISS index saved: {FAISS_INDEX_PATH}")


def main():
    """Build embeddings and FAISS index."""
    print("Building embeddings...")
    print("=" * 60)
    
    rows = get_chunks()
    if not rows:
        print("❌ No chunks found. Run ingest first.")
        return
    
    print(f"📊 Found {len(rows)} chunks")
    
    # Extract data
    chunk_ids = [r[0] for r in rows]
    doc_ids = [r[1] for r in rows]
    texts = [r[2] for r in rows]
    titles = [r[3] for r in rows]
    
    # Build metadata
    meta = [
        {
            "chunk_id": chunk_ids[i],
            "doc_id": doc_ids[i],
            "title": titles[i]
        }
        for i in range(len(chunk_ids))
    ]
    
    # Generate embeddings
    if OPENAI_API_KEY:
        embeddings = embed_texts_openai(texts)
    else:
        embeddings = embed_texts_local(texts)
    
    # Build FAISS index
    build_faiss(embeddings)
    
    # Save metadata
    with open(EMBEDDINGS_META, 'w') as f:
        json.dump(meta, f, indent=2)
    
    print(f"✓ Metadata saved: {EMBEDDINGS_META}")
    print("\n" + "=" * 60)
    print(f"✅ Embeddings complete! {len(chunk_ids)} chunks indexed")
    print("💡 You can now use semantic search in the Streamlit app")


if __name__ == '__main__':
    main()
