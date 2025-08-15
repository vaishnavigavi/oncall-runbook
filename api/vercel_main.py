from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
import json
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory storage for Vercel deployment
class SimpleStorage:
    def __init__(self):
        self.sessions = {}
        self.messages = {}
        self.documents = {}
        self.kb_status = {
            "docs_count": 0,
            "docs": [],
            "index_ready": True,
            "message": "Simple storage mode - documents stored in memory"
        }
    
    async def create_session(self, name: str):
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.sessions[session_id] = session
        return session
    
    async def get_sessions(self):
        return list(self.sessions.values())
    
    async def get_session(self, session_id: str):
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, name: str):
        if session_id in self.sessions:
            self.sessions[session_id]["name"] = name
            self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
            return self.sessions[session_id]
        return None
    
    async def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            # Also delete associated messages
            if session_id in self.messages:
                del self.messages[session_id]
            return True
        return False
    
    async def get_messages(self, session_id: str):
        return self.messages.get(session_id, [])
    
    async def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.messages:
            self.messages[session_id] = []
        
        message = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        self.messages[session_id].append(message)
        return message
    
    async def export_session(self, session_id: str):
        messages = self.messages.get(session_id, [])
        markdown = "# Chat Export\n\n"
        for msg in messages:
            markdown += f"## {msg['role'].title()}\n\n{msg['content']}\n\n"
        return {"markdown": markdown}
    
    async def store_document(self, filename: str, content: str):
        doc_id = str(uuid.uuid4())
        self.documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "content": content,
            "uploaded_at": datetime.now().isoformat()
        }
        self.kb_status["docs_count"] = len(self.documents)
        self.kb_status["docs"] = [{"filename": doc["filename"], "uploaded_at": doc["uploaded_at"]} for doc in self.documents.values()]
        return {
            "status": "success",
            "message": f"Document {filename} stored successfully",
            "chunks_created": 1,
            "sections_detected": 1
        }
    
    async def get_kb_status(self):
        return self.kb_status
    
    async def search_documents(self, query: str):
        # Simple keyword search for demo
        results = []
        query_lower = query.lower()
        
        for doc in self.documents.values():
            if query_lower in doc["content"].lower():
                results.append({
                    "chunk_id": doc["id"],
                    "content": doc["content"][:200] + "...",
                    "filename": doc["filename"],
                    "score": 0.8
                })
        
        return results

# Global storage
storage = SimpleStorage()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting OnCall Runbook API")
    yield
    # Shutdown
    logger.info("Shutting down OnCall Runbook API")

# Create FastAPI app
app = FastAPI(
    title="OnCall Runbook API",
    description="AI-powered OnCall Runbook system (Vercel Deployment)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OnCall Runbook API is running on Vercel"}

# Self-check endpoint
@app.get("/selfcheck")
async def self_check():
    return {
        "status": "operational",
        "checks": {
            "api": "✅ Running on Vercel",
            "database": "✅ Simple in-memory storage",
            "faiss": "❌ Not available (using simple search)",
            "ingestion": "✅ Simple document storage",
            "rag": "❌ Not available (using mock responses)"
        },
        "message": "API is running with simplified services for Vercel deployment"
    }

# Knowledge base endpoints
@app.get("/kb/status")
async def get_kb_status():
    return await storage.get_kb_status()

@app.post("/kb/ingest")
async def ingest_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename
        
        if filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF processing not yet implemented in Vercel")
        
        # Process text files
        text_content = content.decode('utf-8')
        result = await storage.store_document(filename, text_content)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

@app.post("/kb/refresh")
async def refresh_knowledge_base():
    return {
        "status": "success",
        "message": "Knowledge base refreshed",
        "docs_count": storage.kb_status["docs_count"]
    }

# Session management endpoints
@app.post("/sessions")
async def create_session(name: str = Form(...)):
    try:
        return await storage.create_session(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/sessions")
async def get_sessions():
    try:
        sessions = await storage.get_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        session = await storage.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.patch("/sessions/{session_id}")
async def update_session(session_id: str, name: str = Form(...)):
    try:
        updated_session = await storage.update_session(session_id, name)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found")
        return updated_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        success = await storage.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    try:
        messages = await storage.get_messages(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@app.post("/sessions/{session_id}/export")
async def export_session(session_id: str):
    try:
        export_data = await storage.export_session(session_id)
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")

# Main RAG endpoint
@app.post("/ask/structured")
async def ask_question_structured(
    question: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    try:
        # Create session if not provided
        if not session_id:
            session = await storage.create_session(f"Chat: {question[:50]}...")
            session_id = session["id"]
        
        # Search documents for relevant content
        search_results = await storage.search_documents(question)
        
        # Generate a simple response based on search results
        if search_results:
            # Found relevant documents
            answer = f"Based on your uploaded documentation, here's what I found:\n\n"
            for i, result in enumerate(search_results[:3], 1):
                answer += f"{i}. **{result['filename']}**: {result['content']}\n\n"
            answer += "This is a simplified response from the Vercel deployment. For full RAG capabilities, consider deploying to a platform that supports FAISS and full ML libraries."
            
            citations = [{"filename": result["filename"], "chunk_id": result["chunk_id"]} for result in search_results[:3]]
        else:
            # No relevant documents found
            answer = f"I couldn't find specific information about '{question}' in your uploaded documents.\n\n**To get better answers:**\n1. Upload relevant documentation\n2. Make sure your question relates to the uploaded content\n3. Try rephrasing your question\n\nThis is a simplified deployment on Vercel. For full AI-powered responses, deploy to a platform that supports OpenAI and advanced ML libraries."
            citations = []
        
        # Store messages
        await storage.add_message(session_id, "user", question)
        await storage.add_message(session_id, "assistant", answer)
        
        return {
            "answer": answer,
            "citations": citations,
            "confidence": 0.7 if search_results else 0.3,
            "session_id": session_id,
            "diagnostics": {
                "search_results_count": len(search_results),
                "deployment_type": "vercel_simple"
            },
            "retrieval_stats": {"method": "simple_keyword_search"},
            "planning_stats": {"method": "basic_response_generation"}
        }
            
    except Exception as e:
        logger.error(f"Error in ask_question_structured: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

# Session stats endpoint
@app.get("/session-stats")
async def get_session_stats():
    try:
        sessions = await storage.get_sessions()
        total_messages = sum(len(await storage.get_messages(s["id"])) for s in sessions)
        
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "OnCall Runbook API (Vercel Deployment)",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "note": "This is a simplified deployment. For full features, deploy to a platform supporting FAISS and ML libraries."
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
