import pytest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the services we need to test
import sys
sys.path.append('api')

from app.services.faiss_service import FAISSService
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.anti_generic_gate import AntiGenericGate
from app.services.database_service import DatabaseService
from app.services.planner import Planner
from app.services.retrieval import RetrievalPipeline

class TestRAGSystem:
    """Comprehensive tests for the RAG system"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, test_data_dir, test_docs_dir, test_index_dir, test_db_path):
        """Setup test environment for each test"""
        self.test_data_dir = test_data_dir
        self.test_docs_dir = test_docs_dir
        self.test_index_dir = test_index_dir
        self.test_db_path = test_db_path
        
        # Mock the data paths
        with patch('app.services.faiss_service.FAISS_INDEX_PATH', os.path.join(test_index_dir, 'faiss_index.bin')):
            with patch('app.services.faiss_service.FAISS_METADATA_PATH', os.path.join(test_index_dir, 'metadata.pkl')):
                with patch('app.services.ingestion_service.DOCS_PATH', test_docs_dir):
                    with patch('app.services.database_service.DATABASE_PATH', test_db_path):
                        yield
    
    def test_kb_persist(self):
        """Test KB persistence: ingest → status ready → ensure_index → still ready"""
        # Create test document
        test_doc = "Test Document\n# First Checks\n• Check CPU usage\n• Monitor memory\n\n# Fix\n• Restart service\n• Scale resources"
        test_doc_path = os.path.join(self.test_docs_dir, "test_doc.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Initialize services
        faiss_service = FAISSService()
        ingestion_service = IngestionService()
        
        # Test 1: Initial status should show no docs
        initial_status = ingestion_service.get_kb_status()
        assert initial_status['docs_count'] == 0
        assert not initial_status['index_ready']
        
        # Test 2: Ingest document
        result = ingestion_service.ingest_single_document(test_doc_path, test_doc)
        assert result['status'] == 'success'
        assert result['chunks_created'] > 0
        
        # Test 3: Status should now show docs and index ready
        status_after_ingest = ingestion_service.get_kb_status()
        assert status_after_ingest['docs_count'] > 0
        assert status_after_ingest['index_ready']
        
        # Test 4: Call ensure_index (should not wipe existing)
        faiss_service.ensure_index()
        
        # Test 5: Status should still be ready
        status_after_ensure = ingestion_service.get_kb_status()
        assert status_after_ensure['docs_count'] > 0
        assert status_after_ensure['index_ready']
    
    def test_no_generic_when_sufficient(self):
        """Test that anti-generic gate passes when sufficient content exists"""
        # Create test documents with diverse content
        doc1 = """# Incident Response Guide
## First Checks
• Check system logs
• Verify service status
• Monitor resource usage

## Fix Steps
• Restart affected services
• Scale up resources
• Clear caches"""
        
        doc2 = """# Troubleshooting Manual
## Quick Checks
• Review error messages
• Check configuration
• Verify connectivity

