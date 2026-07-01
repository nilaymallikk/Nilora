import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Ensure the data directory exists
Path("data").mkdir(exist_ok=True)

DB_PATH = "data/memories.db"

class ConversationItem:
    def __init__(self, thread_id: str, title: str, created_at: datetime, updated_at: datetime):
        self.thread_id = thread_id
        self.title = title
        self.created_at = created_at
        self.updated_at = updated_at

class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

def init_db():
    """Initializes the database and creates the memories, conversations, and chat_messages tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                memory TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

# Initialize database on module import
init_db()

def save_memory(thread_id: str, memory: str) -> str:
    """
    Saves a memory string associated with a thread_id to the database.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (thread_id, memory) VALUES (?, ?)",
            (thread_id, memory)
        )
        conn.commit()
        return f"Successfully saved memory: '{memory}'"
    except Exception as e:
        return f"Error saving memory: {str(e)}"
    finally:
        conn.close()

def search_memory(thread_id: str, query: str) -> str:
    """
    Retrieves and searches memories associated with a thread_id.
    Matches keywords from the query, or falls back to returning the most recent memories.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        # Retrieve all memories for the thread, ordered by newest first
        cursor.execute(
            "SELECT memory FROM memories WHERE thread_id = ? ORDER BY created_at DESC",
            (thread_id,)
        )
        rows = cursor.fetchall()
        
        if not rows:
            return "No saved memories found for this conversation."
        
        memories = [row[0] for row in rows]
        
        # If there's a specific query, try to filter by keyword relevance
        if query and query.strip():
            # Filter out short/common search terms
            query_words = [w.lower() for w in query.split() if len(w) > 2]
            if query_words:
                filtered = [
                    m for m in memories
                    if any(word in m.lower() for word in query_words)
                ]
                if filtered:
                    return "Recalled memories:\n" + "\n".join(f"- {m}" for m in filtered)
        
        # Fallback: if no keyword matches or query is empty, return the most recent memories (up to 10)
        recent_memories = memories[:10]
        return "Recalled memories (most recent):\n" + "\n".join(f"- {m}" for m in recent_memories)
    except Exception as e:
        return f"Error recalling memory: {str(e)}"
    finally:
        conn.close()

def save_chat_message(thread_id: str, role: str, content: str):
    """Saves a user or assistant chat message to the database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (thread_id, role, content) VALUES (?, ?, ?)",
            (thread_id, role, content)
        )
        conn.commit()
    finally:
        conn.close()

def get_chat_history(thread_id: str):
    """Retrieves all chat messages for a given thread_id."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM chat_messages WHERE thread_id = ? ORDER BY id ASC",
            (thread_id,)
        )
        rows = cursor.fetchall()
        return [ChatMessage(row[0], row[1]) for row in rows]
    finally:
        conn.close()

def create_or_update_conversation(thread_id: str, title: str):
    """Creates a new conversation metadata entry or updates updated_at timestamp."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("SELECT 1 FROM conversations WHERE thread_id = ?", (thread_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                "UPDATE conversations SET updated_at = ? WHERE thread_id = ?",
                (now, thread_id)
            )
        else:
            display_title = title[:50] + "..." if len(title) > 50 else title
            cursor.execute(
                "INSERT INTO conversations (thread_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (thread_id, display_title, now, now)
            )
        conn.commit()
    finally:
        conn.close()

def list_conversations():
    """Lists all conversations ordered by the most recently updated."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT thread_id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        items = []
        for row in rows:
            try:
                created_at = datetime.fromisoformat(row[2])
            except Exception:
                created_at = datetime.now()
            try:
                updated_at = datetime.fromisoformat(row[3])
            except Exception:
                updated_at = datetime.now()
            items.append(ConversationItem(row[0], row[1], created_at, updated_at))
        return items
    finally:
        conn.close()
