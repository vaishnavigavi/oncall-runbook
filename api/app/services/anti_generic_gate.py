import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class AntiGenericGate:
    """Service to enforce answer quality standards and prevent generic responses"""
    
    def __init__(self):
        # Banned generic phrases that indicate poor answer quality
        self.banned_phrases = [
            r"check\s+the\s+relevant\s+documentation",
            r"refer\s+to\s+the\s+retrieved\s+documentation",
            r"based\s+on\s+the\s+retrieved\s+context",
            r"consult\s+the\s+docs",
            r"check\s+the\s+documentation",
            r"refer\s+to\s+documentation",
            r"see\s+the\s+documentation",
            r"review\s+the\s+documentation",
            r"look\s+at\s+the\s+documentation",
            r"examine\s+the\s+documentation",
            r"consult\s+relevant\s+docs",
            r"check\s+appropriate\s+documentation",
            r"refer\s+to\s+appropriate\s+docs",
            r"based\s+on\s+available\s+information",
            r"according\s+to\s+the\s+context",
            r"as\s+per\s+the\s+retrieved\s+information",
            r"from\s+the\s+provided\s+context",
            r"based\s+on\s+what\s+was\s+found",
            r"according\s+to\s+what\s+was\s+retrieved",
            r"based\s+on\s+the\s+available\s+context"
        ]
        
        # Compile regex patterns for efficiency
        self.banned_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.banned_phrases]
        
        # Minimum actionable content requirements
        self.min_actionable_bullets = 3  # Restored from 1
        self.min_distinct_files = 2      # Restored from 1
        self.min_evidence_threshold = 2  # Restored from 1
        
    def check_answer_quality(self, answer: str, citations: List[str], diagnostics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check if an answer meets quality standards
        
        Returns:
            Dict with 'passes_gate', 'quality_score', 'issues', 'missing_context'
        """
        try:
            issues = []
            quality_score = 0
            
            # Check 1: Banned generic phrases
            generic_phrases_found = self._check_banned_phrases(answer)
            if generic_phrases_found:
                issues.append(f"Contains generic phrases: {', '.join(generic_phrases_found)}")
                quality_score -= 2
            
            # Check 2: Actionability minimum
            actionable_bullets = self._count_actionable_bullets(answer)
            if actionable_bullets < self.min_actionable_bullets:
                issues.append(f"Insufficient actionable content: {actionable_bullets}/{self.min_actionable_bullets} bullets required")
                quality_score -= 1
            
            # Check 3: Evidence threshold
            evidence_score = self._calculate_evidence_score(citations, diagnostics)
            if evidence_score < self.min_evidence_threshold:
                issues.append(f"Insufficient evidence: {evidence_score}/{self.min_evidence_threshold} required")
                quality_score -= 1
            
            # Check 4: Distinct file coverage
            distinct_files = self._count_distinct_files(citations)
            if distinct_files < self.min_distinct_files:
                issues.append(f"Insufficient file coverage: {distinct_files}/{self.min_distinct_files} distinct files required")
                quality_score -= 1
            
            # Determine if answer passes the gate
            passes_gate = quality_score >= 0 and len(issues) == 0
            
            # Generate missing context message if needed
            missing_context = None
            if not passes_gate:
                missing_context = self._generate_missing_context_message(issues, actionable_bullets, evidence_score, distinct_files)
            
            return {
                "passes_gate": passes_gate,
                "quality_score": quality_score,
                "issues": issues,
                "missing_context": missing_context,
                "metrics": {
                    "actionable_bullets": actionable_bullets,
                    "evidence_score": evidence_score,
                    "distinct_files": distinct_files,
                    "generic_phrases_found": len(generic_phrases_found) if generic_phrases_found else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking answer quality: {e}")
            return {
                "passes_gate": False,
                "quality_score": -1,
                "issues": [f"Error checking quality: {str(e)}"],
                "missing_context": "Unable to validate answer quality due to an error.",
                "metrics": {}
            }
    
    def _check_banned_phrases(self, answer: str) -> List[str]:
        """Check for banned generic phrases in the answer"""
        found_phrases = []
        
        for pattern in self.banned_patterns:
            if pattern.search(answer):
                # Extract the actual phrase found
                match = pattern.search(answer)
                if match:
                    found_phrases.append(match.group(0))
        
        return found_phrases
    
    def _count_actionable_bullets(self, answer: str) -> int:
        """Count actionable bullet points across First checks and Fix sections"""
        bullet_count = 0
        
        # Look for bullet points in First checks section (various formats)
        first_checks_patterns = [
            r'\*\*First checks:\*\*.*?(?=\*\*|$)',
            r'\*\*Quick Check:\*\*.*?(?=\*\*|$)',
            r'\*\*Quick Checks:\*\*.*?(?=\*\*|$)',
            r'\*\*Initial Checks:\*\*.*?(?=\*\*|$)',
            r'\*\*First Response:\*\*.*?(?=\*\*|$)',
            r'\*\*Immediate Actions:\*\*.*?(?=\*\*|$)'
        ]
        
        for pattern in first_checks_patterns:
            match = re.search(pattern, answer, re.DOTALL | re.IGNORECASE)
            if match:
                first_checks_text = match.group(0)
                # Count bullet points (•, -, *)
                bullets = re.findall(r'[•\-*]\s+', first_checks_text)
                bullet_count += len(bullets)
                break  # Use the first match found
        
        # Look for bullet points in Fix section (if present)
        fix_patterns = [
            r'\*\*Fix:\*\*.*?(?=\*\*|$)',
            r'\*\*Remediation:\*\*.*?(?=\*\*|$)',
            r'\*\*Solution:\*\*.*?(?=\*\*|$)',
            r'\*\*Resolution:\*\*.*?(?=\*\*|$)',
            r'\*\*Steps:\*\*.*?(?=\*\*|$)'
        ]
        
        for pattern in fix_patterns:
            match = re.search(pattern, answer, re.DOTALL | re.IGNORECASE)
            if match:
                fix_text = match.group(0)
                bullets = re.findall(r'[•\-*]\s+', fix_text)
                bullet_count += len(bullets)
                break  # Use the first match found
        
        # Also count numbered lists
        numbered_lists = re.findall(r'\d+\.\s+', answer)
        bullet_count += len(numbered_lists)
        
        # Count bullet points in any section that might contain actionable content
        if bullet_count < self.min_actionable_bullets:
            # Look for any bullet points in the answer
            all_bullets = re.findall(r'[•\-*]\s+', answer)
            bullet_count = len(all_bullets)
        
        return bullet_count
    
    def _calculate_evidence_score(self, citations: List[str], diagnostics: Optional[Dict[str, Any]] = None) -> int:
        """Calculate evidence score based on citations and diagnostics"""
        score = 0
        
        # Base score from citations
        if citations:
            score += min(len(citations), 3)  # Cap at 3 points for citations
        
        # Bonus points for diagnostics if present
        if diagnostics:
            if isinstance(diagnostics, dict):
                # Check if diagnostics contain actual data
                has_logs = any(key in diagnostics for key in ['logs', 'app', 'nginx', 'system'])
                has_queues = any(key in diagnostics for key in ['queues', 'main', 'dlq', 'processing'])
                
                if has_logs or has_queues:
                    score += 1
                
                # Additional points for comprehensive diagnostics
                if len(diagnostics) >= 3:
                    score += 1
        
        return score
    
    def _count_distinct_files(self, citations: List[str]) -> int:
        """Count distinct files from citations"""
        if not citations:
            return 0
        
        # Extract filenames from citations (format: filename#chunk_id)
        files = set()
        for citation in citations:
            if '#' in citation:
                filename = citation.split('#')[0]
                files.add(filename)
            else:
                # Handle citations without chunk IDs
                files.add(citation)
        
        return len(files)
    
    def _generate_missing_context_message(self, issues: List[str], actionable_bullets: int, evidence_score: int, distinct_files: int) -> str:
        """Generate a specific missing context message based on the issues found"""
        
        missing_sections = []
        
        # Determine what sections are missing based on the issues
        if actionable_bullets < self.min_actionable_bullets:
            missing_sections.append("**First Response/Diagnostics**")
        
        if evidence_score < self.min_evidence_threshold:
            missing_sections.append("**Detailed Diagnostics**")
        
        if distinct_files < self.min_distinct_files:
            missing_sections.append("**Remediation/Fix Procedures**")
        
        # Check for generic phrase issues
        generic_issues = [issue for issue in issues if "generic phrases" in issue]
        if generic_issues:
            missing_sections.append("**Specific Action Steps**")
        
        # Generate the missing context message
        if missing_sections:
            sections_text = ", ".join(missing_sections)
            message = f"""**Missing Context Detected**

Your question requires more specific information than what's currently available in the knowledge base. 

**Missing Sections:** {sections_text}

**To get a specific, actionable answer, please upload documentation covering:**
- **First Response/Diagnostics**: Step-by-step investigation procedures
- **Remediation/Fix**: Specific commands, configuration changes, or procedures
- **Validation/SLA**: How to verify the fix worked and measure success

**Current Answer Quality:**
- Actionable bullets: {actionable_bullets}/{self.min_actionable_bullets} required
- Evidence score: {evidence_score}/{self.min_evidence_threshold} required  
- Distinct files: {distinct_files}/{self.min_distinct_files} required

Upload the missing documentation to receive a specific, cited response instead of generic guidance."""
        else:
            message = """**Answer Quality Issue Detected**

The generated answer doesn't meet our quality standards for specificity and actionability. Please try rephrasing your question or upload additional documentation to receive a better response."""
        
        return message
    
    def enforce_gate(self, answer: str, citations: List[str], diagnostics: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enforce the anti-generic gate
        
        Returns:
            Tuple of (passes_gate, final_answer, quality_report)
        """
        quality_check = self.check_answer_quality(answer, citations, diagnostics)
        
        if quality_check["passes_gate"]:
            return True, answer, quality_check
        else:
            # Return the missing context message instead of the generic answer
            return False, quality_check["missing_context"], quality_check
    
    def get_quality_report(self, answer: str, citations: List[str], diagnostics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a detailed quality report without enforcing the gate"""
        return self.check_answer_quality(answer, citations, diagnostics)
