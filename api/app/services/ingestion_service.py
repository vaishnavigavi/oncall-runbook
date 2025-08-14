import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from .document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .faiss_service import FAISSService
from .file_manager import FileManager

logger = logging.getLogger(__name__)

class IngestionService:
    """Service for ingesting documents with section detection and metadata preservation"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.faiss_service = FAISSService()
        self.file_manager = FileManager()
        
    def ingest_seed_documents(self) -> Dict[str, Any]:
        """Ingest seed documents with section detection"""
        try:
            if self.faiss_service.is_index_populated():
                logger.info("Index already populated, skipping seed document ingestion")
                return {
                    "status": "skipped",
                    "message": "Index already populated",
                    "documents_processed": 0,
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            seed_docs_path = "/app/data/seed"
            if not os.path.exists(seed_docs_path):
                logger.warning(f"Seed documents path not found: {seed_docs_path}")
                return {
                    "status": "error",
                    "message": f"Seed documents path not found: {seed_docs_path}",
                    "documents_processed": 0,
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            documents_processed = 0
            total_chunks = 0
            total_sections = 0
            processing_results = []
            
            # Process each seed document
            for file_path in Path(seed_docs_path).glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt', '.pdf']:
                    try:
                        logger.info(f"Processing seed document: {file_path}")
                        
                        # Read file content
                        content = self._read_file_content(file_path)
                        if not content:
                            continue
                        
                        # Process document with section detection
                        processing_result = self.document_processor.process_document(str(file_path), content)
                        
                        if 'error' not in processing_result:
                            # Generate embeddings for chunks
                            chunks_with_embeddings = self._process_chunks_with_embeddings(
                                processing_result['chunks'], 
                                str(file_path)
                            )
                            
                            # Store in FAISS index
                            if chunks_with_embeddings:
                                self.faiss_service.upsert_chunks(chunks_with_embeddings)
                            
                            documents_processed += 1
                            total_chunks += processing_result['total_chunks']
                            total_sections += processing_result['total_sections']
                            processing_results.append(processing_result)
                            
                            logger.info(f"Successfully processed {file_path.name}: "
                                      f"{processing_result['total_chunks']} chunks, "
                                      f"{processing_result['total_sections']} sections")
                        else:
                            logger.error(f"Error processing {file_path.name}: {processing_result['error']}")
                            
                    except Exception as e:
                        logger.error(f"Error processing seed document {file_path}: {e}")
                        continue
            
            # Save index
            self.faiss_service.save_index()
            
            # Generate processing summary
            summary = self._generate_ingestion_summary(processing_results)
            
            logger.info(f"Seed document ingestion completed: {documents_processed} documents, "
                       f"{total_chunks} chunks, {total_sections} sections")
            
            return {
                "status": "success",
                "message": f"Successfully ingested {documents_processed} seed documents",
                "documents_processed": documents_processed,
                "chunks_created": total_chunks,
                "sections_detected": total_sections,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error in seed document ingestion: {e}")
            return {
                "status": "error",
                "message": f"Error ingesting seed documents: {str(e)}",
                "documents_processed": 0,
                "chunks_created": 0,
                "sections_detected": 0
            }
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content based on file type"""
        try:
            file_type = file_path.suffix.lower()
            
            if file_type == '.md' or file_type == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_type == '.pdf':
                return self._read_pdf_content(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _read_pdf_content(self, file_path: Path) -> Optional[str]:
        """Read PDF content with fallback support"""
        try:
            # Try PyMuPDF first
            try:
                import fitz
                doc = fitz.open(file_path)
                content = ""
                for page in doc:
                    content += page.get_text()
                doc.close()
                if content.strip():
                    return content
            except ImportError:
                logger.debug("PyMuPDF not available, trying PyPDF2")
            except Exception as e:
                logger.debug(f"PyMuPDF failed: {e}")
            
            # Fallback to PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                    if content.strip():
                        return content
            except ImportError:
                logger.warning("PyPDF2 not available")
            except Exception as e:
                logger.debug(f"PyPDF2 failed: {e}")
            
            logger.error(f"Failed to extract text from PDF: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return None
    
    def _process_chunks_with_embeddings(self, chunks: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Process chunks and generate embeddings with section metadata"""
        try:
            chunks_with_embeddings = []
            
            for chunk in chunks:
                try:
                    # Generate embedding for chunk content
                    embedding = self.embedding_service.generate_embeddings([chunk['content']])
                    if not embedding:
                        logger.warning(f"Failed to generate embedding for chunk {chunk['id']}")
                        continue
                    
                    # Create chunk with embedding and section metadata
                    chunk_with_embedding = {
                        'id': chunk['id'],
                        'content': chunk['content'],
                        'embedding': embedding[0],
                        'metadata': {
                            'filename': filename,
                            'chunk_id': chunk['id'],
                            'start_line': chunk['metadata']['start_line'],
                            'end_line': chunk['metadata']['end_line'],
                            'line_count': chunk['metadata']['line_count'],
                            'content_length': chunk['metadata']['content_length'],
                            'section_type': chunk['section_info']['primary_type'],
                            'section_hpath': chunk['section_info']['primary_hpath'],
                            'all_section_types': chunk['section_info']['all_types'],
                            'all_hierarchy_paths': chunk['section_info']['all_paths'],
                            'has_commands': chunk['metadata']['has_commands'],
                            'has_metrics': chunk['metadata']['has_metrics'],
                            'total_bullet_points': chunk['metadata']['total_bullet_points'],
                            'total_code_blocks': chunk['metadata']['total_code_blocks']
                        }
                    }
                    
                    chunks_with_embeddings.append(chunk_with_embedding)
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk.get('id', 'unknown')}: {e}")
                    continue
            
            return chunks_with_embeddings
            
        except Exception as e:
            logger.error(f"Error processing chunks with embeddings: {e}")
            return []
    
    def _generate_ingestion_summary(self, processing_results: List[Dict[str, Any]]) -> str:
        """Generate a summary of the ingestion process"""
        try:
            if not processing_results:
                return "No documents were processed."
            
            summary = "# Document Ingestion Summary\n\n"
            summary += f"## Overview\n\n"
            summary += f"- **Total Documents:** {len(processing_results)}\n"
            summary += f"- **Total Chunks:** {sum(r['total_chunks'] for r in processing_results)}\n"
            summary += f"- **Total Sections:** {sum(r['total_sections'] for r in processing_results)}\n\n"
            
            # Document-level summary
            summary += "## Document Details\n\n"
            for result in processing_results:
                summary += f"### {result['filename']}\n\n"
                summary += f"- **Chunks:** {result['total_chunks']}\n"
                summary += f"- **Sections:** {result['total_sections']}\n"
                
                if 'section_summary' in result:
                    section_summary = result['section_summary']
                    if 'section_types' in section_summary:
                        summary += f"- **Section Types:**\n"
                        for section_type, count in section_summary['section_types'].items():
                            summary += f"  - {section_type}: {count}\n"
                
                summary += "\n"
            
            # Aggregate section analysis
            summary += "## Aggregate Section Analysis\n\n"
            all_section_types = {}
            total_bullet_points = 0
            total_code_blocks = 0
            sections_with_commands = 0
            sections_with_metrics = 0
            
            for result in processing_results:
                if 'section_summary' in result:
                    section_summary = result['section_summary']
                    
                    # Aggregate section types
                    if 'section_types' in section_summary:
                        for section_type, count in section_summary['section_types'].items():
                            all_section_types[section_type] = all_section_types.get(section_type, 0) + count
                    
                    # Aggregate content stats
                    if 'content_stats' in section_summary:
                        content_stats = section_summary['content_stats']
                        total_bullet_points += content_stats.get('total_bullet_points', 0)
                        total_code_blocks += content_stats.get('total_code_blocks', 0)
                        sections_with_commands += content_stats.get('sections_with_commands', 0)
                        sections_with_metrics += content_stats.get('sections_with_metrics', 0)
            
            if all_section_types:
                summary += "### Section Type Distribution\n\n"
                for section_type, count in sorted(all_section_types.items(), key=lambda x: x[1], reverse=True):
                    summary += f"- **{section_type}**: {count}\n"
                summary += "\n"
            
            summary += "### Content Statistics\n\n"
            summary += f"- **Total Bullet Points:** {total_bullet_points}\n"
            summary += f"- **Total Code Blocks:** {total_code_blocks}\n"
            summary += f"- **Sections with Commands:** {sections_with_commands}\n"
            summary += f"- **Sections with Metrics:** {sections_with_metrics}\n\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating ingestion summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def ingest_single_document(self, file_path: str, content: str) -> Dict[str, Any]:
        """Ingest a single document with section detection"""
        try:
            logger.info(f"Ingesting single document: {file_path}")
            
            # Check if file has changed
            if not self.file_manager.is_file_changed(file_path, content):
                logger.info(f"File {file_path} has not changed, skipping ingestion")
                return {
                    "status": "skipped",
                    "message": "File has not changed",
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            # Process document with section detection
            processing_result = self.document_processor.process_document(file_path, content)
            
            if 'error' in processing_result:
                return {
                    "status": "error",
                    "message": f"Error processing document: {processing_result['error']}",
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            # Generate embeddings for chunks
            chunks_with_embeddings = self._process_chunks_with_embeddings(
                processing_result['chunks'], 
                file_path
            )
            
            if not chunks_with_embeddings:
                return {
                    "status": "error",
                    "message": "Failed to generate embeddings for chunks",
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            # Store in FAISS index
            self.faiss_service.upsert_chunks(chunks_with_embeddings)
            
            # Save index
            self.faiss_service.save_index()
            
            # Update file manifest
            self.file_manager.update_file_manifest(file_path, content)
            
            logger.info(f"Successfully ingested {file_path}: "
                       f"{processing_result['total_chunks']} chunks, "
                       f"{processing_result['total_sections']} sections")
            
            return {
                "status": "success",
                "message": f"Successfully ingested {file_path}",
                "chunks_created": processing_result['total_chunks'],
                "sections_detected": processing_result['total_sections'],
                "processing_result": processing_result
            }
            
        except Exception as e:
            logger.error(f"Error ingesting single document {file_path}: {e}")
            return {
                "status": "error",
                "message": f"Error ingesting document: {str(e)}",
                "chunks_created": 0,
                "sections_detected": 0
            }
    
    def ingest_uploaded_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Ingest an uploaded file with section detection"""
        try:
            # Save file to docs directory
            docs_path = f"/app/data/docs/{Path(file_path).name}"
            os.makedirs(os.path.dirname(docs_path), exist_ok=True)
            
            with open(docs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Ingest the saved file
            return self.ingest_single_document(docs_path, content)
            
        except Exception as e:
            logger.error(f"Error ingesting uploaded file {file_path}: {e}")
            return {
                "status": "error",
                "message": f"Error ingesting uploaded file: {str(e)}",
                "chunks_created": 0,
                "sections_detected": 0
            }
    
    def refresh_knowledge_base(self) -> Dict[str, Any]:
        """Refresh knowledge base by scanning for new/changed files"""
        try:
            docs_path = "/app/data/docs"
            if not os.path.exists(docs_path):
                return {
                    "status": "error",
                    "message": "Docs directory not found",
                    "files_processed": 0,
                    "chunks_created": 0,
                    "sections_detected": 0
                }
            
            files_processed = 0
            total_chunks = 0
            total_sections = 0
            
            for file_path in Path(docs_path).glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt', '.pdf', '.log']:
                    try:
                        content = self._read_file_content(file_path)
                        if content:
                            result = self.ingest_single_document(str(file_path), content)
                            if result['status'] == 'success':
                                files_processed += 1
                                total_chunks += result['chunks_created']
                                total_sections += result['sections_detected']
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        continue
            
            return {
                "status": "success",
                "message": f"Refreshed knowledge base: {files_processed} files processed",
                "files_processed": files_processed,
                "chunks_created": total_chunks,
                "sections_detected": total_sections
            }
            
        except Exception as e:
            logger.error(f"Error refreshing knowledge base: {e}")
            return {
                "status": "error",
                "message": f"Error refreshing knowledge base: {str(e)}",
                "files_processed": 0,
                "chunks_created": 0,
                "sections_detected": 0
            }
    
    def get_kb_status(self) -> Dict[str, Any]:
        """Get knowledge base status with section information"""
        try:
            # Get basic KB status
            kb_status = {
                "docs_count": 0,
                "docs": [],
                "index_ready": False,
                "total_chunks": 0,
                "total_sections": 0,
                "section_types": {},
                "content_stats": {}
            }
            
            # Count documents in docs directory
            docs_path = "/app/data/docs"
            if os.path.exists(docs_path):
                doc_files = list(Path(docs_path).glob("*"))
                kb_status["docs_count"] = len([f for f in doc_files if f.is_file() and f.suffix.lower() in ['.md', '.txt', '.pdf', '.log']])
                kb_status["docs"] = [f.name for f in doc_files if f.is_file() and f.suffix.lower() in ['.md', '.txt', '.pdf', '.log']]
            
            # Check index status
            if self.faiss_service.is_index_populated():
                kb_status["index_ready"] = True
                kb_status["total_chunks"] = len(self.faiss_service.metadata) if hasattr(self.faiss_service, 'metadata') else 0
                
                # Analyze section types from existing chunks
                if hasattr(self.faiss_service, 'metadata') and self.faiss_service.metadata:
                    section_types = {}
                    total_bullet_points = 0
                    total_code_blocks = 0
                    sections_with_commands = 0
                    sections_with_metrics = 0
                    
                    for chunk_metadata in self.faiss_service.metadata:
                        if isinstance(chunk_metadata, dict):
                            section_type = chunk_metadata.get('section_type', 'unknown')
                            section_types[section_type] = section_types.get(section_type, 0) + 1
                            
                            total_bullet_points += chunk_metadata.get('total_bullet_points', 0)
                            total_code_blocks += chunk_metadata.get('total_code_blocks', 0)
                            if chunk_metadata.get('has_commands', False):
                                sections_with_commands += 1
                            if chunk_metadata.get('has_metrics', False):
                                sections_with_metrics += 1
                    
                    kb_status["section_types"] = section_types
                    kb_status["content_stats"] = {
                        "total_bullet_points": total_bullet_points,
                        "total_code_blocks": total_code_blocks,
                        "sections_with_commands": sections_with_commands,
                        "sections_with_metrics": sections_with_metrics
                    }
            
            return kb_status
            
        except Exception as e:
            logger.error(f"Error getting KB status: {e}")
            return {
                "docs_count": 0,
                "docs": [],
                "index_ready": False,
                "error": str(e)
            }
