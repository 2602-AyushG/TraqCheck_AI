import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "candidates.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            company TEXT,
            designation TEXT,
            skills TEXT,
            resume_path TEXT,
            extraction_confidence TEXT,
            status TEXT DEFAULT 'uploaded',
            document_request_text TEXT,
            documents TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")