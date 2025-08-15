import sqlite3
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Try to import PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/app.db")
DATABASE_URL = os.getenv("DATABASE_URL", None)

class DatabaseService:
    """Service for managing database operations with SQLite and PostgreSQL support"""
    
    def __init__(self):
        self.db_type = self._determine_db_type()
        self.connection = None
        self._ensure_tables()
    
    def _determine_db_type(self) -> str:
        """Determine which database type to use"""
        if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
            if POSTGRES_AVAILABLE:
                return 'postgresql'
            else:
                logger.warning("PostgreSQL URL provided but psycopg2 not available, falling back to SQLite")
                return 'sqlite'
        return 'sqlite'
    
    def _get_connection(self):
        """Get database connection based on type"""
        if self.db_type == 'postgresql':
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            return sqlite3.connect(DATABASE_PATH)
    
    def _ensure_tables(self):
        """Ensure all required tables exist"""
        try:
            if self.db_type == "sqlite":
                self._create_sqlite_tables()
            elif self.db_type == "postgresql":
                self._create_postgresql_tables()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            logger.info(f"Database tables ensured using {self.db_type}")
            return True
        except Exception as e:
            logger.error(f"Error ensuring tables: {e}")
            # Don't raise the error, just log it and return False
            return False
    
    def _create_sqlite_tables(self):
        """Create SQLite tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            conn.commit()
    
    def _create_postgresql_tables(self):
        """Create PostgreSQL tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(255) PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id VARCHAR(255) PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            conn.commit()
    
    def create_session(self, title: str) -> str:
        """Create a new session and return its ID"""
        session_id = str(uuid.uuid4())
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        INSERT INTO sessions (id, title, created_at, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (session_id, title))
                else:
                    cursor.execute("""
                        INSERT INTO sessions (id, title, created_at, updated_at)
                        VALUES (?, ?, datetime('now'), datetime('now'))
                    """, (session_id, title))
                
                conn.commit()
                logger.info(f"Created session: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def update_session(self, session_id: str, title: str) -> bool:
        """Update session title"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        UPDATE sessions SET title = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (title, session_id))
                else:
                    cursor.execute("""
                        UPDATE sessions SET title = ?, updated_at = datetime('now')
                        WHERE id = ?
                    """, (title, session_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete messages first (foreign key constraint)
                if self.db_type == 'postgresql':
                    cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
                    cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
                else:
                    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT s.*, COUNT(m.id) as message_count
                        FROM sessions s
                        LEFT JOIN messages m ON s.id = m.session_id
                        GROUP BY s.id, s.title, s.created_at, s.updated_at
                        ORDER BY s.updated_at DESC
                    """)
                else:
                    cursor.execute("""
                        SELECT s.*, COUNT(m.id) as message_count
                        FROM sessions s
                        LEFT JOIN messages m ON s.id = m.session_id
                        GROUP BY s.id, s.title, s.created_at, s.updated_at
                        ORDER BY s.updated_at DESC
                    """)
                
                rows = cursor.fetchall()
                sessions = []
                
                for row in rows:
                    if self.db_type == 'postgresql':
                        session = dict(row)
                    else:
                        session = {
                            'id': row[0],
                            'title': row[1],
                            'created_at': row[2],
                            'updated_at': row[3],
                            'message_count': row[4]
                        }
                    sessions.append(session)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def add_message(self, session_id: str, role: str, content: str) -> str:
        """Add a message to a session"""
        message_id = str(uuid.uuid4())
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        INSERT INTO messages (id, session_id, role, content, timestamp)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (message_id, session_id, role, content))
                else:
                    cursor.execute("""
                        INSERT INTO messages (id, session_id, role, content, timestamp)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (message_id, session_id, role, content))
                
                conn.commit()
                logger.info(f"Added message {message_id} to session {session_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT * FROM messages 
                        WHERE session_id = %s 
                        ORDER BY timestamp ASC
                    """, (session_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM messages 
                        WHERE session_id = ? 
                        ORDER BY timestamp ASC
                    """, (session_id,))
                
                rows = cursor.fetchall()
                messages = []
                
                for row in rows:
                    if self.db_type == 'postgresql':
                        message = dict(row)
                    else:
                        message = {
                            'id': row[0],
                            'session_id': row[1],
                            'role': row[2],
                            'content': row[3],
                            'timestamp': row[4]
                        }
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
                else:
                    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                
                row = cursor.fetchone()
                if row:
                    if self.db_type == 'postgresql':
                        return dict(row)
                    else:
                        return {
                            'id': row[0],
                            'title': row[1],
                            'created_at': row[2],
                            'updated_at': row[3]
                        }
                return None
                
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