## Resolution
• Update configurations
• Restart processes
• Monitor recovery"""
        
        # Write test documents
        doc1_path = os.path.join(self.test_docs_dir, "incident_guide.md")
        doc2_path = os.path.join(self.test_docs_dir, "troubleshooting.md")
        
        with open(doc1_path, 'w') as f:
            f.write(doc1)
        with open(doc2_path, 'w') as f:
            f.write(doc2)
        
        # Ingest documents
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(doc1_path, doc1)
        ingestion_service.ingest_single_document(doc2_path, doc2)
        
        # Test RAG query
        rag_service = RAGService()
        question = "What are the first steps for system issues?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            # Mock FAISS service to return diverse results
            mock_faiss.return_value.search.return_value = [
                (Mock(content=doc1, source_file="incident_guide.md", chunk_id="1"), 0.9),
                (Mock(content=doc2, source_file="troubleshooting.md", chunk_id="1"), 0.8)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should pass anti-generic gate
            assert response['quality_gate']['passed'] == True
            assert response['planning_stats']['total_bullets'] >= 3
            assert response['planning_stats']['sources_count'] >= 2
    
    def test_missing_context_message(self):
        """Test that missing context message is generated when quality gate fails"""
        # Create minimal test document
        test_doc = "# Basic Guide\n• Simple check"
        test_doc_path = os.path.join(self.test_docs_dir, "basic.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Ingest minimal document
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(test_doc_path, test_doc)
        
        # Test RAG query that should fail quality gate
        rag_service = RAGService()
        question = "How do I fix complex database issues?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            # Mock FAISS service to return minimal results
            mock_faiss.return_value.search.return_value = [
                (Mock(content=test_doc, source_file="basic.md", chunk_id="1"), 0.7)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should fail quality gate and show missing context message
            assert response['quality_gate']['passed'] == False
            assert "Missing Context Detected" in response['answer']
            assert "Missing Sections" in response['answer']
    
    def test_sessions_persist(self):
        """Test that sessions persist: ask without session_id creates one; messages stored"""
        # Initialize database service
        db_service = DatabaseService()
        
        # Test 1: Ask question without session_id
        rag_service = RAGService()
        question = "What is the first step for CPU issues?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            mock_faiss.return_value.search.return_value = [
                (Mock(content="Check CPU usage", source_file="test.md", chunk_id="1"), 0.8)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should create new session
            assert 'session_id' in response
            session_id = response['session_id']
            assert session_id is not None
        
        # Test 2: Verify session exists in database
        sessions = db_service.list_sessions()
        assert len(sessions) > 0
        
        # Test 3: Verify messages are stored
        messages = db_service.get_session_messages(session_id)
        assert len(messages) > 0
        
        # Test 4: Ask follow-up question with same session_id
        follow_up = "What about memory issues?"
        response2 = rag_service.ask_question(follow_up, session_id=session_id)
        
        # Should use same session
        assert response2['session_id'] == session_id
        
        # Test 5: Verify more messages added
        messages_after = db_service.get_session_messages(session_id)
        assert len(messages_after) > len(messages)
    
    def test_citations_clean(self):
        """Test that citations are normalized, de-duped, and exclude readme/license files"""
        # Create test documents including some meta files
        docs = {
            "runbook.md": "# Runbook\n## First Checks\n• Check status\n• Verify logs",
            "troubleshooting.md": "# Troubleshooting\n## Fix\n• Restart service\n• Clear cache",
            "README.md": "# Project README\nThis is a readme file",
            "LICENSE": "MIT License\nCopyright 2024",
            "CHANGELOG.md": "# Changelog\nVersion 1.0.0"
        }
        
        # Write test documents
        for filename, content in docs.items():
            doc_path = os.path.join(self.test_docs_dir, filename)
            with open(doc_path, 'w') as f:
                f.write(content)
        
        # Ingest documents
        ingestion_service = IngestionService()
        for filename, content in docs.items():
            doc_path = os.path.join(self.test_docs_dir, filename)
            ingestion_service.ingest_single_document(doc_path, content)
        
        # Test RAG query
        rag_service = RAGService()
        question = "What are the first steps for system issues?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            # Mock diverse results
            mock_faiss.return_value.search.return_value = [
                (Mock(content=docs["runbook.md"], source_file="runbook.md", chunk_id="1"), 0.9),
                (Mock(content=docs["troubleshooting.md"], source_file="troubleshooting.md", chunk_id="1"), 0.8),
                (Mock(content=docs["README.md"], source_file="README.md", chunk_id="1"), 0.7),
                (Mock(content=docs["LICENSE"], source_file="LICENSE", chunk_id="1"), 0.6)
            ]
            
            response = rag_service.ask_question(question)
            
            # Citations should be cleaned
            citations = response.get('citations', [])
            
            # Should exclude meta files
            assert not any('README' in citation for citation in citations)
            assert not any('LICENSE' in citation for citation in citations)
            assert not any('CHANGELOG' in citation for citation in citations)
            
            # Should include runbook and troubleshooting
            assert any('runbook' in citation for citation in citations)
            assert any('troubleshooting' in citation for citation in citations)
            
            # Should be de-duplicated
            assert len(citations) == len(set(citations))
    
    def test_cpu_spike_no_fix_section(self):
        """Test CPU spike scenario with no fix section"""
        # Create test document with only checks, no fix
        test_doc = """# CPU Performance Guide
## First Checks
• Monitor CPU usage with `top`
• Check for runaway processes
• Review recent deployments
• Verify resource limits

