import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ActionableBullet:
    """Represents an actionable bullet point with provenance"""
    content: str
    verb: str
    section_type: str
    source_chunk: Any
    source_file: str
    chunk_id: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class PlannedResponse:
    """Structured response plan with actionable content"""
    first_checks: List[ActionableBullet]
    why_explanation: str
    fix_steps: List[ActionableBullet]
    validate_steps: List[ActionableBullet]
    sources: List[str]
    has_fix: bool
    has_validate: bool
    metadata: Dict[str, Any]

class Planner:
    """Service for extracting and organizing actionable content from retrieved chunks"""
    
    def __init__(self):
        # Imperative verb patterns for actionable content
        self.action_verbs = [
            r'\b(?:Check|Verify|Review|Set|Increase|Scale|Rollback|Pin|Pre-warm|Move|Cap|Raise|Switch)\b',
            r'\b(?:Restart|Restore|Clear|Flush|Reset|Reload|Refresh|Update|Upgrade|Downgrade)\b',
            r'\b(?:Enable|Disable|Configure|Tune|Optimize|Adjust|Modify|Change|Replace|Remove)\b',
            r'\b(?:Monitor|Watch|Track|Log|Alert|Notify|Report|Document|Test|Validate)\b',
            r'\b(?:Connect|Disconnect|Bind|Unbind|Mount|Unmount|Attach|Detach|Link|Unlink)\b',
            r'\b(?:Start|Stop|Pause|Resume|Suspend|Kill|Terminate|Abort|Cancel|Skip)\b',
            r'\b(?:Add|Remove|Insert|Delete|Create|Destroy|Build|Deploy|Install|Uninstall)\b',
            r'\b(?:Check\s+if|Verify\s+that|Ensure\s+that|Make\s+sure|Confirm\s+that)\b',
            r'\b(?:Run|Execute|Launch|Invoke|Call|Trigger|Initiate|Begin|Commence|Start)\b'
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_verbs = [re.compile(pattern, re.IGNORECASE) for pattern in self.action_verbs]
        
        # Section type patterns for classification
        self.section_patterns = {
            'first_checks': [
                r'first\s+checks?',
                r'quick\s+checks?',
                r'initial\s+checks?',
                r'immediate\s+actions?',
                r'first\s+response',
                r'emergency\s+response',
                r'urgent\s+actions?',
                r'initial\s+response',
                r'first\s+steps?',
                r'immediate\s+steps?',
                r'diagnosis',
                r'investigation'
            ],
            'fix': [
                r'fix(?:es)?',
                r'remediation',
                r'resolution',
                r'solution',
                r'corrective\s+actions?',
                r'repair',
                r'resolve',
                r'correct',
                r'fix\s+steps?',
                r'remediation\s+steps?',
                r'steps\s+to\s+resolve',
                r'how\s+to\s+fix'
            ],
            'validate': [
                r'validate',
                r'verification',
                r'confirm',
                r'check',
                r'test',
                r'verify',
                r'validation\s+steps?',
                r'verification\s+steps?',
                r'confirmation\s+steps?',
                r'post\s+fix\s+checks?',
                r'how\s+to\s+verify',
                r'ensure\s+resolution'
            ]
        }
        
        # Compile section patterns
        self.compiled_sections = {}
        for section_type, patterns in self.section_patterns.items():
            self.compiled_sections[section_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Bullet point patterns
        self.bullet_patterns = [
            r'^\s*[•\-*]\s+(.+)',  # Standard bullet points
            r'^\s*\d+\.\s+(.+)',   # Numbered lists
            r'^\s*[A-Z]\.\s+(.+)', # Lettered lists
            r'^\s*→\s+(.+)',       # Arrow lists
            r'^\s*▶\s+(.+)',       # Triangle lists
            r'^\s*▪\s+(.+)',       # Square lists
        ]
        
        # Compile bullet patterns
        self.compiled_bullets = [re.compile(pattern, re.MULTILINE) for pattern in self.bullet_patterns]
        
    def plan_response(self, chunks: List[Tuple[Any, float]], question: str) -> PlannedResponse:
        """
        Plan a structured response from retrieved chunks
        
        Args:
            chunks: List of (chunk, score) tuples
            question: User question for context
            
        Returns:
            PlannedResponse with organized actionable content
        """
        try:
            logger.info(f"Planning response for question: {question[:100]}...")
            
            # Extract actionable bullets from chunks
            all_bullets = self._extract_actionable_bullets(chunks)
            logger.info(f"Extracted {len(all_bullets)} actionable bullets")
            
            # Classify bullets by section type
            classified_bullets = self._classify_bullets_by_section(all_bullets)
            
            # Build Why explanation
            why_explanation = self._build_why_explanation(chunks, question)
            
            # Organize bullets into sections
            first_checks = self._select_best_bullets(
                classified_bullets.get('first_checks', []), 
                min_count=3, max_count=5
            )
            
            fix_steps = self._select_best_bullets(
                classified_bullets.get('fix', []), 
                min_count=2, max_count=5
            )
            
            validate_steps = self._select_best_bullets(
                classified_bullets.get('validate', []), 
                min_count=2, max_count=4
            )
            
            # Generate sources list
            sources = self._generate_sources_list(chunks)
            
            # Create planned response
            planned_response = PlannedResponse(
                first_checks=first_checks,
                why_explanation=why_explanation,
                fix_steps=fix_steps,
                validate_steps=validate_steps,
                sources=sources,
                has_fix=len(fix_steps) > 0,
                has_validate=len(validate_steps) > 0,
                metadata={
                    'total_bullets': len(all_bullets),
                    'question_type': self._classify_question_type(question),
                    'chunks_analyzed': len(chunks)
                }
            )
            
            logger.info(f"Response planned: {len(first_checks)} checks, {len(fix_steps)} fixes, {len(validate_steps)} validations")
            return planned_response
            
        except Exception as e:
            logger.error(f"Error planning response: {e}")
            return self._create_fallback_response(chunks, question)
    
    def _extract_actionable_bullets(self, chunks: List[Tuple[Any, float]]) -> List[ActionableBullet]:
        """Extract actionable bullets from chunks with provenance tracking"""
        try:
            actionable_bullets = []
            
            for chunk, score in chunks:
                try:
                    # Extract chunk metadata
                    chunk_metadata = self._extract_chunk_metadata(chunk)
                    if not chunk_metadata:
                        continue
                    
                    # Extract content
                    content = chunk_metadata.get('content', '')
                    if not content:
                        continue
                    
                    # Find bullet points in content
                    bullets = self._extract_bullet_points(content)
                    
                    for bullet_content in bullets:
                        # Check if bullet contains actionable verbs
                        if self._is_actionable_bullet(bullet_content):
                            # Extract the main verb
                            verb = self._extract_main_verb(bullet_content)
                            
                            # Create actionable bullet
                            actionable_bullet = ActionableBullet(
                                content=bullet_content.strip(),
                                verb=verb,
                                section_type='unknown',  # Will be classified later
                                source_chunk=chunk,
                                source_file=chunk_metadata.get('filename', 'unknown'),
                                chunk_id=chunk_metadata.get('chunk_id', 'unknown'),
                                confidence=score,
                                metadata={
                                    'content_length': len(bullet_content),
                                    'has_metrics': self._has_metrics(bullet_content),
                                    'has_commands': self._has_commands(bullet_content),
                                    'original_score': score
                                }
                            )
                            
                            actionable_bullets.append(actionable_bullet)
                            
                except Exception as e:
                    logger.warning(f"Error processing chunk: {e}")
                    continue
            
            # Sort by confidence score
            actionable_bullets.sort(key=lambda x: x.confidence, reverse=True)
            
            return actionable_bullets
            
        except Exception as e:
            logger.error(f"Error extracting actionable bullets: {e}")
            return []
    
    def _extract_chunk_metadata(self, chunk) -> Optional[Dict[str, Any]]:
        """Extract metadata from chunk object"""
        try:
            if isinstance(chunk, dict):
                return {
                    'content': chunk.get('content', ''),
                    'filename': chunk.get('filename', ''),
                    'chunk_id': chunk.get('chunk_id', ''),
                    'section_type': chunk.get('section_type', 'unknown'),
                    'metadata': chunk.get('metadata', {})
                }
            elif hasattr(chunk, 'metadata'):
                metadata = chunk.metadata
                if isinstance(metadata, dict):
                    return {
                        'content': getattr(chunk, 'content', ''),
                        'filename': metadata.get('filename', ''),
                        'chunk_id': metadata.get('chunk_id', ''),
                        'section_type': metadata.get('section_type', 'unknown'),
                        'metadata': metadata
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting chunk metadata: {e}")
            return None
    
    def _extract_bullet_points(self, content: str) -> List[str]:
        """Extract bullet points from content"""
        try:
            bullets = []
            
            for pattern in self.compiled_bullets:
                matches = pattern.findall(content)
                bullets.extend(matches)
            
            # Also look for lines that start with action verbs (even without bullets)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and self._is_actionable_bullet(line):
                    bullets.append(line)
            
            return bullets
            
        except Exception as e:
            logger.error(f"Error extracting bullet points: {e}")
            return []
    
    def _is_actionable_bullet(self, text: str) -> bool:
        """Check if text contains actionable content"""
        try:
            # Check for imperative verbs
            for pattern in self.compiled_verbs:
                if pattern.search(text):
                    return True
            
            # Check for command-like patterns
            command_patterns = [
                r'`[^`]+`',  # Inline code
                r'```[\s\S]*?```',  # Code blocks
                r'\b(?:ssh|curl|wget|git|docker|kubectl|helm|terraform|ansible|make|npm|yarn|pip|apt|yum|brew)\b'
            ]
            
            for pattern in command_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if bullet is actionable: {e}")
            return False
    
    def _extract_main_verb(self, text: str) -> str:
        """Extract the main action verb from text"""
        try:
            # Find the first imperative verb
            for pattern in self.compiled_verbs:
                match = pattern.search(text)
                if match:
                    return match.group(0).lower()
            
            # Fallback: look for common action words
            fallback_verbs = ['check', 'verify', 'review', 'set', 'increase', 'scale', 'restart']
            text_lower = text.lower()
            
            for verb in fallback_verbs:
                if verb in text_lower:
                    return verb
            
            return 'action'
            
        except Exception as e:
            logger.error(f"Error extracting main verb: {e}")
            return 'action'
    
    def _has_metrics(self, text: str) -> bool:
        """Check if text contains metrics or measurements"""
        try:
            metric_patterns = [
                r'\b\d+(?:\.\d+)?\s*(?:ms|s|min|hour|day|%|MB|GB|TB|KB|bps|req/s|ops/s)\b',
                r'\b(?:high|low|medium|critical|warning|error|success|failure)\b',
                r'\b(?:threshold|limit|quota|rate|latency|throughput|availability|uptime)\b'
            ]
            
            for pattern in metric_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for metrics: {e}")
            return False
    
    def _has_commands(self, text: str) -> bool:
        """Check if text contains command examples"""
        try:
            command_patterns = [
                r'`[^`]*\b(?:ssh|curl|wget|git|docker|kubectl|helm|terraform|ansible|make|npm|yarn|pip|apt|yum|brew)\b[^`]*`',
                r'```[\s\S]*?\b(?:ssh|curl|wget|git|docker|kubectl|helm|terraform|ansible|make|npm|yarn|pip|apt|yum|brew)\b[\s\S]*?```'
            ]
            
            for pattern in command_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for commands: {e}")
            return False
    
    def _classify_bullets_by_section(self, bullets: List[ActionableBullet]) -> Dict[str, List[ActionableBullet]]:
        """Classify bullets by their intended section type"""
        try:
            classified = {
                'first_checks': [],
                'fix': [],
                'validate': []
            }
            
            for bullet in bullets:
                # Try to classify based on source chunk section type
                source_metadata = getattr(bullet.source_chunk, 'metadata', {})
                if isinstance(source_metadata, dict):
                    chunk_section_type = source_metadata.get('section_type', 'unknown')
                    if chunk_section_type in classified:
                        classified[chunk_section_type].append(bullet)
                        continue
                
                # Try to classify based on content analysis
                content_lower = bullet.content.lower()
                
                # Check for section-specific keywords
                if any(word in content_lower for word in ['check', 'verify', 'review', 'monitor', 'diagnose']):
                    classified['first_checks'].append(bullet)
                elif any(word in content_lower for word in ['fix', 'resolve', 'restart', 'restore', 'clear']):
                    classified['fix'].append(bullet)
                elif any(word in content_lower for word in ['validate', 'confirm', 'test', 'ensure', 'verify']):
                    classified['validate'].append(bullet)
                else:
                    # Default to first_checks for actionable content
                    classified['first_checks'].append(bullet)
            
            return classified
            
        except Exception as e:
            logger.error(f"Error classifying bullets by section: {e}")
            return {'first_checks': bullets, 'fix': [], 'validate': []}
    
    def _select_best_bullets(self, bullets: List[ActionableBullet], min_count: int, max_count: int) -> List[ActionableBullet]:
        """Select the best bullets for a section based on confidence and quality"""
        try:
            if len(bullets) <= max_count:
                return bullets
            
            # Sort by confidence and quality metrics
            scored_bullets = []
            for bullet in bullets:
                score = bullet.confidence
                
                # Bonus for commands and metrics
                if bullet.metadata.get('has_commands', False):
                    score += 0.1
                if bullet.metadata.get('has_metrics', False):
                    score += 0.1
                
                # Bonus for longer, more detailed content
                if bullet.metadata.get('content_length', 0) > 50:
                    score += 0.05
                
                scored_bullets.append((bullet, score))
            
            # Sort by final score
            scored_bullets.sort(key=lambda x: x[1], reverse=True)
            
            # Select top bullets
            selected_bullets = [bullet for bullet, _ in scored_bullets[:max_count]]
            
            # Ensure minimum count if possible
            if len(selected_bullets) < min_count and len(bullets) >= min_count:
                # Add more bullets to meet minimum
                remaining = [bullet for bullet, _ in scored_bullets[max_count:]]
                selected_bullets.extend(remaining[:min_count - len(selected_bullets)])
            
            return selected_bullets
            
        except Exception as e:
            logger.error(f"Error selecting best bullets: {e}")
            return bullets[:max_count] if bullets else []
    
    def _build_why_explanation(self, chunks: List[Tuple[Any, float]], question: str) -> str:
        """Build a concise Why explanation from evidence and policy chunks"""
        try:
            # Extract content from chunks
            chunk_contents = []
            for chunk, score in chunks:
                metadata = self._extract_chunk_metadata(chunk)
                if metadata and metadata.get('content'):
                    chunk_contents.append({
                        'content': metadata['content'],
                        'score': score,
                        'section_type': metadata.get('section_type', 'unknown')
                    })
            
            if not chunk_contents:
                return "Based on the available information in the knowledge base."
            
            # Sort by relevance score
            chunk_contents.sort(key=lambda x: x['score'], reverse=True)
            
            # Build explanation from top chunks
            explanation_parts = []
            
            for chunk_info in chunk_contents[:3]:  # Use top 3 chunks
                content = chunk_info['content']
                section_type = chunk_info['section_type']
                
                # Extract relevant sentences
                sentences = self._extract_relevant_sentences(content, question)
                
                if sentences:
                    # Add context based on section type
                    if section_type == 'policy':
                        explanation_parts.append(f"According to policy: {sentences[0]}")
                    elif section_type == 'background':
                        explanation_parts.append(sentences[0])
                    else:
                        explanation_parts.append(sentences[0])
            
            if explanation_parts:
                # Combine explanations
                explanation = " ".join(explanation_parts)
                
                # Clean up and ensure it ends properly
                if not explanation.endswith(('.', '!', '?')):
                    explanation += "."
                
                return explanation
            
            return "Based on the available information in the knowledge base."
            
        except Exception as e:
            logger.error(f"Error building why explanation: {e}")
            return "Based on the available information in the knowledge base."
    
    def _extract_relevant_sentences(self, content: str, question: str) -> List[str]:
        """Extract relevant sentences from content based on question"""
        try:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            # Score sentences based on relevance to question
            scored_sentences = []
            question_words = set(re.findall(r'\b\w+\b', question.lower()))
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                
                # Calculate relevance score
                sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
                common_words = question_words.intersection(sentence_words)
                relevance_score = len(common_words) / max(len(question_words), 1)
                
                if relevance_score > 0.1:  # Minimum relevance threshold
                    scored_sentences.append((sentence, relevance_score))
            
            # Sort by relevance and return top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            return [sentence for sentence, _ in scored_sentences[:2]]
            
        except Exception as e:
            logger.error(f"Error extracting relevant sentences: {e}")
            return []
    
    def _generate_sources_list(self, chunks: List[Tuple[Any, float]]) -> List[str]:
        """Generate a cleaned global sources list"""
        try:
            sources = set()
            
            for chunk, _ in chunks:
                metadata = self._extract_chunk_metadata(chunk)
                if metadata and metadata.get('filename'):
                    filename = metadata['filename']
                    # Clean filename (remove extension, normalize)
                    clean_filename = self._clean_filename(filename)
                    if clean_filename:
                        sources.add(clean_filename)
            
            # Convert to sorted list
            return sorted(list(sources))
            
        except Exception as e:
            logger.error(f"Error generating sources list: {e}")
            return []
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename for display"""
        try:
            # Remove file extension
            clean_name = re.sub(r'\.(md|txt|pdf)$', '', filename, flags=re.IGNORECASE)
            
            # Replace underscores and hyphens with spaces
            clean_name = re.sub(r'[_-]', ' ', clean_name)
            
            # Title case
            clean_name = clean_name.title()
            
            return clean_name
            
        except Exception as e:
            logger.error(f"Error cleaning filename: {e}")
            return filename
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question to determine response structure"""
        try:
            question_lower = question.lower()
            
            # Check for specific question types
            if any(word in question_lower for word in ['cpu', 'memory', 'performance', 'alert', 'spike']):
                return 'performance_alert'
            elif any(word in question_lower for word in ['database', 'pool', 'connection', 'timeout']):
                return 'database_issue'
            elif any(word in question_lower for word in ['cache', 'redis', 'hit rate', 'miss']):
                return 'cache_issue'
            elif any(word in question_lower for word in ['queue', 'backlog', 'processing']):
                return 'queue_issue'
            else:
                return 'general_issue'
                
        except Exception as e:
            logger.error(f"Error classifying question type: {e}")
            return 'general_issue'
    
    def _create_fallback_response(self, chunks: List[Tuple[Any, float]], question: str) -> PlannedResponse:
        """Create a fallback response when planning fails"""
        try:
            # Extract basic information
            sources = self._generate_sources_list(chunks)
            
            return PlannedResponse(
                first_checks=[],
                why_explanation="Based on the available information in the knowledge base.",
                fix_steps=[],
                validate_steps=[],
                sources=sources,
                has_fix=False,
                has_validate=False,
                metadata={
                    'total_bullets': 0,
                    'question_type': 'unknown',
                    'chunks_analyzed': len(chunks),
                    'fallback': True
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating fallback response: {e}")
            return PlannedResponse(
                first_checks=[],
                why_explanation="Unable to process the question at this time.",
                fix_steps=[],
                validate_steps=[],
                sources=[],
                has_fix=False,
                has_validate=False,
                metadata={'error': str(e)}
            )
    
    def get_planning_stats(self, planned_response: PlannedResponse) -> Dict[str, Any]:
        """Get statistics about the planned response"""
        try:
            return {
                "total_bullets": len(planned_response.first_checks) + 
                               len(planned_response.fix_steps) + 
                               len(planned_response.validate_steps),
                "first_checks_count": len(planned_response.first_checks),
                "fix_steps_count": len(planned_response.fix_steps),
                "validate_steps_count": len(planned_response.validate_steps),
                "sources_count": len(planned_response.sources),
                "has_fix": planned_response.has_fix,
                "has_validate": planned_response.has_validate,
                "question_type": planned_response.metadata.get('question_type', 'unknown'),
                "chunks_analyzed": planned_response.metadata.get('chunks_analyzed', 0)
            }
        except Exception as e:
            logger.error(f"Error getting planning stats: {e}")
            return {"error": str(e)}

