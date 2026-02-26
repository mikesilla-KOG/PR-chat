#!/usr/bin/env python3
"""
Ingest documents into the knowledge base.
Handles:
- Direct file uploads (MP3, PDF)
- URLs (MP3 downloads)
- Transcription with local Whisper
- PDF text extraction
- Text chunking and storage
"""

import os
import sys
import sqlite3
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

# Third-party imports
import requests
from tqdm import tqdm

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')
UPLOADS_DIR = os.getenv('UPLOADS_DIR', 'data/uploads')
TRANSCRIPTS_DIR = os.getenv('TRANSCRIPTS_DIR', 'data/transcripts')
LOCAL_WHISPER_MODEL = os.getenv('LOCAL_WHISPER_MODEL', 'base')

CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 200


def ensure_dirs():
    """Ensure required directories exist."""
    for d in [UPLOADS_DIR, TRANSCRIPTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)


def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    try:
        from PyPDF2 import PdfReader
        
        print(f"  📄 Extracting text from PDF...")
        text = ""
        reader = PdfReader(pdf_path)
        print(f"    Pages to extract: {len(reader.pages)}")
        for page_num, page in enumerate(reader.pages):
            if page_num % 10 == 0:
                print(f"    Extracting page {page_num}...")
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.extract_text()
        
        print(f"    Extraction complete: {len(text)} characters")
        if not text.strip():
            print("  ⚠️ PDF has no extractable text (may be image-based)")
            return None
        
        return text
    except Exception as e:
        print(f"  ❌ PDF extraction error: {e}")
        import traceback
        traceback.print_exc()
        return None


def transcribe_with_whisper(audio_path):
    """Transcribe MP3 with local Whisper."""
    try:
        import whisper
        
        print(f"  🎙️ Transcribing with Whisper ({LOCAL_WHISPER_MODEL} model)...")
        model = whisper.load_model(LOCAL_WHISPER_MODEL)
        result = model.transcribe(audio_path)
        text = result["text"]
        
        if not text.strip():
            print("  ⚠️ Whisper returned empty transcription")
            return None
        
        return text
    except Exception as e:
        print(f"  ❌ Whisper transcription error: {e}")
        return None


def download_file(url, dest_dir):
    """Download file from URL."""
    try:
        print(f"  ⬇️ Downloading from {url}...")
        
        filename = urlparse(url).path.split('/')[-1]
        if not filename:
            filename = "downloaded_file"
        
        dest_path = os.path.join(dest_dir, filename)
        
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f:
            if total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            else:
                f.write(response.content)
        
        print(f"  ✓ Downloaded: {dest_path}")
        return dest_path
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    print(f"    chunk_text called with {len(text)} characters")
    if not text or len(text.strip()) < 50:
        return [text]
    
    chunks = []
    start = 0
    L = len(text)
    
    while start < L:
        end = min(start + size, L)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move forward: if we're at the end or close to it, break
        prev_start = start
        start = end - overlap
        
        # Prevent infinite loop: ensure we always make progress
        if start >= L or start <= prev_start:
            break
    
    print(f"    chunk_text returning {len(chunks)} chunks")
    return chunks


def ingest_file(file_path, source_type='upload', title=None):
    """
    Ingest a single file or URL into the knowledge base.
    
    Args:
        file_path: Local file path, URL, or text content
        source_type: 'upload', 'url', or 'text'
        title: Optional title for the document
    """
    ensure_dirs()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    content_type = None
    full_text = None
    actual_path = file_path
    
    try:
        # Handle URL input
        if source_type == 'url':
            file_path = download_file(file_path, UPLOADS_DIR)
            if not file_path:
                return False
            actual_path = file_path
            source_type = 'upload'
        
        # Determine file type and process accordingly
        if file_path.lower().endswith('.mp3'):
            content_type = 'mp3'
            print(f"\n🎵 Processing MP3: {file_path}")
            
            full_text = transcribe_with_whisper(file_path)
            if not full_text:
                print("  ❌ Failed to transcribe MP3")
                return False
            
            # Save transcript
            if title is None:
                title = Path(file_path).stem
            
            transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{title}.json")
            with open(transcript_path, 'w') as f:
                json.dump({
                    'title': title,
                    'source': file_path,
                    'transcript': full_text,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            print(f"  ✓ Transcript saved: {transcript_path}")
        
        elif file_path.lower().endswith('.pdf'):
            content_type = 'pdf'
            print(f"\n📄 Processing PDF: {file_path}")
            
            full_text = extract_pdf_text(file_path)
            if not full_text:
                print("  ❌ Failed to extract PDF text")
                return False
            
            if title is None:
                title = Path(file_path).stem
        
        else:
            print(f"  ❌ Unsupported file type: {file_path}")
            return False
        
        # Insert document
        print(f"  💾 Inserting into database...")
        c.execute('''
            INSERT INTO documents (source_type, source_path, title, content_type, full_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (source_type, actual_path, title, content_type, full_text))
        
        doc_id = c.lastrowid
        print(f"  ✓ Document inserted with ID {doc_id}")
        
        # Insert into FTS table
        print(f"  📇 Inserting into FTS...")
        c.execute('INSERT INTO documents_fts VALUES (?, ?, ?)',
                  (doc_id, title, full_text))
        print(f"  ✓ FTS indexed")
        
        # Create and insert chunks
        print(f"  📦 Chunking text...")
        chunks = chunk_text(full_text)
        print(f"  📦 Creating {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            if i % 50 == 0:
                print(f"    Inserting chunk {i}/{len(chunks)}...")
            c.execute('''
                INSERT INTO chunks (doc_id, chunk_order, chunk_text)
                VALUES (?, ?, ?)
            ''', (doc_id, i, chunk))
        
        print(f"  💾 Committing...")
        conn.commit()
        print(f"✓ Successfully ingested: {title} ({len(chunks)} chunks)")
        
        return True
    
    except Exception as e:
        print(f"❌ Ingest error: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest.py <file_path|url> [--title TITLE] [--type upload|url|text]")
        print("\nExample:")
        print("  python scripts/ingest.py data/uploads/sermon.mp3")
        print("  python scripts/ingest.py https://example.com/file.mp3 --type url")
        print("  python scripts/ingest.py data/file.pdf --title 'My Document'")
        return
    
    source = sys.argv[1]
    title = None
    source_type = 'upload'
    
    # Parse arguments
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
        elif sys.argv[i] == '--type' and i + 1 < len(sys.argv):
            source_type = sys.argv[i + 1]
    
    success = ingest_file(source, source_type=source_type, title=title)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