## Why This Happens
CPU spikes can occur due to increased load, inefficient code, or resource contention."""
        
        test_doc_path = os.path.join(self.test_docs_dir, "cpu_guide.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Ingest document
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(test_doc_path, test_doc)
        
        # Test RAG query
        rag_service = RAGService()
        question = "CPU usage is at 95%, what should I check first?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            mock_faiss.return_value.search.return_value = [
                (Mock(content=test_doc, source_file="cpu_guide.md", chunk_id="1"), 0.9)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should have first checks but no fix section
            answer = response['answer']
            assert "First checks" in answer
            assert "Fix" not in answer
            assert "top" in answer
            assert "runaway processes" in answer
    
    def test_db_pool_has_fix_validate(self):
        """Test DB pool scenario with fix and validate sections"""
        # Create test document with fix and validate sections
        test_doc = """# Database Pool Management
## First Checks
• Check current pool size
• Monitor connection wait time
• Review pool configuration

## Fix
• Increase POOL_SIZE to 50
• Set MAX_OVERFLOW to 20
• Adjust connection timeout

## Validate
• Verify pool utilization < 80%
• Check connection wait time < 100ms
• Monitor SLO compliance"""
        
        test_doc_path = os.path.join(self.test_docs_dir, "db_pool.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Ingest document
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(test_doc_path, test_doc)
        
        # Test RAG query
        rag_service = RAGService()
        question = "Database pool is exhausted, how do I fix it and validate?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            mock_faiss.return_value.search.return_value = [
                (Mock(content=test_doc, source_file="db_pool.md", chunk_id="1"), 0.9)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should have all sections
            answer = response['answer']
            assert "First checks" in answer
            assert "Fix" in answer
            assert "Validate" in answer
            
            # Should have specific values
            assert "POOL_SIZE=50" in answer or "50" in answer
            assert "MAX_OVERFLOW=20" in answer or "20" in answer
            assert "SLO" in answer
    
    def test_cache_hotkey_specific(self):
        """Test cache hotkey scenario with specific details"""
        # Create test document with cache-specific information
        test_doc = """# Cache Management
## First Checks
• Check cache hit rate
• Monitor memory usage
• Review eviction policies

## Fix
• Set allkeys-lru eviction policy
• Configure TTL to 900 seconds
• Implement pre-warm strategies
• Adjust memory limits

## Validate
• Verify hit rate > 95%
• Check memory usage < 80%
• Monitor TTL compliance"""
        
        test_doc_path = os.path.join(self.test_docs_dir, "cache_guide.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Ingest document
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(test_doc_path, test_doc)
        
        # Test RAG query
        rag_service = RAGService()
        question = "Cache performance is poor, what specific settings should I use?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            mock_faiss.return_value.search.return_value = [
                (Mock(content=test_doc, source_file="cache_guide.md", chunk_id="1"), 0.9)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should have specific cache details
            answer = response['answer']
            assert "allkeys-lru" in answer
            assert "900" in answer or "TTL" in answer
            assert "pre-warm" in answer
    
    def test_queue_backlog_specific(self):
        """Test queue backlog scenario with specific scaling details"""
        # Create test document with queue-specific scaling information
        test_doc = """# Queue Management
## First Checks
• Monitor queue depth
• Check consumer health
• Review processing rates

## Fix
• Scale workers +2 instances
• Cap concurrency at 50%
• Configure DLQ for failed jobs
• Set max depth < 100 items
• Implement backpressure

## Validate
• Queue depth < 100
• Processing rate > 100 jobs/min
• Error rate < 1%"""
        
        test_doc_path = os.path.join(self.test_docs_dir, "queue_guide.md")
        with open(test_doc_path, 'w') as f:
            f.write(test_doc)
        
        # Ingest document
        ingestion_service = IngestionService()
        ingestion_service.ingest_single_document(test_doc_path, test_doc)
        
        # Test RAG query
        rag_service = RAGService()
        question = "Queue has 200 items backlog, how do I scale and manage it?"
        
        with patch('app.services.rag_service.FAISSService') as mock_faiss:
            mock_faiss.return_value.search.return_value = [
                (Mock(content=test_doc, source_file="queue_guide.md", chunk_id="1"), 0.9)
            ]
            
            response = rag_service.ask_question(question)
            
            # Should have specific scaling details
            answer = response['answer']
            assert "+2" in answer or "scale" in answer
            assert "50%" in answer or "concurrency" in answer
            assert "DLQ" in answer
            assert "100" in answer or "depth" in answer

