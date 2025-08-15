import logging
import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import random

logger = logging.getLogger(__name__)

class RetrievalPipeline:
    """Advanced retrieval pipeline combining vector search, BM25, and MMR for diversity"""
    
    def __init__(self):
        self.vector_weight = 0.6
        self.bm25_weight = 0.4
        self.mmr_lambda = 0.7  # Diversity vs relevance trade-off
        self.max_rerank_candidates = 20
        self.target_diversity = {
            'files': 3,  # Target distinct files
            'section_types': ['first_checks', 'fix', 'validate', 'policy'],
            'min_section_coverage': 2  # At least 2 different section types
        }
        
        # Generic intent hints for query rewriting
        self.intent_hints = {
            'cpu': ['cpu', 'processor', 'load', 'usage', 'performance', 'spike', 'high'],
            'latency': ['latency', 'response', 'time', 'slow', 'delay', 'wait'],
            'cache': ['cache', 'redis', 'memcached', 'hit', 'miss', 'eviction'],
            'queue': ['queue', 'backlog', 'depth', 'processing', 'dlq', 'dead letter'],
            'pool': ['pool', 'connection', 'thread', 'worker', 'process', 'resource'],
            'memory': ['memory', 'ram', 'swap', 'leak', 'usage', 'allocation'],
            'disk': ['disk', 'storage', 'space', 'io', 'throughput', 'latency'],
            'network': ['network', 'bandwidth', 'packet', 'drop', 'timeout', 'connection']
        }
        
        # Cross-encoder availability (can be set externally)
        self.cross_encoder_available = False
        self.cross_encoder_model = None
        
    def retrieve_diverse_results(self, query: str, faiss_service, top_k: int = 8) -> List[Tuple[Any, float]]:
        """
        Main retrieval method combining multiple strategies for diverse results
        
        Args:
            query: User query
            faiss_service: FAISS service instance
            top_k: Number of results to return
            
        Returns:
            List of (chunk, score) tuples with diverse coverage
        """
        try:
            logger.info(f"Starting diverse retrieval for query: {query[:100]}...")
            
            # Step 1: Query rewriting with intent hints
            rewritten_query = self._rewrite_query_with_intent(query)
            logger.info(f"Rewritten query: {rewritten_query}")
            
            # Step 2: Vector search
            vector_results = self._vector_search(query, faiss_service, top_k * 2)
            logger.info(f"Vector search returned {len(vector_results)} results")
            
            # Step 3: BM25 search
            bm25_results = self._bm25_search(rewritten_query, faiss_service, top_k * 2)
            logger.info(f"BM25 search returned {len(bm25_results)} results")
            
            # Step 4: Merge and normalize scores
            merged_results = self._merge_results(vector_results, bm25_results, top_k * 3)
            logger.info(f"Merged results: {len(merged_results)} candidates")
            
            # Step 5: Optional cross-encoder re-ranking
            if self.cross_encoder_available and self.cross_encoder_model:
                logger.info("Applying cross-encoder re-ranking")
                merged_results = self._cross_encoder_rerank(query, merged_results)
            
            # Step 6: MMR for diversity
            diverse_results = self._mmr_diversity_selection(query, merged_results, top_k)
            logger.info(f"MMR diversity selection returned {len(diverse_results)} results")
            
            # Step 7: Ensure diversity constraints
            final_results = self._enforce_diversity_constraints(diverse_results, top_k)
            logger.info(f"Final diverse results: {len(final_results)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in retrieval pipeline: {e}")
            # Fallback to simple vector search
            return self._fallback_vector_search(query, faiss_service, top_k)
    
    def _rewrite_query_with_intent(self, query: str) -> str:
        """
        Rewrite query using generic intent hints to improve recall
        
        Args:
            query: Original query
            
        Returns:
            Rewritten query with intent hints
        """
        try:
            query_lower = query.lower()
            rewritten_parts = [query]
            
            # Add relevant intent hints based on query content
            for intent, keywords in self.intent_hints.items():
                if any(keyword in query_lower for keyword in keywords):
                    # Add intent-specific terms to improve recall
                    if intent == 'cpu':
                        rewritten_parts.extend(['performance', 'monitoring', 'metrics'])
                    elif intent == 'latency':
                        rewritten_parts.extend(['response time', 'performance', 'bottleneck'])
                    elif intent == 'cache':
                        rewritten_parts.extend(['redis', 'memcached', 'performance'])
                    elif intent == 'queue':
                        rewritten_parts.extend(['backlog', 'processing', 'throughput'])
                    elif intent == 'pool':
                        rewritten_parts.extend(['resources', 'scalability', 'performance'])
                    elif intent == 'memory':
                        rewritten_parts.extend(['ram', 'allocation', 'leak'])
                    elif intent == 'disk':
                        rewritten_parts.extend(['storage', 'io', 'throughput'])
                    elif intent == 'network':
                        rewritten_parts.extend(['bandwidth', 'connectivity', 'timeout'])
            
            # Combine original query with intent hints
            rewritten_query = ' '.join(rewritten_parts)
            
            # Remove duplicates and normalize
            words = rewritten_query.split()
            unique_words = []
            for word in words:
                if word not in unique_words:
                    unique_words.append(word)
            
            return ' '.join(unique_words)
            
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return query
    
    def _vector_search(self, query: str, faiss_service, top_k: int) -> List[Tuple[Any, float]]:
        """Perform vector search using FAISS"""
        try:
            # Generate query embedding
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_embeddings([query])
            
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Search FAISS index
            search_results = faiss_service.search(query_embedding[0], k=top_k)
            
            # Normalize scores to [0, 1] range
            if search_results:
                max_score = max(score for _, score in search_results)
                min_score = min(score for _, score in search_results)
                score_range = max_score - min_score if max_score != min_score else 1
                
                normalized_results = []
                for chunk, score in search_results:
                    normalized_score = (score - min_score) / score_range
                    normalized_results.append((chunk, normalized_score))
                
                return normalized_results
            
            return []
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _bm25_search(self, query: str, faiss_service, top_k: int) -> List[Tuple[Any, float]]:
        """Perform BM25 search for better keyword matching"""
        try:
            if not hasattr(faiss_service, 'metadata') or not faiss_service.metadata:
                logger.warning("No metadata available for BM25 search")
                return []
            
            # Prepare documents for BM25
            documents = []
            chunk_map = {}
            
            for chunk_data in faiss_service.metadata:
                if isinstance(chunk_data, dict):
                    content = chunk_data.get('content', '')
                    chunk_id = chunk_data.get('chunk_id', 'unknown')
                    
                    if content:
                        # Clean content for BM25
                        clean_content = self._clean_content_for_bm25(content)
                        documents.append(clean_content)
                        chunk_map[len(documents) - 1] = chunk_data
            
            if not documents:
                logger.warning("No valid documents for BM25 search")
                return []
            
            # Initialize BM25
            tokenized_docs = [doc.split() for doc in documents]
            bm25 = BM25Okapi(tokenized_docs)
            
            # Search
            tokenized_query = query.split()
            scores = bm25.get_scores(tokenized_query)
            
            # Get top results
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Convert to (chunk, score) format
            bm25_results = []
            for idx in top_indices:
                if idx < len(chunk_map):
                    chunk = chunk_map[idx]
                    score = scores[idx]
                    
                    # Normalize score to [0, 1] range
                    normalized_score = min(score / max(scores) if max(scores) > 0 else 0, 1.0)
                    bm25_results.append((chunk, normalized_score))
            
            return bm25_results
            
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _clean_content_for_bm25(self, content: str) -> str:
        """Clean content for BM25 processing"""
        try:
            # Remove markdown formatting
            content = re.sub(r'[#*`]', '', content)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            # Convert to lowercase
            content = content.lower()
            return content.strip()
        except Exception as e:
            logger.error(f"Error cleaning content: {e}")
            return content
    
    def _merge_results(self, vector_results: List[Tuple[Any, float]], 
                      bm25_results: List[Tuple[Any, float]], 
                      top_k: int) -> List[Tuple[Any, float]]:
        """
        Merge vector and BM25 results with score normalization
        
        Args:
            vector_results: Vector search results
            bm25_results: BM25 search results
            top_k: Maximum number of results
            
        Returns:
            Merged and normalized results
        """
        try:
            # Create chunk ID to result mapping
            merged_map = {}
            
            # Add vector results
            for chunk, score in vector_results:
                chunk_id = self._get_chunk_id(chunk)
                if chunk_id:
                    merged_map[chunk_id] = {
                        'chunk': chunk,
                        'vector_score': score,
                        'bm25_score': 0.0,
                        'combined_score': score * self.vector_weight
                    }
            
            # Add/update with BM25 results
            for chunk, score in bm25_results:
                chunk_id = self._get_chunk_id(chunk)
                if chunk_id:
                    if chunk_id in merged_map:
                        # Update existing entry
                        merged_map[chunk_id]['bm25_score'] = score
                        merged_map[chunk_id]['combined_score'] += score * self.bm25_weight
                    else:
                        # Add new entry
                        merged_map[chunk_id] = {
                            'chunk': chunk,
                            'vector_score': 0.0,
                            'bm25_score': score,
                            'combined_score': score * self.bm25_weight
                        }
            
            # Convert to list and sort by combined score
            merged_list = list(merged_map.values())
            merged_list.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Return top_k results
            return [(item['chunk'], item['combined_score']) for item in merged_list[:top_k]]
            
        except Exception as e:
            logger.error(f"Error merging results: {e}")
            # Fallback to vector results only
            return vector_results[:top_k]
    
    def _get_chunk_id(self, chunk) -> Optional[str]:
        """Extract chunk ID from chunk object"""
        try:
            if isinstance(chunk, dict):
                return chunk.get('chunk_id') or chunk.get('id')
            elif hasattr(chunk, 'chunk_id'):
                return chunk.chunk_id
            elif hasattr(chunk, 'id'):
                return chunk.id
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting chunk ID: {e}")
            return None
    
    def _cross_encoder_rerank(self, query: str, candidates: List[Tuple[Any, float]]) -> List[Tuple[Any, float]]:
        """
        Re-rank candidates using cross-encoder if available
        
        Args:
            query: User query
            candidates: List of (chunk, score) tuples
            
        Returns:
            Re-ranked candidates
        """
        try:
            if not self.cross_encoder_available or not self.cross_encoder_model:
                logger.info("Cross-encoder not available, skipping re-ranking")
                return candidates
            
            # Limit candidates for re-ranking
            rerank_candidates = candidates[:self.max_rerank_candidates]
            
            # Prepare query-document pairs
            query_doc_pairs = []
            for chunk, _ in rerank_candidates:
                content = self._extract_chunk_content(chunk)
                if content:
                    query_doc_pairs.append([query, content])
            
            if not query_doc_pairs:
                return candidates
            
            # Get cross-encoder scores
            try:
                scores = self.cross_encoder_model.predict(query_doc_pairs)
                
                # Update scores
                reranked_results = []
                for i, (chunk, _) in enumerate(rerank_candidates):
                    if i < len(scores):
                        reranked_results.append((chunk, float(scores[i])))
                    else:
                        reranked_results.append((chunk, 0.0))
                
                # Sort by cross-encoder scores
                reranked_results.sort(key=lambda x: x[1], reverse=True)
                
                # Combine with original candidates
                reranked_ids = {self._get_chunk_id(chunk) for chunk, _ in reranked_results}
                remaining_candidates = [(chunk, score) for chunk, score in candidates 
                                     if self._get_chunk_id(chunk) not in reranked_ids]
                
                return reranked_results + remaining_candidates
                
            except Exception as e:
                logger.warning(f"Cross-encoder prediction failed: {e}")
                return candidates
            
        except Exception as e:
            logger.error(f"Error in cross-encoder re-ranking: {e}")
            return candidates
    
    def _extract_chunk_content(self, chunk) -> Optional[str]:
        """Extract content from chunk object"""
        try:
            if isinstance(chunk, dict):
                return chunk.get('content', '')
            elif hasattr(chunk, 'content'):
                return chunk.content
            else:
                return str(chunk)
        except Exception as e:
            logger.error(f"Error extracting chunk content: {e}")
            return None
    
    def _mmr_diversity_selection(self, query: str, candidates: List[Tuple[Any, float]], 
                                top_k: int) -> List[Tuple[Any, float]]:
        """
        Apply MMR (Maximal Marginal Relevance) for diversity selection
        
        Args:
            query: User query
            candidates: List of (chunk, score) tuples
            top_k: Number of results to select
            
        Returns:
            Diverse selection of results
        """
        try:
            if len(candidates) <= top_k:
                return candidates
            
            # Extract query embedding for similarity calculation
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.generate_embeddings([query])
            
            if not query_embedding:
                logger.warning("Failed to generate query embedding for MMR")
                return candidates[:top_k]
            
            # Initialize selected and remaining sets
            selected = []
            remaining = candidates.copy()
            
            # Select first result (highest relevance)
            if remaining:
                selected.append(remaining.pop(0))
            
            # Apply MMR for remaining selections
            while len(selected) < top_k and remaining:
                mmr_scores = []
                
                for chunk, score in remaining:
                    # Relevance to query
                    relevance = score
                    
                    # Diversity from already selected
                    diversity = 0.0
                    if selected:
                        diversity = self._calculate_diversity(chunk, selected)
                    
                    # MMR score
                    mmr_score = self.mmr_lambda * relevance + (1 - self.mmr_lambda) * diversity
                    mmr_scores.append((chunk, score, mmr_score))
                
                # Select chunk with highest MMR score
                if mmr_scores:
                    mmr_scores.sort(key=lambda x: x[2], reverse=True)
                    best_chunk, best_score, _ = mmr_scores[0]
                    
                    # Remove from remaining and add to selected
                    remaining = [(chunk, score) for chunk, score in remaining if chunk != best_chunk]
                    selected.append((best_chunk, best_score))
            
            return selected
            
        except Exception as e:
            logger.error(f"Error in MMR diversity selection: {e}")
            return candidates[:top_k]
    
    def _calculate_diversity(self, chunk, selected_chunks: List[Tuple[Any, float]]) -> float:
        """
        Calculate diversity of a chunk relative to selected chunks
        
        Args:
            chunk: Candidate chunk
            selected_chunks: Already selected chunks
            
        Returns:
            Diversity score [0, 1]
        """
        try:
            if not selected_chunks:
                return 1.0
            
            # Extract features for diversity calculation
            chunk_features = self._extract_chunk_features(chunk)
            
            max_similarity = 0.0
            for selected_chunk, _ in selected_chunks:
                selected_features = self._extract_chunk_features(selected_chunk)
                
                # Calculate similarity based on features
                similarity = self._calculate_feature_similarity(chunk_features, selected_features)
                max_similarity = max(max_similarity, similarity)
            
            # Diversity is inverse of similarity
            diversity = 1.0 - max_similarity
            return max(0.0, diversity)
            
        except Exception as e:
            logger.error(f"Error calculating diversity: {e}")
            return 0.5  # Default diversity score
    
    def _extract_chunk_features(self, chunk) -> Dict[str, Any]:
        """Extract features from chunk for diversity calculation"""
        try:
            features = {
                'filename': '',
                'section_type': 'unknown',
                'content_length': 0,
                'has_commands': False,
                'has_metrics': False
            }
            
            if isinstance(chunk, dict):
                features['filename'] = chunk.get('filename', '')
                features['section_type'] = chunk.get('section_type', 'unknown')
                features['content_length'] = chunk.get('content_length', 0)
                features['has_commands'] = chunk.get('has_commands', False)
                features['has_metrics'] = chunk.get('has_metrics', False)
            elif hasattr(chunk, 'metadata'):
                metadata = chunk.metadata
                if isinstance(metadata, dict):
                    features['filename'] = metadata.get('filename', '')
                    features['section_type'] = metadata.get('section_type', 'unknown')
                    features['content_length'] = metadata.get('content_length', 0)
                    features['has_commands'] = metadata.get('has_commands', False)
                    features['has_metrics'] = metadata.get('has_metrics', False)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting chunk features: {e}")
            return {'filename': '', 'section_type': 'unknown', 'content_length': 0, 
                   'has_commands': False, 'has_metrics': False}
    
    def _calculate_feature_similarity(self, features1: Dict[str, Any], 
                                    features2: Dict[str, Any]) -> float:
        """Calculate similarity between two feature sets"""
        try:
            similarity = 0.0
            total_weight = 0.0
            
            # Filename similarity (high weight)
            if features1['filename'] == features2['filename']:
                similarity += 0.4
            total_weight += 0.4
            
            # Section type similarity (medium weight)
            if features1['section_type'] == features2['section_type']:
                similarity += 0.3
            total_weight += 0.3
            
            # Content length similarity (low weight)
            length_diff = abs(features1['content_length'] - features2['content_length'])
            max_length = max(features1['content_length'], features2['content_length'])
            if max_length > 0:
                length_similarity = 1.0 - (length_diff / max_length)
                similarity += 0.1 * length_similarity
            total_weight += 0.1
            
            # Command/metrics similarity (low weight)
            if features1['has_commands'] == features2['has_commands']:
                similarity += 0.1
            if features1['has_metrics'] == features2['has_metrics']:
                similarity += 0.1
            total_weight += 0.2
            
            # Normalize by total weight
            if total_weight > 0:
                similarity = similarity / total_weight
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating feature similarity: {e}")
            return 0.5
    
    def _enforce_diversity_constraints(self, results: List[Tuple[Any, float]], 
                                     top_k: int) -> List[Tuple[Any, float]]:
        """
        Enforce diversity constraints across files and section types
        
        Args:
            results: Current results
            top_k: Target number of results
            
        Returns:
            Results with enforced diversity constraints
        """
        try:
            if len(results) <= top_k:
                return results
            
            # Analyze current diversity
            current_files = set()
            current_section_types = set()
            diverse_results = []
            
            # First pass: ensure minimum diversity
            for chunk, score in results:
                chunk_id = self._get_chunk_id(chunk)
                if not chunk_id:
                    continue
                
                features = self._extract_chunk_features(chunk)
                filename = features['filename']
                section_type = features['section_type']
                
                # Check if this chunk improves diversity
                improves_diversity = False
                
                # File diversity
                if filename not in current_files:
                    improves_diversity = True
                
                # Section type diversity
                if section_type in self.target_diversity['section_types']:
                    if section_type not in current_section_types:
                        improves_diversity = True
                
                # Add if it improves diversity or we need more results
                if improves_diversity or len(diverse_results) < self.target_diversity['min_section_coverage']:
                    diverse_results.append((chunk, score))
                    current_files.add(filename)
                    current_section_types.add(section_type)
                    
                    if len(diverse_results) >= top_k:
                        break
            
            # Fill remaining slots with best remaining results
            remaining_results = [(chunk, score) for chunk, score in results 
                               if (chunk, score) not in diverse_results]
            
            while len(diverse_results) < top_k and remaining_results:
                diverse_results.append(remaining_results.pop(0))
            
            return diverse_results
            
        except Exception as e:
            logger.error(f"Error enforcing diversity constraints: {e}")
            return results[:top_k]
    
    def _fallback_vector_search(self, query: str, faiss_service, top_k: int) -> List[Tuple[Any, float]]:
        """Fallback to simple vector search if pipeline fails"""
        try:
            logger.info("Using fallback vector search")
            return self._vector_search(query, faiss_service, top_k)
        except Exception as e:
            logger.error(f"Fallback vector search failed: {e}")
            return []
    
    def set_cross_encoder(self, model, available: bool = True):
        """Set cross-encoder model for re-ranking"""
        self.cross_encoder_model = model
        self.cross_encoder_available = available
        logger.info(f"Cross-encoder set: available={available}")
    
    def get_retrieval_stats(self, results: List[Tuple[Any, float]]) -> Dict[str, Any]:
        """Get statistics about retrieval results"""
        try:
            if not results:
                return {"error": "No results to analyze"}
            
            stats = {
                "total_results": len(results),
                "files_covered": set(),
                "section_types": set(),
                "score_distribution": {
                    "min": float('inf'),
                    "max": float('-inf'),
                    "mean": 0.0
                }
            }
            
            scores = []
            for chunk, score in results:
                scores.append(score)
                
                # Extract features
                features = self._extract_chunk_features(chunk)
                stats["files_covered"].add(features["filename"])
                stats["section_types"].add(features["section_type"])
            
            # Convert sets to lists for JSON serialization
            stats["files_covered"] = list(stats["files_covered"])
            stats["section_types"] = list(stats["section_types"])
            
            # Score statistics
            if scores:
                stats["score_distribution"]["min"] = min(scores)
                stats["score_distribution"]["max"] = max(scores)
                stats["score_distribution"]["mean"] = sum(scores) / len(scores)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {"error": str(e)}

