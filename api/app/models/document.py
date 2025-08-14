from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class DocumentChunk(BaseModel):
    """Represents a chunk of a document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="The text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata about the chunk")
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    start_char: int = Field(..., description="Starting character position in original document")
    end_char: int = Field(..., description="Ending character position in original document")
    heading: Optional[str] = Field(None, description="Associated heading for this chunk")
    
class Document(BaseModel):
    """Represents a document to be ingested"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to the document file")
    file_type: str = Field(..., description="Type of document (md, txt, pdf)")
    content: str = Field(..., description="Full text content of the document")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Document chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    file_path: Optional[str] = Field(None, description="Path to specific file to ingest")
    ingest_seed_docs: bool = Field(False, description="Whether to ingest seed documents")
    
class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Description of the result")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    index_updated: bool = Field(..., description="Whether the FAISS index was updated")
    
class AskRequest(BaseModel):
    """Request model for asking questions"""
    question: str = Field(..., description="The question to ask")
    context: str = Field("", description="Additional context for the question")
    
class AskResponse(BaseModel):
    """Response model for question answering"""
    answer: str = Field(..., description="The answer to the question")
    sources: List[str] = Field(..., description="List of source documents")
    confidence: float = Field(..., description="Confidence score of the answer")
    
class SearchResult(BaseModel):
    """Result from searching the document index"""
    content: str = Field(..., description="The chunk content")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the chunk")
    score: float = Field(..., description="Similarity score")
    source_document: str = Field(..., description="Source document filename")
