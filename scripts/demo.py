#!/usr/bin/env python3
"""
Demo script to test the PR-chat system with sample data.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')


def show_stats():
    """Display database statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM documents')
        doc_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM chunks')
        chunk_count = c.fetchone()[0]
        
        conn.close()
        
        print("\n📊 Knowledge Base Statistics")
        print("=" * 40)
        print(f"Documents:  {doc_count}")
        print(f"Chunks:     {chunk_count}")
        print()
        
        if doc_count == 0:
            print("💡 No documents yet. Try:")
            print("   python scripts/ingest.py <file.mp3 or file.pdf>")
        
        return doc_count > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def show_documents():
    """Display all documents in the knowledge base."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT d.doc_id, d.title, d.content_type, COUNT(ch.chunk_id) as chunks
            FROM documents d
            LEFT JOIN chunks ch ON d.doc_id = ch.doc_id
            GROUP BY d.doc_id
            ORDER BY d.created_at DESC
        ''')
        
        docs = c.fetchall()
        conn.close()
        
        if docs:
            print("\n📚 Documents in Knowledge Base")
            print("=" * 60)
            for doc_id, title, content_type, chunk_count in docs:
                print(f"ID {doc_id}: {title}")
                print(f"  Type: {content_type} | Chunks: {chunk_count}")
            print()
        else:
            print("\n(No documents found)")
        
        return len(docs) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def show_help():
    """Show usage information."""
    print("""
📖 PR-chat Demo & Status

Quick Commands:
  python scripts/setup_db.py              Initialize database
  python scripts/ingest.py <file>         Upload MP3 or PDF
  python scripts/build_embeddings.py      Build search index
  streamlit run app/streamlit_app.py      Launch web interface
  python scripts/demo.py --help           Show this help

Examples:
  python scripts/ingest.py recording.mp3 --title "My Recording"
  python scripts/ingest.py document.pdf --title "My PDF"
  python scripts/ingest.py https://example.com/file.mp3 --type url

Environment:
  Edit .env to configure:
    - OPENAI_API_KEY (optional, for AI chat)
    - LOCAL_WHISPER_MODEL (tiny/base/small/medium/large)
    - Other paths and settings

Status:
  Use this script to check knowledge base status:
    python scripts/demo.py --stats        Show statistics
    python scripts/demo.py --list         List documents
    python scripts/demo.py --help         Show this help
    """)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--help':
            show_help()
        elif arg == '--stats':
            show_stats()
        elif arg == '--list':
            show_documents()
    else:
        # Default: show stats and documents
        print("\n🚀 PR-chat Status\n")
        has_docs = show_stats()
        if has_docs:
            show_documents()


if __name__ == '__main__':
    main()
