import os
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using OpenAI or Azure OpenAI"""
    
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        self.dimension = int(os.getenv("FAISS_DIMENSION", "1536"))
        
        # Defer client initialization until first use
        self.client = None
        self.model = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure the service is initialized before use"""
        if not self._initialized:
            if self.provider == "azure":
                self._init_azure_client()
            else:
                self._init_openai_client()
            self._initialized = True
    
    def _init_azure_client(self):
        """Initialize Azure OpenAI client"""
        try:
            from openai import AzureOpenAI
            
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
            
            if not api_key or not endpoint:
                logger.warning("Azure OpenAI credentials not configured, using mock embeddings")
                self.client = None
                self.model = None
                return
            
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version
            )
            self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            
            if not self.model:
                logger.warning("Azure OpenAI deployment name not configured")
                self.client = None
                return
                
        except ImportError:
            logger.warning("OpenAI library not available, using mock embeddings")
            self.client = None
            self.model = None
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            
            if not api_key:
                logger.warning("OpenAI API key not configured, using mock embeddings")
                self.client = None
                self.model = None
                return
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
            
        except ImportError:
            logger.warning("OpenAI library not available, using mock embeddings")
            self.client = None
            self.model = None
    
    def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for testing when API is not available"""
        import random
        
        embeddings = []
        for text in texts:
            # Generate deterministic mock embeddings based on text content
            random.seed(hash(text) % 2**32)
            embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
            # Normalize to unit vector
            norm = sum(x*x for x in embedding) ** 0.5
            embedding = [x/norm for x in embedding]
            embeddings.append(embedding)
        
        return embeddings
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []
        
        # Try to use real API first
        if self.client and self.model:
            try:
                self._ensure_initialized()
                
                if self.provider == "azure":
                    response = self.client.embeddings.create(
                        input=texts,
                        model=self.model
                    )
                else:
                    response = self.client.embeddings.create(
                        input=texts,
                        model=self.model
                    )
                
                embeddings = [embedding.embedding for embedding in response.data]
                return embeddings
                
            except Exception as e:
                logger.warning(f"Error generating embeddings with API, falling back to mock: {e}")
        
        # Fallback to mock embeddings
        logger.info("Using mock embeddings (API not available or failed)")
        return self._generate_mock_embeddings(texts)
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.dimension
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct dimension"""
        return len(embedding) == self.dimension
    
    def is_available(self) -> bool:
        """Check if the real embedding service is available"""
        return self.client is not None and self.model is not None
