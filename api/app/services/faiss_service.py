import logging
import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

# Use scikit-learn instead of FAISS for Railway compatibility
try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class FAISSService:
    """Service for managing vector search using scikit-learn (FAISS alternative)"""
    
    def __init__(self):
        self.index_dir = "/app/data/index"
        self.index_file = f"{self.index_dir}/sklearn_index.pkl"
        self.metadata_file = f"{self.index_dir}/metadata.pkl"
        self.vectorizer = None
        self.vectors = None
        self.metadata = []
        self._ensure_index_dir()
    
    def _ensure_index_dir(self):
        """Ensure index directory exists"""
        Path(self.index_dir).mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """Load existing index if available"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                with open(self.index_file, 'rb') as f:
                    self.vectors = pickle.load(f)
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                # Initialize vectorizer
                self.vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                
                # Fit vectorizer on existing data
                if self.metadata:
                    texts = [item.get('text', '') for item in self.metadata]
                    self.vectorizer.fit(texts)
                
                logger.info(f"Loaded existing index with {len(self.metadata)} vectors")
                return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
        
        return False
    
    def _save_index(self):
        """Save index to disk"""
        try:
            if self.vectors is not None:
                with open(self.index_file, 'wb') as f:
                    pickle.dump(self.vectors, f)
                with open(self.metadata_file, 'wb') as f:
                    pickle.dump(self.metadata, f)
                logger.info("Index saved successfully")
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
            if not self._load_index():
                # Initialize new index
                self.vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                self.vectors = None
                self.metadata = []
                logger.info("Initialized new index")
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring index: {e}")
            return False
    
    def is_index_populated(self) -> bool:
        """Check if index has vectors"""
        return self.vectors is not None and len(self.metadata) > 0
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get index status information"""
        try:
            index_exists = os.path.exists(self.index_file) and os.path.exists(self.metadata_file)
            total_vectors = len(self.metadata) if self.metadata else 0
            
            return {
                "index_exists": index_exists,
                "total_vectors": total_vectors,
                "index_size_mb": os.path.getsize(self.index_file) / (1024 * 1024) if index_exists else 0,
                "last_updated": datetime.now().isoformat() if self.metadata else None,
                "vectorizer_ready": self.vectorizer is not None
            }
        except Exception as e:
            logger.error(f"Error getting index status: {e}")
            return {
                "index_exists": False,
                "total_vectors": 0,
                "error": str(e)
            }
    
    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add or update chunks in the index"""
        try:
            if not chunks:
                return True
            
            # Extract texts for vectorization
            texts = [chunk.get('text', '') for chunk in chunks]
            
            # Fit vectorizer on new texts
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
            
            # Transform texts to vectors
            new_vectors = self.vectorizer.fit_transform(texts).toarray()
            
            # Add new metadata
            for i, chunk in enumerate(chunks):
                chunk['vector_id'] = len(self.metadata) + i
                self.metadata.append(chunk)
            
            # Update vectors
            if self.vectors is None:
                self.vectors = new_vectors
            else:
                self.vectors = np.vstack([self.vectors, new_vectors])
            
            # Save index
            self._save_index()
            
            logger.info(f"Upserted {len(chunks)} chunks, total vectors: {len(self.metadata)}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            return False
    
    def search(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            if not self.is_index_populated():
                logger.warning("Index not populated, returning empty results")
                return []
            
            # Transform query to vector
            query_vector = self.vectorizer.transform([query]).toarray()
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            
            # Get top-k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    result = self.metadata[idx].copy()
                    result['similarity'] = float(similarities[idx])
                    results.append(result)
            
            logger.info(f"Search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []
    
    def clear_index(self):
        """Clear the entire index"""
        try:
            self.vectors = None
            self.metadata = []
            self.vectorizer = None
            
            # Remove index files
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            logger.info("Index cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False
