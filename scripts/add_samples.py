#!/usr/bin/env python3
"""
Generate sample test data for PR-chat (creates mock documents for testing).
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'pr_chat.db')


def add_sample_documents():
    """Add sample documents to test the system."""
    
    samples = [
        {
            "title": "Introduction to Prayer",
            "content_type": "text",
            "text": """
Prayer is a fundamental spiritual practice found in many religions and philosophies.
It serves as a means of communication with the divine, whether through spoken words,
silent thoughts, or meditative practices.

Types of prayer include:
- Petitionary prayer (asking for help)
- Intercessory prayer (praying for others)
- Thanksgiving prayer (expressing gratitude)
- Contemplative prayer (meditative connection)

Research shows that prayer can reduce stress, improve emotional wellbeing,
and foster a sense of community among practitioners.
"""
        },
        {
            "title": "Meditation and Mindfulness",
            "content_type": "text",
            "text": """
Meditation is an ancient practice that involves focusing the mind and reducing
the stream of thoughts. Mindfulness, a form of meditation, emphasizes present-moment
awareness without judgment.

Benefits of meditation include:
- Reduced anxiety and depression
- Improved focus and concentration
- Better sleep quality
- Lower blood pressure
- Enhanced emotional regulation

Different meditation techniques include:
- Breath awareness
- Body scan meditation
- Loving-kindness meditation
- Walking meditation
- Transcendental meditation

Most practitioners recommend starting with 5-10 minutes daily and gradually
increasing the duration as you become more comfortable with the practice.
"""
        },
        {
            "title": "Scripture Study Methods",
            "content_type": "text",
            "text": """
Effective scripture study requires intentional approaches and consistent practice.
Several proven methods can help readers gain deeper understanding of sacred texts.

Popular scripture study methods:

1. INDUCTIVE METHOD
- Observe: What does the text say?
- Interpret: What does it mean?
- Apply: How does it apply to my life?

2. EXPOSITORY METHOD
Focuses on thorough explanation of specific passages and their context.

3. TOPICAL METHOD
Studies specific themes or subjects across multiple passages.

4. HISTORICAL METHOD
Examines the historical context and cultural background of the text.

When studying scriptures, consider:
- Who is the author?
- Who is the intended audience?
- What is the historical context?
- What are the key themes?
- How does this apply today?

Regular scripture study deepens spiritual understanding and strengthens faith.
"""
        }
    ]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        print("📝 Adding sample documents to knowledge base...\n")
        
        for doc in samples:
            # Insert document
            c.execute('''
                INSERT INTO documents (source_type, source_path, title, content_type, full_text)
                VALUES (?, ?, ?, ?, ?)
            ''', ('text', 'sample', doc['title'], doc['content_type'], doc['text']))
            
            doc_id = c.lastrowid
            
            # Insert into FTS
            c.execute('INSERT INTO documents_fts VALUES (?, ?, ?)',
                      (doc_id, doc['title'], doc['text']))
            
            # Create chunks (simple split by paragraphs)
            chunks = [p.strip() for p in doc['text'].split('\n\n') if p.strip()]
            
            for i, chunk in enumerate(chunks):
                c.execute('''
                    INSERT INTO chunks (doc_id, chunk_order, chunk_text)
                    VALUES (?, ?, ?)
                ''', (doc_id, i, chunk))
            
            print(f"✓ Added: {doc['title']} ({len(chunks)} chunks)")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Sample documents added successfully!")
        print("\nNext steps:")
        print("1. Build embeddings: python scripts/build_embeddings.py")
        print("2. Run the app: streamlit run app/streamlit_app.py")
        print("3. Try searching for 'prayer', 'meditation', or 'scripture'")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    add_sample_documents()
