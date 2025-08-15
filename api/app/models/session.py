from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class SessionBase(BaseModel):
    title: str = Field(..., description="Session title")
    description: Optional[str] = Field(None, description="Session description")

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated session title")
    description: Optional[str] = Field(None, description="Updated session description")

class Session(SessionBase):
    id: str = Field(..., description="Unique session ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(0, description="Number of messages in session")

class MessageBase(BaseModel):
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    session_id: str = Field(..., description="Session ID this message belongs to")

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str = Field(..., description="Unique message ID")
    created_at: datetime = Field(..., description="Message creation timestamp")
    citations: Optional[List[str]] = Field(None, description="Source citations for assistant messages")
    confidence: Optional[float] = Field(None, description="Confidence score for assistant messages")
    diagnostics: Optional[dict] = Field(None, description="Diagnostics results if tools ran")

class SessionWithMessages(Session):
    messages: List[Message] = Field(..., description="Messages in this session")

class AskRequest(BaseModel):
    question: str = Field(..., description="User question")
    context: str = Field("", description="Additional context")
    session_id: Optional[str] = Field(None, description="Existing session ID (creates new if missing)")

class AskResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    citations: List[str] = Field(..., description="Source citations")
    trace_id: str = Field(..., description="Trace ID for debugging")
    retrieved_chunks: int = Field(..., description="Number of chunks retrieved")
    confidence: float = Field(..., description="Confidence score")
    diagnostics: Optional[dict] = Field(None, description="Diagnostics results if tools ran")
    session_id: str = Field(..., description="Session ID (new or existing)")

class SessionListResponse(BaseModel):
    sessions: List[Session] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")

class MessageListResponse(BaseModel):
    messages: List[Message] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")
    session_id: str = Field(..., description="Session ID")

class ExportResponse(BaseModel):
    markdown: str = Field(..., description="Markdown export of session")
    filename: str = Field(..., description="Suggested filename for export")
