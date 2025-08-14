import os
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional

from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.faiss_service import FAISSService
from app.services.database_service import DatabaseService
from app.models.document import AskRequest, AskResponse
from app.models.session import (
    SessionCreate, SessionUpdate, Session, SessionListResponse,
    MessageListResponse, ExportResponse, AskRequest as SessionAskRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OnCall Runbook API",
    description="AI-powered incident response and runbook management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ingestion_service = IngestionService()
rag_service = RAGService()
faiss_service = FAISSService()
database_service = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting OnCall Runbook API...")
        
        # Ensure FAISS index is ready (do not wipe existing index)
        faiss_service.ensure_index()
        logger.info("FAISS index initialization completed")
        
        # Check if index needs initial population
        if not faiss_service.is_index_populated():
            logger.info("Index is empty, running initial seed document ingestion...")
            result = ingestion_service.ingest_seed_documents()
            if result["success"]:
                logger.info(f"Initial ingestion completed: {result['ingested_files']} files, {result['total_chunks']} chunks")
            else:
                logger.warning(f"Initial ingestion had issues: {result.get('message', 'Unknown error')}")
        else:
            logger.info("Index already populated, skipping initial ingestion")
        
        logger.info("OnCall Runbook API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "oncall-runbook-api",
        "version": "1.0.0"
    }

# Session Management Endpoints

@app.post("/sessions", response_model=Session)
async def create_session(session: SessionCreate):
    """Create a new chat session"""
    try:
        session_id = database_service.create_session(session.title, session.description)
        created_session = database_service.get_session(session_id)
        return created_session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    search: Optional[str] = Query(None, description="Search sessions by title or description"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
):
    """List chat sessions with optional search and pagination"""
    try:
        result = database_service.list_sessions(search=search, limit=limit, offset=offset)
        return result
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """Get a specific chat session"""
    try:
        session = database_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.patch("/sessions/{session_id}", response_model=Session)
async def update_session(session_id: str, session_update: SessionUpdate):
    """Update a chat session"""
    try:
        # Check if session exists
        existing_session = database_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session
        success = database_service.update_session(
            session_id, 
            title=session_update.title, 
            description=session_update.description
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="No changes to update")
        
        # Return updated session
        updated_session = database_service.get_session(session_id)
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session and all its messages"""
    try:
        # Check if session exists
        existing_session = database_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session
        success = database_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
        return {"success": True, "message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip")
):
    """Get messages for a specific session"""
    try:
        # Check if session exists
        existing_session = database_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        result = database_service.get_messages(session_id, limit=limit, offset=offset)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@app.post("/sessions/{session_id}/export", response_model=ExportResponse)
async def export_session(session_id: str):
    """Export a session to Markdown format"""
    try:
        # Check if session exists
        existing_session = database_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Export to markdown
        markdown = database_service.export_session_markdown(session_id)
        if not markdown:
            raise HTTPException(status_code=500, detail="Failed to export session")
        
        # Generate filename
        filename = f"session-{session_id[:8]}-{existing_session['title'].replace(' ', '-').lower()}.md"
        
        return ExportResponse(markdown=markdown, filename=filename)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")

# Knowledge Base Endpoints

@app.get("/kb/status")
async def get_kb_status():
    """Get knowledge base status"""
    try:
        status = ingestion_service.get_kb_status()
        return status
    except Exception as e:
        logger.error(f"Error getting KB status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get KB status: {str(e)}")

@app.post("/kb/ingest")
async def upload_and_ingest_file(file: UploadFile = File(...)):
    """Upload and ingest a file into the knowledge base"""
    try:
        # Validate file type
        allowed_extensions = {'.md', '.txt', '.pdf', '.log'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        if file_extension == '.pdf':
            # For PDFs, we need to extract text content
            try:
                import fitz  # PyMuPDF
                import io
                pdf_stream = io.BytesIO(content)
                pdf_doc = fitz.open(stream=pdf_stream, filetype="pdf")
                text_content = ""
                for page in pdf_doc:
                    text_content += page.get_text()
                pdf_doc.close()
                content = text_content.encode('utf-8')
            except ImportError:
                # Fallback to PyPDF2
                try:
                    import PyPDF2
                    import io
                    pdf_stream = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_stream)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
                    content = text_content.encode('utf-8')
                except ImportError:
                    raise HTTPException(status_code=500, detail="PDF processing not available")
        else:
            # For text files, decode content
            content = content.decode('utf-8')
        
        # Process the uploaded file
        result = ingestion_service.ingest_uploaded_file(file.filename, content)
        
        if result["status"] == "success":
            return {
                "success": True,
                "message": result["message"],
                "filename": file.filename,
                "chunks_count": result["chunks_created"],
                "sections_detected": result["sections_detected"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")

@app.post("/kb/refresh")
async def refresh_knowledge_base():
    """Refresh the knowledge base by scanning for new/changed files"""
    try:
        result = ingestion_service.refresh_knowledge_base()
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "files_processed": result["files_processed"],
                "total_chunks": result["total_chunks"],
                "total_files": result["total_files"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh knowledge base: {str(e)}")

# Legacy Endpoints

@app.post("/ingest")
async def ingest_documents():
    """Legacy endpoint for ingesting seed documents"""
    try:
        result = ingestion_service.ingest_seed_documents()
        return result
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest documents: {str(e)}")

@app.post("/ask")
async def ask_question(request: AskRequest):
    """Legacy endpoint for asking questions"""
    try:
        result = rag_service.ask_question(request.question, request.context)
        
        # Convert to legacy format
        return AskResponse(
            answer=result["answer"],
            sources=result["citations"],
            confidence=result["confidence"]
        )
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.post("/ask/structured")
async def ask_question_structured(request: SessionAskRequest):
    """Structured endpoint for asking questions with session support"""
    try:
        # Generate answer using RAG service
        result = rag_service.ask_question(request.question, request.context)
        
        # Handle session management
        session_id = request.session_id
        
        if not session_id:
            # Create new session with question as title
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            session_id = database_service.create_session(title)
        
        # Add user message to session
        database_service.add_message(
            session_id=session_id,
            content=request.question,
            role="user"
        )
        
        # Add assistant message to session
        database_service.add_message(
            session_id=session_id,
            content=result["answer"],
            role="assistant",
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            diagnostics=result.get("diagnostics")
        )
        
        # Add session_id to response
        result["session_id"] = session_id
        
        return result
        
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get FAISS index statistics"""
    try:
        stats = faiss_service.get_index_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/session-stats")
async def get_session_stats():
    """Get session and message statistics"""
    try:
        stats = database_service.get_session_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
