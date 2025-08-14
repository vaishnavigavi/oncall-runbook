import os
import logging
import pickle
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, using mock implementation")

logger = logging.getLogger(__name__)

class FAISSService:
    """Service for managing FAISS vector index"""
    
    def __init__(self):
        self.index_dir = "/app/data/index"
        self.index_file = os.path.join(self.index_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(self.index_dir, "metadata.pkl")
        
        self.index = None
        self.metadata = []
        self.dimension = int(os.getenv("FAISS_DIMENSION", "1536"))
        
        # Ensure index directory exists
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                # Load FAISS index
                if FAISS_AVAILABLE:
                    self.index = faiss.read_index(self.index_file)
                    logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
                else:
                    logger.warning("FAISS not available, using mock index")
                    self.index = None
                
                # Load metadata
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} chunks")
            else:
                logger.info("No existing index found, will create new one")
        except Exception as e:
            logger.error(f"Error loading existing index: {e}")
            self.index = None
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            if self.index is not None and FAISS_AVAILABLE:
                faiss.write_index(self.index, self.index_file)
                logger.info("FAISS index saved to disk")
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info("Metadata saved to disk")
            
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def save_index(self):
        """Public method to save the index"""
        return self._save_index()
    
    def ensure_index(self):
        """Ensure index exists and is ready (do not wipe existing index)"""
        try:
            if self.index is not None:
                logger.info("Index already exists and is ready")
                return True
            
            if FAISS_AVAILABLE:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
            else:
                logger.warning("FAISS not available, using mock index")
                self.index = None
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring index: {e}")
            return False
    
    def is_index_populated(self) -> bool:
        """Check if the index has content (vectors and metadata)"""
        try:
            if self.index is None:
                return False
            
            if FAISS_AVAILABLE:
                return self.index.ntotal > 0 and len(self.metadata) > 0
            else:
                return len(self.metadata) > 0
        except Exception as e:
            logger.error(f"Error checking if index is populated: {e}")
            return False
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get detailed status of the FAISS index"""
        try:
            if self.index is None:
                return {
                    "index_exists": False,
                    "index_type": "none",
                    "total_vectors": 0,
                    "dimension": self.dimension,
                    "metadata_count": len(self.metadata)
                }
            
            if FAISS_AVAILABLE:
                return {
                    "index_exists": True,
                    "index_type": "faiss",
                    "total_vectors": self.index.ntotal,
                    "dimension": self.index.d,
                    "metadata_count": len(self.metadata),
                    "is_trained": self.index.is_trained
                }
            else:
                return {
                    "index_exists": True,
                    "index_type": "mock",
                    "total_vectors": len(self.metadata),
                    "dimension": self.dimension,
                    "metadata_count": len(self.metadata)
                }
        except Exception as e:
            logger.error(f"Error getting index status: {e}")
            return {
                "index_exists": False,
                "index_type": "error",
                "error": str(e)
            }
    
    def upsert_chunks(self, chunks: List[Any]):
        """Upsert chunks to the index (add or update)"""
        try:
            if not chunks:
                logger.warning("No chunks provided for upsert")
                return False
            
            # Ensure index exists
            self.ensure_index()
            
            # Extract embeddings and metadata
            embeddings = []
            new_metadata = []
            
            for chunk in chunks:
                if hasattr(chunk, 'embedding') and chunk.embedding is not None:
                    embeddings.append(chunk.embedding)
                    
                    # Create metadata entry
                    metadata_entry = {
                        'id': chunk.id,
                        'content': chunk.content,
                        'chunk_index': getattr(chunk, 'chunk_index', 0),
                        'heading': getattr(chunk, 'heading', ''),
                        'metadata': getattr(chunk, 'metadata', {})
                    }
                    new_metadata.append(metadata_entry)
                else:
                    logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
            
            if not embeddings:
                logger.error("No valid embeddings found in chunks")
                return False
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            if FAISS_AVAILABLE and self.index is not None:
                # Add vectors to FAISS index
                self.index.add(embeddings_array)
                logger.info(f"Added {len(embeddings)} vectors to FAISS index")
            else:
                logger.info(f"Mock mode: would add {len(embeddings)} vectors")
            
            # Add metadata
            self.metadata.extend(new_metadata)
            logger.info(f"Added metadata for {len(new_metadata)} chunks")
            
            # Save to disk
            self._save_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            return False
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Tuple[Any, float]]:
        """Search for similar chunks"""
        try:
            if not self.is_index_populated():
                logger.warning("Index is not populated, cannot perform search")
                return []
            
            if FAISS_AVAILABLE and self.index is not None:
                # Convert query to numpy array
                query_array = np.array([query_embedding], dtype=np.float32)
                
                # Search FAISS index
                scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
                
                # Return results with metadata
                results = []
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self.metadata):
                        chunk = self._create_chunk_from_metadata(self.metadata[idx])
                        results.append((chunk, float(score)))
                
                return results
            else:
                # Mock search - return random results
                logger.info("Mock mode: returning random search results")
                import random
                random.shuffle(self.metadata)
                
                results = []
                for i, metadata in enumerate(self.metadata[:k]):
                    chunk = self._create_chunk_from_metadata(metadata)
                    # Generate mock similarity score
                    score = random.uniform(0.1, 0.9)
                    results.append((chunk, score))
                
                return results
                
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def _create_chunk_from_metadata(self, metadata: Dict[str, Any]) -> Any:
        """Create a chunk object from metadata"""
        # Create a simple chunk object with the required attributes
        class SimpleChunk:
            def __init__(self, metadata):
                self.id = metadata.get('id', '')
                self.content = metadata.get('content', '')
                self.chunk_index = metadata.get('chunk_index', 0)
                self.heading = metadata.get('heading', '')
                self.metadata = metadata.get('metadata', {})
        
        return SimpleChunk(metadata)
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index"""
        try:
            status = self.get_index_status()
            
            # Count files by type
            file_types = {}
            for meta in self.metadata:
                filename = meta.get('metadata', {}).get('filename', 'unknown')
                ext = os.path.splitext(filename)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "index_status": status,
                "file_types": file_types,
                "total_files": len(set(meta.get('metadata', {}).get('filename', '') for meta in self.metadata)),
                "total_chunks": len(self.metadata)
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}
