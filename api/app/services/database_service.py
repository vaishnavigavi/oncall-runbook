import sqlite3
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for managing SQLite database operations"""
    
    def __init__(self):
        self.db_path = "/app/data/app.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist"""
        try:
            # Ensure data directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        message_count INTEGER DEFAULT 0
                    )
                """)
                
                # Create messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        citations TEXT,
                        confidence REAL,
                        diagnostics TEXT,
                        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions (updated_at)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _get_connection(self):
        """Get database connection with proper row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def create_session(self, title: str, description: Optional[str] = None) -> str:
        """Create a new session and return its ID"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (id, title, description, created_at, updated_at, message_count)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (session_id, title, description, now, now))
                conn.commit()
                
                logger.info(f"Created session: {session_id} with title: {title}")
                return session_id
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sessions WHERE id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            raise
    
    def list_sessions(self, search: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List sessions with optional search and pagination"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with optional search
                query = "SELECT * FROM sessions"
                params = []
                
                if search:
                    query += " WHERE title LIKE ? OR description LIKE ?"
                    params.extend([f"%{search}%", f"%{search}%"])
                
                query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                sessions = [dict(row) for row in cursor.fetchall()]
                
                # Get total count
                count_query = "SELECT COUNT(*) FROM sessions"
                if search:
                    count_query += " WHERE title LIKE ? OR description LIKE ?"
                    count_params = [f"%{search}%", f"%{search}%"]
                else:
                    count_params = []
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()[0]
                
                return {
                    "sessions": sessions,
                    "total": total
                }
                
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            raise
    
    def update_session(self, session_id: str, title: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Update session title and/or description"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                updates = []
                params = []
                
                if title is not None:
                    updates.append("title = ?")
                    params.append(title)
                
                if description is not None:
                    updates.append("description = ?")
                    params.append(description)
                
                if not updates:
                    return False  # Nothing to update
                
                updates.append("updated_at = ?")
                params.append(datetime.utcnow())
                params.append(session_id)
                
                query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                logger.info(f"Updated session: {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            raise
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete messages first (CASCADE should handle this, but being explicit)
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                
                # Delete session
                cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                conn.commit()
                
                logger.info(f"Deleted session: {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            raise
    
    def add_message(self, session_id: str, content: str, role: str, 
                   citations: Optional[List[str]] = None, confidence: Optional[float] = None,
                   diagnostics: Optional[Dict[str, Any]] = None) -> str:
        """Add a message to a session and return its ID"""
        try:
            message_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Convert citations and diagnostics to JSON strings
            citations_json = json.dumps(citations) if citations else None
            diagnostics_json = json.dumps(diagnostics) if diagnostics else None
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Add message
                cursor.execute("""
                    INSERT INTO messages (id, session_id, content, role, created_at, citations, confidence, diagnostics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (message_id, session_id, content, role, now, citations_json, confidence, diagnostics_json))
                
                # Update session message count and updated_at
                cursor.execute("""
                    UPDATE sessions 
                    SET message_count = message_count + 1, updated_at = ?
                    WHERE id = ?
                """, (now, session_id))
                
                conn.commit()
                
                logger.info(f"Added message {message_id} to session {session_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            raise
    
    def get_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get messages for a session with pagination"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get messages
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE session_id = ? 
                    ORDER BY created_at ASC 
                    LIMIT ? OFFSET ?
                """, (session_id, limit, offset))
                
                messages = []
                for row in cursor.fetchall():
                    message = dict(row)
                    
                    # Parse JSON fields
                    if message['citations']:
                        try:
                            message['citations'] = json.loads(message['citations'])
                        except json.JSONDecodeError:
                            message['citations'] = []
                    
                    if message['diagnostics']:
                        try:
                            message['diagnostics'] = json.loads(message['diagnostics'])
                        except json.JSONDecodeError:
                            message['diagnostics'] = None
                    
                    messages.append(message)
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
                total = cursor.fetchone()[0]
                
                return {
                    "messages": messages,
                    "total": total,
                    "session_id": session_id
                }
                
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            raise
    
    def get_session_with_messages(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session with all its messages"""
        try:
            session = self.get_session(session_id)
            if not session:
                return None
            
            messages_data = self.get_messages(session_id, limit=1000)  # Get all messages
            session['messages'] = messages_data['messages']
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting session with messages {session_id}: {e}")
            raise
    
    def export_session_markdown(self, session_id: str) -> Optional[str]:
        """Export a session to Markdown format"""
        try:
            session_data = self.get_session_with_messages(session_id)
            if not session_data:
                return None
            
            markdown = f"# {session_data['title']}\n\n"
            if session_data.get('description'):
                markdown += f"*{session_data['description']}*\n\n"
            
            markdown += f"**Session ID:** {session_id}\n"
            markdown += f"**Created:** {session_data['created_at']}\n"
            markdown += f"**Messages:** {session_data['message_count']}\n\n"
            markdown += "---\n\n"
            
            for message in session_data['messages']:
                role_emoji = "👤" if message['role'] == 'user' else "🤖"
                markdown += f"## {role_emoji} {message['role'].title()}\n\n"
                markdown += f"{message['content']}\n\n"
                
                # Add metadata for assistant messages
                if message['role'] == 'assistant':
                    if message.get('citations'):
                        markdown += "**Sources:**\n"
                        for citation in message['citations']:
                            markdown += f"- {citation}\n"
                        markdown += "\n"
                    
                    if message.get('confidence'):
                        markdown += f"**Confidence:** {message['confidence']:.1%}\n\n"
                    
                    if message.get('diagnostics'):
                        markdown += "**Diagnostics:**\n"
                        markdown += "```json\n"
                        markdown += json.dumps(message['diagnostics'], indent=2)
                        markdown += "\n```\n\n"
                
                markdown += "---\n\n"
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error exporting session {session_id} to markdown: {e}")
            raise
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total sessions
                cursor.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Total messages
                cursor.execute("SELECT COUNT(*) FROM messages")
                total_messages = cursor.fetchone()[0]
                
                # Sessions by date (last 7 days)
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM sessions 
                    WHERE created_at >= datetime('now', '-7 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                recent_sessions = [dict(row) for row in cursor.fetchall()]
                
                # Messages by role
                cursor.execute("""
                    SELECT role, COUNT(*) as count
                    FROM messages 
                    GROUP BY role
                """)
                messages_by_role = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "recent_sessions": recent_sessions,
                    "messages_by_role": messages_by_role
                }
                
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            raise
