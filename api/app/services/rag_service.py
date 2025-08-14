import os
import logging
import uuid
from typing import List, Dict, Any, Tuple
import re

from .embedding_service import EmbeddingService
from .faiss_service import FAISSService
from .diagnostics_service import DiagnosticsService
from .anti_generic_gate import AntiGenericGate
from .retrieval import RetrievalPipeline
from .planner import Planner
from ..models.document import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval-Augmented Generation with anti-generic gate enforcement, diverse retrieval, and intelligent planning"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.faiss_service = FAISSService()
        self.diagnostics_service = DiagnosticsService()
        self.anti_generic_gate = AntiGenericGate()
        self.retrieval_pipeline = RetrievalPipeline()
        self.planner = Planner()
        self.top_k = int(os.getenv("RAG_TOP_K", "7"))  # Default to 7 chunks
        
    def ask_question(self, question: str, context: str = "") -> Dict[str, Any]:
        """Ask a question and return a structured answer with planning and anti-generic gate enforcement"""
        try:
            trace_id = str(uuid.uuid4())
            logger.info(f"Processing question with trace_id: {trace_id}")
            
            # Use diverse retrieval pipeline instead of simple FAISS search
            search_results = self.retrieval_pipeline.retrieve_diverse_results(
                question, self.faiss_service, top_k=8
            )
            
            if not search_results:
                # Fallback to keyword search
                search_results = self._keyword_search(question)
                if not search_results:
                    return self._create_error_response("No relevant information found", trace_id)
            
            # Plan the response using the planner
            planned_response = self.planner.plan_response(search_results, question)
            logger.info(f"Response planned: {planned_response.metadata}")
            
            # Run diagnostics if appropriate
            diagnostics_results = self.diagnostics_service.run_diagnostics(question)
            
            # Compose answer using the planned response
            answer = self._compose_answer_from_plan(question, planned_response, diagnostics_results)
            
            # Clean the answer to remove any system/prompt text
            cleaned_answer = self._clean_answer(answer)
            
            # Generate final citations from planned response
            final_citations = self._generate_citations_from_plan(planned_response)
            
            # Calculate confidence
            confidence = self._calculate_confidence_from_plan(planned_response)
            
            # Enforce anti-generic gate
            passes_gate, final_answer, quality_report = self.anti_generic_gate.enforce_gate(
                cleaned_answer, final_citations, diagnostics_results
            )
            
            # Temporarily bypass anti-generic gate for debugging
            # passes_gate = True
            # final_answer = cleaned_answer
            # quality_report = {"quality_score": 1, "issues": [], "metrics": {}}
            
            # Get retrieval and planning statistics
            retrieval_stats = self.retrieval_pipeline.get_retrieval_stats(search_results)
            planning_stats = self.planner.get_planning_stats(planned_response)
            
            # Log quality check results
            logger.info(f"Anti-generic gate check - Passes: {passes_gate}, Score: {quality_report.get('quality_score', 'N/A')}")
            if not passes_gate:
                logger.warning(f"Answer rejected by anti-generic gate: {quality_report.get('issues', [])}")
            
            return {
                "answer": final_answer,
                "citations": final_citations if passes_gate else [],
                "trace_id": trace_id,
                "retrieved_chunks": len(search_results),
                "confidence": confidence if passes_gate else 0.0,
                "diagnostics": diagnostics_results if passes_gate else None,
                "quality_gate": {
                    "passed": passes_gate,
                    "score": quality_report.get("quality_score", 0),
                    "issues": quality_report.get("issues", []),
                    "metrics": quality_report.get("metrics", {})
                },
                "retrieval_stats": retrieval_stats,
                "planning_stats": planning_stats
            }
            
        except Exception as e:
            logger.error(f"Error in RAG service: {e}")
            return self._create_error_response(f"Error processing question: {str(e)}", str(uuid.uuid4()))
    
    def _create_error_response(self, error_message: str, trace_id: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "answer": f"Sorry, I encountered an error: {error_message}",
            "citations": [],
            "trace_id": trace_id,
            "retrieved_chunks": 0,
            "confidence": 0.0,
            "diagnostics": None,
            "quality_gate": {
                "passed": False,
                "score": -1,
                "issues": [error_message],
                "metrics": {}
            }
        }
    
    def _keyword_search(self, question: str) -> List[Tuple[Any, float]]:
        """Fallback keyword search when embedding search fails"""
        try:
            # Extract key terms from the question
            question_lower = question.lower()
            
            # Define keyword categories
            cpu_keywords = ['cpu', 'processor', 'usage', 'high', 'spike', 'load']
            memory_keywords = ['memory', 'ram', 'usage', 'high', 'leak', 'swap']
            disk_keywords = ['disk', 'storage', 'space', 'usage', 'full', 'io']
            alert_keywords = ['alert', 'alarm', 'warning', 'critical', 'incident']
            command_keywords = ['command', 'script', 'tool', 'utility', 'check']
            
            # Check which category the question belongs to
            if any(keyword in question_lower for keyword in cpu_keywords):
                search_terms = ['cpu', 'processor', 'load', 'performance']
            elif any(keyword in question_lower for keyword in memory_keywords):
                search_terms = ['memory', 'ram', 'swap', 'leak']
            elif any(keyword in question_lower for keyword in disk_keywords):
                search_terms = ['disk', 'storage', 'space', 'io']
            elif any(keyword in question_lower for keyword in alert_keywords):
                search_terms = ['alert', 'alarm', 'incident', 'response']
            elif any(keyword in question_lower for keyword in command_keywords):
                search_terms = ['command', 'script', 'tool', 'check']
            else:
                search_terms = ['troubleshoot', 'investigate', 'check', 'verify']
            
            # Search for chunks containing these terms
            all_chunks = self.faiss_service.metadata
            relevant_chunks = []
            
            for chunk in all_chunks:
                chunk_content = chunk.content.lower()
                relevance_score = 0
                
                for term in search_terms:
                    if term in chunk_content:
                        relevance_score += 1
                
                if relevance_score > 0:
                    # Normalize score
                    normalized_score = min(relevance_score / len(search_terms), 0.8)
                    relevant_chunks.append((chunk, normalized_score))
            
            # Sort by relevance and return top results
            relevant_chunks.sort(key=lambda x: x[1], reverse=True)
            return relevant_chunks[:6]
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _clean_citations(self, search_results: List[Tuple[Any, float]]) -> List[Tuple[Any, float]]:
        """Clean and normalize citations"""
        try:
            cleaned_results = []
            seen_citations = set()
            
            for chunk, score in search_results:
                # Extract filename from chunk metadata
                filename = chunk.metadata.get('filename', 'unknown')
                
                # Normalize filename
                normalized_filename = self._normalize_filename(filename)
                
                # Skip obvious meta files
                if normalized_filename.lower() in ['readme', 'license', 'changelog', 'contributing']:
                    continue
                
                # Create citation key
                citation_key = f"{normalized_filename}#{chunk.id}"
                
                # Skip duplicates
                if citation_key in seen_citations:
                    continue
                
                seen_citations.add(citation_key)
                cleaned_results.append((chunk, score))
            
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Error cleaning citations: {e}")
            return search_results
    
    def _normalize_filename(self, filename: str) -> str:
        """Normalize filename by removing common prefixes and extensions"""
        try:
            # Remove file extensions
            name = re.sub(r'\.(md|txt|pdf)$', '', filename, flags=re.IGNORECASE)
            
            # Remove common prefixes
            prefixes = [
                'runbook-', 'docs-', 'guide-', 'manual-', 'cheatsheet-',
                'policy-', 'procedure-', 'playbook-', 'sop-', 'kb-'
            ]
            
            for prefix in prefixes:
                if name.lower().startswith(prefix.lower()):
                    name = name[len(prefix):]
                    break
            
            return name.strip()
            
        except Exception as e:
            logger.error(f"Error normalizing filename: {e}")
            return filename
    
    def _clean_answer(self, answer: str) -> str:
        """Remove common system/prompt prefixes from the answer"""
        try:
            # Common prefixes to remove
            prefixes_to_remove = [
                r'^System:\s*',
                r'^Question:\s*',
                r'^Context:\s*',
                r'^Based on the provided information:\s*',
                r'^According to the retrieved context:\s*',
                r'^Based on the available information:\s*',
                r'^From the retrieved documentation:\s*',
                r'^Based on what was found:\s*',
                r'^According to the context:\s*'
            ]
            
            cleaned_answer = answer
            for pattern in prefixes_to_remove:
                cleaned_answer = re.sub(pattern, '', cleaned_answer, flags=re.IGNORECASE)
            
            return cleaned_answer.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning answer: {e}")
            return answer
    
    def _generate_final_citations(self, cleaned_results: List[Tuple[Any, float]]) -> List[str]:
        """Generate final citation list"""
        try:
            citations = []
            for chunk, score in cleaned_results:
                filename = chunk.metadata.get('filename', 'unknown')
                normalized_filename = self._normalize_filename(filename)
                citation = f"{normalized_filename}#{chunk.id}"
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Error generating final citations: {e}")
            return []
    
    def _compose_answer(self, question: str, search_results: List[Tuple[Any, float]], diagnostics_results: Dict[str, Any]) -> str:
        """Compose a structured answer from search results and diagnostics"""
        try:
            if not search_results:
                return "I couldn't find enough relevant information to provide a specific answer."
            
            # Extract content from search results
            chunks_content = []
            for chunk, score in search_results:
                content = chunk.content.strip()
                if content:
                    chunks_content.append(content)
            
            # Analyze the question type and compose appropriate response
            question_lower = question.lower()
            
            # Determine response structure based on question content
            if any(term in question_lower for term in ['cpu', 'memory', 'disk', 'performance', 'alert']):
                response_structure = "performance"
            elif any(term in question_lower for term in ['error', 'failure', 'broken', 'down']):
                response_structure = "incident"
            elif any(term in question_lower for term in ['how', 'what', 'steps', 'procedure']):
                response_structure = "procedure"
            else:
                response_structure = "general"
            
            # Compose the answer based on structure
            if response_structure == "performance":
                answer = self._compose_performance_response(chunks_content, diagnostics_results)
            elif response_structure == "incident":
                answer = self._compose_incident_response(chunks_content, diagnostics_results)
            elif response_structure == "procedure":
                answer = self._compose_procedure_response(chunks_content, diagnostics_results)
            else:
                answer = self._compose_general_response(chunks_content, diagnostics_results)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error composing answer: {e}")
            return "I encountered an error while composing the answer. Please try again."
    
    def _compose_answer_from_plan(self, question: str, planned_response, diagnostics_results: Dict[str, Any]) -> str:
        """Compose a structured answer from a planned response and diagnostics"""
        try:
            # Build the answer using the planned response structure
            answer_parts = []
            
            # First checks section
            if planned_response.first_checks:
                answer_parts.append("**First checks:**")
                for bullet in planned_response.first_checks:
                    answer_parts.append(f"• {bullet.content}")
                answer_parts.append("")
            
            # Why explanation
            if planned_response.why_explanation:
                answer_parts.append("**Why:**")
                answer_parts.append(planned_response.why_explanation)
                answer_parts.append("")
            
            # Fix steps (only if present)
            if planned_response.has_fix and planned_response.fix_steps:
                answer_parts.append("**Fix:**")
                for bullet in planned_response.fix_steps:
                    answer_parts.append(f"• {bullet.content}")
                answer_parts.append("")
            
            # Validate steps (only if present)
            if planned_response.has_validate and planned_response.validate_steps:
                answer_parts.append("**Validate:**")
                for bullet in planned_response.validate_steps:
                    answer_parts.append(f"• {bullet.content}")
                answer_parts.append("")
            
            # Diagnostics (only if tools ran)
            if diagnostics_results and any(diagnostics_results.values()):
                answer_parts.append("**Diagnostics:**")
                diagnostics_text = self._format_diagnostics_block(diagnostics_results)
                # Join diagnostics lines into a single string
                if isinstance(diagnostics_text, list):
                    diagnostics_text = "\n".join(diagnostics_text)
                answer_parts.append(diagnostics_text)
                answer_parts.append("")
            
            # Sources
            if planned_response.sources:
                answer_parts.append("**Sources:**")
                for source in planned_response.sources:
                    answer_parts.append(f"• {source}")
            
            # Ensure all parts are strings
            answer_parts = [str(part) for part in answer_parts]
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error composing answer from plan: {e}")
            return "I encountered an error while composing the answer. Please try again."
    
    def _compose_performance_response(self, chunks_content: List[str], diagnostics_results: Dict[str, Any]) -> str:
        """Compose a performance-related response"""
        try:
            answer_parts = []
            
            # First checks section
            first_checks = self._extract_first_checks(chunks_content)
            if first_checks:
                answer_parts.append("**First checks:**")
                for check in first_checks:
                    answer_parts.append(f"• {check}")
                answer_parts.append("")
            
            # Why this happens section
            why_section = self._extract_why_section(chunks_content)
            if why_section:
                answer_parts.append("**Why this happens:**")
                for reason in why_section:
                    answer_parts.append(f"• {reason}")
                answer_parts.append("")
            
            # Diagnostics section (if tools ran)
            if diagnostics_results and any(diagnostics_results.values()):
                diagnostics_block = self._format_diagnostics_block(diagnostics_results)
                if diagnostics_block:
                    answer_parts.append("**Diagnostics if tools ran:**")
                    # Join diagnostics lines into a single string
                    if isinstance(diagnostics_block, list):
                        diagnostics_block = "\n".join(diagnostics_block)
                    answer_parts.append(diagnostics_block)
                    answer_parts.append("")
            
            # Sources section
            answer_parts.append("**Sources:** See citations below.")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error composing performance response: {e}")
            return "Error composing performance response."
    
    def _compose_incident_response(self, chunks_content: List[str], diagnostics_results: Dict[str, Any]) -> str:
        """Compose an incident-related response"""
        try:
            answer_parts = []
            
            # First response section
            first_response = self._extract_first_response(chunks_content)
            if first_response:
                answer_parts.append("**First response:**")
                for step in first_response:
                    answer_parts.append(f"• {step}")
                answer_parts.append("")
            
            # Investigation section
            investigation = self._extract_investigation(chunks_content)
            if investigation:
                answer_parts.append("**Investigation:**")
                for step in investigation:
                    answer_parts.append(f"• {step}")
                answer_parts.append("")
            
            # Diagnostics section (if tools ran)
            if diagnostics_results and any(diagnostics_results.values()):
                diagnostics_block = self._format_diagnostics_block(diagnostics_results)
                if diagnostics_block:
                    answer_parts.append("**Diagnostics if tools ran:**")
                    # Join diagnostics lines into a single string
                    if isinstance(diagnostics_block, list):
                        diagnostics_block = "\n".join(diagnostics_block)
                    answer_parts.append(diagnostics_block)
                    answer_parts.append("")
            
            # Sources section
            answer_parts.append("**Sources:** See citations below.")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error composing incident response: {e}")
            return "Error composing incident response."
    
    def _compose_procedure_response(self, chunks_content: List[str], diagnostics_results: Dict[str, Any]) -> str:
        """Compose a procedure-related response"""
        try:
            answer_parts = []
            
            # Steps section
            steps = self._extract_steps(chunks_content)
            if steps:
                answer_parts.append("**Steps:**")
                for i, step in enumerate(steps, 1):
                    answer_parts.append(f"{i}. {step}")
                answer_parts.append("")
            
            # Prerequisites section
            prerequisites = self._extract_prerequisites(chunks_content)
            if prerequisites:
                answer_parts.append("**Prerequisites:**")
                for prereq in prerequisites:
                    answer_parts.append(f"• {prereq}")
                answer_parts.append("")
            
            # Diagnostics section (if tools ran)
            if diagnostics_results and any(diagnostics_results.values()):
                diagnostics_block = self._format_diagnostics_block(diagnostics_results)
                if diagnostics_block:
                    answer_parts.append("**Diagnostics if tools ran:**")
                    # Join diagnostics lines into a single string
                    if isinstance(diagnostics_block, list):
                        diagnostics_block = "\n".join(diagnostics_block)
                    answer_parts.append(diagnostics_block)
                    answer_parts.append("")
            
            # Sources section
            answer_parts.append("**Sources:** See citations below.")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error composing procedure response: {e}")
            return "Error composing procedure response."
    
    def _compose_general_response(self, chunks_content: List[str], diagnostics_results: Dict[str, Any]) -> str:
        """Compose a general response"""
        try:
            answer_parts = []
            
            # Key points section
            key_points = self._extract_key_points(chunks_content)
            if key_points:
                answer_parts.append("**Key points:**")
                for point in key_points:
                    answer_parts.append(f"• {point}")
                answer_parts.append("")
            
            # Details section
            details = self._extract_details(chunks_content)
            if details:
                answer_parts.append("**Details:**")
                for detail in details:
                    answer_parts.append(f"• {detail}")
                answer_parts.append("")
            
            # Diagnostics section (if tools ran)
            if diagnostics_results and any(diagnostics_results.values()):
                diagnostics_block = self._format_diagnostics_block(diagnostics_results)
                if diagnostics_block:
                    answer_parts.append("**Diagnostics if tools ran:**")
                    # Join diagnostics lines into a single string
                    if isinstance(diagnostics_block, list):
                        diagnostics_block = "\n".join(diagnostics_block)
                    answer_parts.append(diagnostics_block)
                    answer_parts.append("")
            
            # Sources section
            answer_parts.append("**Sources:** See citations below.")
            
            return "\n".join(answer_parts)
            
        except Exception as e:
            logger.error(f"Error composing general response: {e}")
            return "Error composing general response."
    
    def _extract_first_checks(self, chunks_content: List[str]) -> List[str]:
        """Extract first check steps from chunks"""
        checks = []
        for content in chunks_content:
            # Look for check-related content
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['check', 'verify', 'confirm', 'ensure', 'look for']):
                    # Clean up the line
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        checks.append(clean_line)
                        if len(checks) >= 5:  # Limit to 5 checks
                            break
            if len(checks) >= 5:
                break
        return checks[:5]
    
    def _extract_why_section(self, chunks_content: List[str]) -> List[str]:
        """Extract why this happens reasons from chunks"""
        reasons = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['because', 'due to', 'caused by', 'reason', 'issue', 'problem']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        reasons.append(clean_line)
                        if len(reasons) >= 3:  # Limit to 3 reasons
                            break
            if len(reasons) >= 3:
                break
        return reasons[:3]
    
    def _extract_first_response(self, chunks_content: List[str]) -> List[str]:
        """Extract first response steps from chunks"""
        steps = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['first', 'immediate', 'urgent', 'emergency', 'response']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        steps.append(clean_line)
                        if len(steps) >= 4:  # Limit to 4 steps
                            break
            if len(steps) >= 4:
                break
        return steps[:4]
    
    def _extract_investigation(self, chunks_content: List[str]) -> List[str]:
        """Extract investigation steps from chunks"""
        steps = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['investigate', 'examine', 'analyze', 'review', 'check', 'verify']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        steps.append(clean_line)
                        if len(steps) >= 4:  # Limit to 4 steps
                            break
            if len(steps) >= 4:
                break
        return steps[:4]
    
    def _extract_steps(self, chunks_content: List[str]) -> List[str]:
        """Extract procedure steps from chunks"""
        steps = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['step', 'procedure', 'process', 'method', 'approach']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        steps.append(clean_line)
                        if len(steps) >= 6:  # Limit to 6 steps
                            break
            if len(steps) >= 6:
                break
        return steps[:6]
    
    def _extract_prerequisites(self, chunks_content: List[str]) -> List[str]:
        """Extract prerequisites from chunks"""
        prereqs = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['prerequisite', 'requirement', 'need', 'before', 'ensure']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        prereqs.append(clean_line)
                        if len(prereqs) >= 3:  # Limit to 3 prereqs
                            break
            if len(prereqs) >= 3:
                break
        return prereqs[:3]
    
    def _extract_key_points(self, chunks_content: List[str]) -> List[str]:
        """Extract key points from chunks"""
        points = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and any(keyword in line.lower() for keyword in ['key', 'important', 'critical', 'essential', 'main', 'primary']):
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 10:
                        points.append(clean_line)
                        if len(points) >= 4:  # Limit to 4 points
                            break
            if len(points) >= 4:
                break
        return points[:4]
    
    def _extract_details(self, chunks_content: List[str]) -> List[str]:
        """Extract details from chunks"""
        details = []
        for content in chunks_content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 20:  # Look for substantial content
                    clean_line = re.sub(r'^[•\-*]\s*', '', line)
                    if clean_line and len(clean_line) > 20:
                        details.append(clean_line)
                        if len(details) >= 3:  # Limit to 3 details
                            break
            if len(details) >= 3:
                break
        return details[:3]
    
    def _format_diagnostics_block(self, diagnostics_results: Dict[str, Any]) -> List[str]:
        """Format diagnostics results into readable bullet points"""
        try:
            formatted_lines = []
            
            # Format logs if present
            if 'logs' in diagnostics_results and diagnostics_results['logs']:
                for service, log_data in diagnostics_results['logs'].items():
                    if log_data.get('success') and log_data.get('recent_entries'):
                        entries = log_data['recent_entries']
                        if len(entries) > 0:
                            formatted_lines.append(f"• {service} logs: {len(entries)} recent entries")
                        else:
                            formatted_lines.append(f"• {service} logs: No recent entries found")
                    else:
                        formatted_lines.append(f"• {service} logs: {log_data.get('message', 'Not available')}")
            
            # Format queues if present
            if 'queues' in diagnostics_results and diagnostics_results['queues']:
                for queue_name, queue_data in diagnostics_results['queues'].items():
                    if queue_data.get('success'):
                        depth = queue_data.get('depth', 'unknown')
                        status = queue_data.get('status', 'unknown')
                        formatted_lines.append(f"• {queue_name} queue: {depth} items ({status})")
                    else:
                        formatted_lines.append(f"• {queue_name} queue: {queue_data.get('message', 'Not available')}")
            
            # Format other diagnostic results
            for key, value in diagnostics_results.items():
                if key not in ['logs', 'queues'] and value:
                    if isinstance(value, dict):
                        if value.get('success'):
                            formatted_lines.append(f"• {key}: {value.get('message', 'Available')}")
                        else:
                            formatted_lines.append(f"• {key}: {value.get('message', 'Not available')}")
                    else:
                        formatted_lines.append(f"• {key}: {value}")
            
            return formatted_lines
            
        except Exception as e:
            logger.error(f"Error formatting diagnostics block: {e}")
            return ["• Diagnostics information available"]
    
    def _calculate_confidence(self, search_results: List[Tuple[Any, float]]) -> float:
        """Calculate confidence score based on search results"""
        try:
            if not search_results:
                return 0.0
            
            # Calculate average similarity score
            scores = [score for _, score in search_results]
            avg_score = sum(scores) / len(scores)
            
            # Boost confidence based on number of results
            result_boost = min(len(search_results) / 8.0, 0.2)  # Max 0.2 boost for 8+ results
            
            # Final confidence score
            confidence = min(avg_score + result_boost, 1.0)
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _calculate_confidence_from_plan(self, planned_response) -> float:
        """Calculate confidence score based on the planned response"""
        try:
            total_bullets = (len(planned_response.first_checks) + 
                           len(planned_response.fix_steps) + 
                           len(planned_response.validate_steps))
            
            if total_bullets == 0:
                return 0.0
            
            # Base confidence from bullet count
            base_confidence = min(total_bullets / 10.0, 1.0)
            
            # Bonus for having fix and validate steps
            if planned_response.has_fix:
                base_confidence += 0.1
            if planned_response.has_validate:
                base_confidence += 0.1
            
            # Bonus for multiple sources
            sources_count = len(planned_response.sources)
            if sources_count > 1:
                base_confidence += min(sources_count * 0.05, 0.2)
            
            # Ensure confidence is within bounds
            confidence = max(0.0, min(base_confidence, 1.0))
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence from plan: {e}")
            return 0.0
    
    def _generate_citations_from_plan(self, planned_response) -> List[str]:
        """Generate final citation list from the planned response"""
        try:
            citations = []
            
            # Collect citations from all bullets
            all_bullets = (planned_response.first_checks + 
                          planned_response.fix_steps + 
                          planned_response.validate_steps)
            
            for bullet in all_bullets:
                # Handle cases where chunk_id might be empty
                if bullet.chunk_id and bullet.chunk_id.strip():
                    citation = f"{bullet.source_file}#{bullet.chunk_id}"
                else:
                    citation = bullet.source_file
                
                if citation not in citations:
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Error generating citations from plan: {e}")
            return []
