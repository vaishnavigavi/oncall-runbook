import logging
import re
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import tiktoken

# PDF processing imports
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from .sectionizer import Sectionizer, Section

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing and chunking documents with section detection"""
    
    def __init__(self):
        self.sectionizer = Sectionizer()
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "100"))
        
    def process_document(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Process a document and return structured chunks with section metadata
        
        Args:
            file_path: Path to the document file
            content: Raw document content
            
        Returns:
            Dictionary containing chunks and section information
        """
        try:
            # Detect sections in the document
            sections = self.sectionizer.detect_sections(content)
            
            # Generate chunks with section metadata
            chunks = self._generate_chunks_with_sections(content, sections, file_path)
            
            # Get section summary
            section_summary = self.sectionizer.get_section_summary(sections)
            
            return {
                'chunks': chunks,
                'sections': sections,
                'section_summary': section_summary,
                'total_chunks': len(chunks),
                'total_sections': len(sections),
                'filename': Path(file_path).name
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                'chunks': [],
                'sections': [],
                'section_summary': {},
                'total_chunks': 0,
                'total_sections': 0,
                'filename': Path(file_path).name,
                'error': str(e)
            }
    
    def _generate_chunks_with_sections(self, content: str, sections: List[Section], filename: str) -> List[Dict[str, Any]]:
        """
        Generate chunks with section metadata preserved
        
        Args:
            content: Raw document content
            sections: Detected sections
            filename: Document filename
            
        Returns:
            List of chunks with section metadata
        """
        try:
            chunks = []
            lines = content.split('\n')
            
            # Create section line mapping
            section_line_map = self._create_section_line_map(sections, len(lines))
            
            # Generate chunks using heading-aware splitting
            current_chunk = []
            current_chunk_lines = []
            chunk_start_line = 0
            
            for line_num, line in enumerate(lines):
                current_chunk.append(line)
                current_chunk_lines.append(line_num)
                
                # Check if we should create a chunk
                if self._should_create_chunk(current_chunk, line_num, lines):
                    # Create chunk with section metadata
                    chunk_data = self._create_chunk_data(
                        current_chunk, 
                        current_chunk_lines, 
                        chunk_start_line, 
                        line_num, 
                        section_line_map, 
                        filename
                    )
                    chunks.append(chunk_data)
                    
                    # Start new chunk with overlap
                    overlap_lines = self._get_overlap_lines(current_chunk, current_chunk_lines)
                    current_chunk = overlap_lines['content']
                    current_chunk_lines = overlap_lines['line_numbers']
                    chunk_start_line = overlap_lines['start_line']
            
            # Add final chunk if there's remaining content
            if current_chunk:
                chunk_data = self._create_chunk_data(
                    current_chunk, 
                    current_chunk_lines, 
                    chunk_start_line, 
                    len(lines) - 1, 
                    section_line_map, 
                    filename
                )
                chunks.append(chunk_data)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error generating chunks with sections: {e}")
            return []
    
    def _create_section_line_map(self, sections: List[Section], total_lines: int) -> Dict[int, Section]:
        """
        Create a mapping from line numbers to sections
        
        Args:
            sections: Detected sections
            total_lines: Total number of lines in document
            
        Returns:
            Dictionary mapping line numbers to sections
        """
        try:
            section_map = {}
            
            for section in sections:
                for line_num in range(section.start_line, section.end_line + 1):
                    if line_num < total_lines:
                        section_map[line_num] = section
            
            return section_map
            
        except Exception as e:
            logger.error(f"Error creating section line map: {e}")
            return {}
    
    def _should_create_chunk(self, current_chunk: List[str], current_line: int, all_lines: List[str]) -> bool:
        """
        Determine if we should create a chunk at the current line
        
        Args:
            current_chunk: Current chunk content
            current_line: Current line number
            all_lines: All document lines
            
        Returns:
            True if chunk should be created
        """
        try:
            # Check if we've reached the chunk size limit
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) >= self.chunk_size:
                return True
            
            # Check if we're at a natural break point (heading)
            if current_line < len(all_lines):
                next_line = all_lines[current_line + 1].strip()
                if self._is_heading(next_line):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if chunk should be created: {e}")
            return False
    
    def _is_heading(self, line: str) -> bool:
        """Check if a line is a heading"""
        try:
            heading_patterns = [
                r'^(#{1,6})\s+',  # Markdown headings
                r'^(\*\*[^*]+\*\*)$',  # Bold text
                r'^([A-Z][A-Z\s]+:?)$',  # ALL CAPS headings
                r'^(\d+\.\s+)',  # Numbered lists
                r'^([A-Z]\.\s+)',  # Lettered lists
            ]
            
            for pattern in heading_patterns:
                if re.match(pattern, line):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if line is heading: {e}")
            return False
    
    def _get_overlap_lines(self, current_chunk: List[str], current_chunk_lines: List[int]) -> Dict[str, Any]:
        """
        Get overlap lines for the next chunk
        
        Args:
            current_chunk: Current chunk content
            current_chunk_lines: Line numbers in current chunk
            
        Returns:
            Dictionary with overlap content and metadata
        """
        try:
            if len(current_chunk) <= self.chunk_overlap:
                return {
                    'content': current_chunk,
                    'line_numbers': current_chunk_lines,
                    'start_line': current_chunk_lines[0] if current_chunk_lines else 0
                }
            
            # Get last N lines for overlap
            overlap_content = current_chunk[-self.chunk_overlap:]
            overlap_line_numbers = current_chunk_lines[-self.chunk_overlap:]
            
            return {
                'content': overlap_content,
                'line_numbers': overlap_line_numbers,
                'start_line': overlap_line_numbers[0] if overlap_line_numbers else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting overlap lines: {e}")
            return {
                'content': [],
                'line_numbers': [],
                'start_line': 0
            }
    
    def _create_chunk_data(self, chunk_lines: List[str], line_numbers: List[int], 
                          start_line: int, end_line: int, section_map: Dict[int, Section], 
                          filename: str) -> Dict[str, Any]:
        """
        Create chunk data with section metadata
        
        Args:
            chunk_lines: Lines in the chunk
            line_numbers: Line numbers in the chunk
            start_line: Starting line number
            end_line: Ending line number
            section_map: Mapping from line numbers to sections
            filename: Document filename
            
        Returns:
            Dictionary with chunk data and metadata
        """
        try:
            chunk_content = '\n'.join(chunk_lines)
            chunk_id = f"{filename}_{start_line}_{end_line}"
            
            # Determine which sections this chunk belongs to
            chunk_sections = self._get_chunk_sections(line_numbers, section_map)
            
            # Get primary section (most common in chunk)
            primary_section = self._get_primary_section(chunk_sections)
            
            # Create chunk metadata
            chunk_metadata = {
                'filename': filename,
                'chunk_id': chunk_id,
                'start_line': start_line,
                'end_line': end_line,
                'line_count': len(chunk_lines),
                'content_length': len(chunk_content),
                'sections': chunk_sections,
                'primary_section': primary_section,
                'section_types': list(set(section.section_type for section in chunk_sections)),
                'hierarchy_paths': list(set(section.hpath for section in chunk_sections)),
                'has_commands': any(section.metadata.get('has_commands', False) for section in chunk_sections),
                'has_metrics': any(section.metadata.get('has_metrics', False) for section in chunk_sections),
                'total_bullet_points': sum(section.metadata.get('bullet_points', 0) for section in chunk_sections),
                'total_code_blocks': sum(section.metadata.get('code_blocks', 0) for section in chunk_sections)
            }
            
            return {
                'id': chunk_id,
                'content': chunk_content,
                'metadata': chunk_metadata,
                'section_info': {
                    'primary_type': primary_section.section_type if primary_section else 'unknown',
                    'primary_hpath': primary_section.hpath if primary_section else '',
                    'all_types': chunk_metadata['section_types'],
                    'all_paths': chunk_metadata['hierarchy_paths']
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating chunk data: {e}")
            return {
                'id': f"{filename}_{start_line}_{end_line}",
                'content': '\n'.join(chunk_lines),
                'metadata': {
                    'filename': filename,
                    'chunk_id': f"{filename}_{start_line}_{end_line}",
                    'start_line': start_line,
                    'end_line': end_line,
                    'error': str(e)
                },
                'section_info': {
                    'primary_type': 'unknown',
                    'primary_hpath': '',
                    'all_types': [],
                    'all_paths': []
                }
            }
    
    def _get_chunk_sections(self, line_numbers: List[int], section_map: Dict[int, Section]) -> List[Section]:
        """
        Get sections that overlap with the chunk
        
        Args:
            line_numbers: Line numbers in the chunk
            section_map: Mapping from line numbers to sections
            
        Returns:
            List of sections that overlap with the chunk
        """
        try:
            chunk_sections = []
            seen_section_ids = set()
            
            for line_num in line_numbers:
                if line_num in section_map:
                    section = section_map[line_num]
                    # Use section title as unique identifier since Section objects are not hashable
                    section_id = f"{section.title}_{section.start_line}_{section.end_line}"
                    if section_id not in seen_section_ids:
                        chunk_sections.append(section)
                        seen_section_ids.add(section_id)
            
            return chunk_sections
            
        except Exception as e:
            logger.error(f"Error getting chunk sections: {e}")
            return []
    
    def _get_primary_section(self, chunk_sections: List[Section]) -> Optional[Section]:
        """
        Get the primary section for a chunk (most common or highest priority)
        
        Args:
            chunk_sections: Sections in the chunk
            
        Returns:
            Primary section or None
        """
        try:
            if not chunk_sections:
                return None
            
            if len(chunk_sections) == 1:
                return chunk_sections[0]
            
            # Count section types
            section_type_counts = {}
            for section in chunk_sections:
                section_type = section.section_type
                section_type_counts[section_type] = section_type_counts.get(section_type, 0) + 1
            
            # Find most common section type
            most_common_type = max(section_type_counts.items(), key=lambda x: x[1])[0]
            
            # Return first section of most common type
            for section in chunk_sections:
                if section.section_type == most_common_type:
                    return section
            
            return chunk_sections[0]  # Fallback
            
        except Exception as e:
            logger.error(f"Error getting primary section: {e}")
            return chunk_sections[0] if chunk_sections else None
    
    def get_processing_summary(self, processing_result: Dict[str, Any]) -> str:
        """
        Get a summary of document processing results
        
        Args:
            processing_result: Result from process_document
            
        Returns:
            Formatted summary string
        """
        try:
            if 'error' in processing_result:
                return f"❌ Error processing document: {processing_result['error']}"
            
            summary = f"📄 Document: {processing_result['filename']}\n"
            summary += f"📊 Sections detected: {processing_result['total_sections']}\n"
            summary += f"🔢 Chunks generated: {processing_result['total_chunks']}\n"
            
            if 'section_summary' in processing_result:
                section_summary = processing_result['section_summary']
                if 'section_types' in section_summary:
                    summary += "\n📋 Section Types:\n"
                    for section_type, count in section_summary['section_types'].items():
                        summary += f"  • {section_type}: {count}\n"
                
                if 'content_stats' in section_summary:
                    content_stats = section_summary['content_stats']
                    summary += f"\n📝 Content Stats:\n"
                    summary += f"  • Bullet points: {content_stats.get('total_bullet_points', 0)}\n"
                    summary += f"  • Code blocks: {content_stats.get('total_code_blocks', 0)}\n"
                    summary += f"  • Links: {content_stats.get('total_links', 0)}\n"
                    summary += f"  • Sections with commands: {content_stats.get('sections_with_commands', 0)}\n"
                    summary += f"  • Sections with metrics: {content_stats.get('sections_with_metrics', 0)}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating processing summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def export_sections_analysis(self, processing_result: Dict[str, Any]) -> str:
        """
        Export detailed sections analysis as markdown
        
        Args:
            processing_result: Result from process_document
            
        Returns:
            Markdown string with sections analysis
        """
        try:
            if 'error' in processing_result:
                return f"# Document Processing Error\n\n{processing_result['error']}"
            
            markdown = f"# Document Analysis: {processing_result['filename']}\n\n"
            
            # Add processing summary
            markdown += "## Processing Summary\n\n"
            markdown += f"- **Total Sections:** {processing_result['total_sections']}\n"
            markdown += f"- **Total Chunks:** {processing_result['total_chunks']}\n\n"
            
            # Add section summary
            if 'section_summary' in processing_result:
                markdown += "## Section Summary\n\n"
                section_summary = processing_result['section_summary']
                
                if 'section_types' in section_summary:
                    markdown += "### Section Types\n\n"
                    for section_type, count in section_summary['section_types'].items():
                        markdown += f"- **{section_type}**: {count}\n"
                    markdown += "\n"
                
                if 'content_stats' in section_summary:
                    markdown += "### Content Statistics\n\n"
                    content_stats = section_summary['content_stats']
                    markdown += f"- **Total Bullet Points:** {content_stats.get('total_bullet_points', 0)}\n"
                    markdown += f"- **Total Code Blocks:** {content_stats.get('total_code_blocks', 0)}\n"
                    markdown += f"- **Total Links:** {content_stats.get('total_links', 0)}\n"
                    markdown += f"- **Sections with Commands:** {content_stats.get('sections_with_commands', 0)}\n"
                    markdown += f"- **Sections with Metrics:** {content_stats.get('sections_with_metrics', 0)}\n\n"
            
            # Add detailed sections analysis
            if 'sections' in processing_result:
                markdown += "## Detailed Sections Analysis\n\n"
                markdown += self.sectionizer.export_sections_markdown(processing_result['sections'])
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error exporting sections analysis: {e}")
            return f"Error exporting analysis: {str(e)}"
