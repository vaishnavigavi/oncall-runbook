#!/usr/bin/env python3
"""
Document ingestion script for OnCall Runbook API
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, '/app')

from app.services.ingestion_service import IngestionService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main ingestion function"""
    logger.info("Starting document ingestion process...")
    
    try:
        # Initialize the ingestion service
        ingestion_service = IngestionService()
        
        # Ingest seed documents
        response = ingestion_service.ingest_seed_documents()
        
        if response.success:
            logger.info(f"Ingestion completed successfully!")
            logger.info(f"Documents processed: {response.documents_processed}")
            logger.info(f"Chunks created: {response.chunks_created}")
            logger.info(f"Index updated: {response.index_updated}")
            logger.info(f"Message: {response.message}")
            
            # Get and display index stats
            stats = ingestion_service.get_index_stats()
            logger.info(f"Index stats: {stats}")
            
            return 0
        else:
            logger.error(f"Ingestion failed: {response.message}")
            return 1
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
