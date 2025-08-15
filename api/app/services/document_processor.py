import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleTokenizer:
    """Simple word-based tokenizer as replacement for tiktoken"""
    
    def __init__(self):
        self.avg_chars_per_token = 4.0  # Rough estimate
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count based on character count"""
        if not text:
            return 0
        return int(len(text) / self.avg_chars_per_token)
    
    def encode(self, text: str) -> List[str]:
        """Simple word-based encoding"""
        if not text:
            return []
        # Split on whitespace and punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        return words

class DocumentProcessor:
    """Process documents and extract chunks with section detection"""
    
    def __init__(self):
        self.tokenizer = SimpleTokenizer()
        self.max_chunk_tokens = 800
        self.overlap_tokens = 100
    
    def process_document(self, filename: str, content: str) -> Dict[str, Any]:
        """Process a document and return chunks with metadata"""
        try:
            # Detect document type
            doc_type = self._detect_document_type(filename)
            
            # Extract text based on type
            if doc_type == 'pdf':
                text = self._extract_pdf_text(content)
            else:
                text = content
            
            # Detect sections
            sections = self._detect_sections(text)
            
            # Create chunks
            chunks = self._create_chunks(text, sections, filename)
            
            return {
                'status': 'success',
                'filename': filename,
                'doc_type': doc_type,
                'sections_detected': len(sections),
                'chunks_created': len(chunks),
                'chunks': chunks,
                'sections': sections
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return {
                'status': 'error',
                'filename': filename,
                'error': str(e)
            }
    
    def _detect_document_type(self, filename: str) -> str:
        """Detect document type from filename"""
        ext = Path(filename).suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext == '.md':
            return 'markdown'
        elif ext == '.txt':
            return 'text'
        elif ext == '.log':
            return 'log'
        else:
            return 'text'
    
    def _extract_pdf_text(self, content: str) -> str:
        """Extract text from PDF content"""
        # This is a placeholder - in practice, content should already be extracted text
        return content
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect document sections based on headings"""
        sections = []
        
        # Split text into lines
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for headings (markdown style)
            if line.startswith('# '):
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new section
                title = line[2:].strip()
                section_type = self._classify_section(title)
                current_section = {
                    'title': title,
                    'type': section_type,
                    'level': 1,
                    'content': '',
                    'hpath': title
                }
                current_content = []
                
            elif line.startswith('## '):
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new subsection
                title = line[3:].strip()
                section_type = self._classify_section(title)
                current_section = {
                    'title': title,
                    'type': section_type,
                    'level': 2,
                    'content': '',
                    'hpath': title
                }
                current_content = []
                
            elif line.startswith('### '):
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new subsubsection
                title = line[4:].strip()
                section_type = self._classify_section(title)
                current_section = {
                    'title': title,
                    'type': section_type,
                    'level': 3,
                    'content': '',
                    'hpath': title
                }
                current_content = []
                
            else:
                # Add content to current section
                if current_section:
                    current_content.append(line)
        
        # Save final section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            sections.append(current_section)
        
        return sections
    
    def _classify_section(self, title: str) -> str:
        """Classify section type based on title"""
        title_lower = title.lower()
        
        # First checks
        if any(word in title_lower for word in ['check', 'verify', 'monitor', 'investigate', 'diagnose']):
            return 'first_checks'
        
        # Fix/Remediation
        if any(word in title_lower for word in ['fix', 'resolve', 'remediate', 'solution', 'action', 'step']):
            return 'fix'
        
        # Validation
        if any(word in title_lower for word in ['validate', 'verify', 'confirm', 'test', 'sla', 'metric']):
            return 'validate'
        
        # Policy
        if any(word in title_lower for word in ['policy', 'procedure', 'guideline', 'rule', 'standard']):
            return 'policy'
        
        # Gotchas
        if any(word in title_lower for word in ['gotcha', 'warning', 'caution', 'note', 'important']):
            return 'gotchas'
        
        # Background
        if any(word in title_lower for word in ['background', 'overview', 'introduction', 'context']):
            return 'background'
        
        # Default to first_checks for action-oriented titles
        if any(word in title_lower for word in ['how', 'what', 'when', 'where', 'why']):
            return 'first_checks'
        
        return 'background'
    
    def _create_chunks(self, text: str, sections: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        """Create chunks from document text"""
        chunks = []
        
        # Process each section
        for section in sections:
            section_text = section.get('content', '')
            if not section_text.strip():
                continue
            
            # Create chunks for this section
            section_chunks = self._split_section_into_chunks(
                section_text, 
                section, 
                filename
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _split_section_into_chunks(self, text: str, section: Dict[str, Any], filename: str) -> List[Dict[str, Any]]:
        """Split a section into chunks"""
        chunks = []
        
        # Simple splitting by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Estimate tokens in this paragraph
            paragraph_tokens = self.tokenizer.count_tokens(paragraph)
            
            # If adding this paragraph would exceed chunk size
            if current_tokens + paragraph_tokens > self.max_chunk_tokens and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunk_id = self._generate_chunk_id(filename, section['title'], len(chunks))
                
                chunks.append({
                    'id': chunk_id,
                    'text': chunk_text,
                    'section_type': section['type'],
                    'section_title': section['title'],
                    'hpath': section['hpath'],
                    'filename': filename,
                    'tokens': current_tokens,
                    'metadata': {
                        'section_type': section['type'],
                        'section_title': section['title'],
                        'hpath': section['hpath']
                    }
                })
                
                # Start new chunk with overlap
                if self.overlap_tokens > 0:
                    # Keep last few paragraphs for overlap
                    overlap_text = []
                    overlap_tokens = 0
                    for para in reversed(current_chunk):
                        para_tokens = self.tokenizer.count_tokens(para)
                        if overlap_tokens + para_tokens <= self.overlap_tokens:
                            overlap_text.insert(0, para)
                            overlap_tokens += para_tokens
                        else:
                            break
                    current_chunk = overlap_text
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0
            
            # Add paragraph to current chunk
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk_id = self._generate_chunk_id(filename, section['title'], len(chunks))
            
            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'section_type': section['type'],
                'section_title': section['title'],
                'hpath': section['hpath'],
                'filename': filename,
                'tokens': current_tokens,
                'metadata': {
                    'section_type': section['type'],
                    'section_title': section['title'],
                    'hpath': section['hpath']
                }
            })
        
        return chunks
    
    def _generate_chunk_id(self, filename: str, section_title: str, chunk_index: int) -> str:
        """Generate a unique chunk ID"""
        # Create a hash-based ID
        content = f"{filename}:{section_title}:{chunk_index}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:8]
