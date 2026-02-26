#!/usr/bin/env python3
"""
Initialize the PR-chat database schema.
Creates tables for storing documents, chunks, and metadata.
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')


def setup_database():
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Documents table - stores metadata for each uploaded/ingested document
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT,  -- 'upload', 'url', 'manual'
            source_path TEXT,  -- file path, URL, or description
            title TEXT,
            content_type TEXT,  -- 'mp3', 'pdf', 'text'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            full_text TEXT  -- Full extracted text
        )
    ''')

    # Full-Text Search virtual table for keyword search
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            doc_id,
            title,
            full_text
        )
    ''')

    # Chunks table - text segments for semantic search
    c.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            chunk_order INTEGER,
            chunk_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        )
    ''')

    # Chat history - store conversation threads
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,  -- 'user' or 'assistant'
            content TEXT,
            sources TEXT,  -- JSON list of relevant doc_ids
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")


if __name__ == '__main__':
    setup_database()
