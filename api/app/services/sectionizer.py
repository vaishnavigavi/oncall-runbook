import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Section:
    """Represents a detected document section"""
    title: str
    section_type: str
    level: int
    hpath: str
    start_line: int
    end_line: int
    content: str
    metadata: Dict[str, Any]

class Sectionizer:
    """Service for detecting and categorizing document sections during ingestion"""
    
    def __init__(self):
        # Section type detection patterns
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
                r'immediate\s+steps?'
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
                r'remediation\s+steps?'
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
                r'post\s+fix\s+checks?'
            ],
            'policy': [
                r'policy',
                r'policies',
                r'procedure',
                r'procedures',
                r'guideline',
                r'guidelines',
                r'standard',
                r'standards',
                r'rule',
                r'rules',
                r'requirement',
                r'requirements',
                r'compliance',
                r'governance'
            ],
            'gotchas': [
                r'gotcha',
                r'gotchas',
                r'common\s+mistakes?',
                r'pitfalls?',
                r'caveats?',
                r'warnings?',
                r'caution',
                r'important\s+notes?',
                r'key\s+points?',
                r'critical\s+notes?',
                r'watch\s+out',
                r'be\s+careful',
                r'note:',
                r'warning:',
                r'caution:'
            ],
            'background': [
                r'background',
                r'overview',
                r'introduction',
                r'context',
                r'description',
                r'explanation',
                r'rationale',
                r'reason',
                r'why',
                r'what\s+is',
                r'definition',
                r'concept',
                r'theory',
                r'principles?'
            ]
        }
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {}
        for section_type, patterns in self.section_patterns.items():
            self.compiled_patterns[section_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Heading detection patterns
        self.heading_patterns = [
            re.compile(r'^(#{1,6})\s+(.+)$'),  # Markdown headings
            re.compile(r'^([A-Z][A-Z\s]+)$'),  # ALL CAPS headings
            re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$'),  # Title Case headings
            re.compile(r'^(\d+\.\s+.+)$'),  # Numbered headings
            re.compile(r'^([A-Z]\.\s+.+)$'),  # Lettered headings
            re.compile(r'^(\*\*[^*]+\*\*)$'),  # Bold headings
            re.compile(r'^([A-Z][A-Z\s]+:)$'),  # ALL CAPS with colon
        ]
        
        # Section content boundaries
        self.content_boundary_patterns = [
            re.compile(r'^(#{1,6})\s+'),  # Markdown headings
            re.compile(r'^(\*\*[^*]+\*\*)$'),  # Bold text
            re.compile(r'^([A-Z][A-Z\s]+:?)$'),  # ALL CAPS headings
            re.compile(r'^(\d+\.\s+)'),  # Numbered lists
            re.compile(r'^([A-Z]\.\s+)'),  # Lettered lists
        ]
    
    def detect_sections(self, content: str) -> List[Section]:
        """
        Detect and categorize sections in document content
        
        Args:
            content: Raw document content
            
        Returns:
            List of detected sections with metadata
        """
        try:
            lines = content.split('\n')
            sections = []
            current_section = None
            current_content = []
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                # Check if this line is a heading
                heading_info = self._detect_heading(line)
                
                if heading_info:
                    # Save previous section if exists
                    if current_section:
                        current_section.end_line = line_num - 1
                        current_section.content = '\n'.join(current_content)
                        sections.append(current_section)
                    
                    # Start new section
                    title, level = heading_info
                    section_type = self._classify_section(title)
                    hpath = self._build_hpath(title, level, sections)
                    
                    current_section = Section(
                        title=title,
                        section_type=section_type,
                        level=level,
                        hpath=hpath,
                        start_line=line_num,
                        end_line=len(lines) - 1,  # Will be updated when next section starts
                        content='',
                        metadata={
                            'section_type': section_type,
                            'hpath': hpath,
                            'level': level,
                            'title': title,
                            'start_line': line_num,
                            'end_line': len(lines) - 1
                        }
                    )
                    current_content = []
                else:
                    # Add line to current section content
                    if current_section:
                        current_content.append(line)
            
            # Save final section
            if current_section:
                current_section.end_line = len(lines) - 1
                current_section.content = '\n'.join(current_content)
                sections.append(current_section)
            
            # Post-process sections to improve classification
            sections = self._post_process_sections(sections)
            
            logger.info(f"Detected {len(sections)} sections in document")
            return sections
            
        except Exception as e:
            logger.error(f"Error detecting sections: {e}")
            return []
    
    def _detect_heading(self, line: str) -> Optional[Tuple[str, int]]:
        """Detect if a line is a heading and return title and level"""
        try:
            # Check markdown headings
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                return title, level
            
            # Check ALL CAPS headings
            if line.isupper() and len(line) > 3 and not line.endswith('.'):
                return line.strip(), 2
            
            # Check Title Case headings (but not too long)
            if (re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', line) and 
                len(line) < 100 and not line.endswith('.')):
                return line.strip(), 3
            
            # Check numbered headings
            match = re.match(r'^(\d+\.\s+)(.+)$', line)
            if match:
                title = match.group(2).strip()
                return title, 4
            
            # Check lettered headings
            match = re.match(r'^([A-Z]\.\s+)(.+)$', line)
            if match:
                title = match.group(2).strip()
                return title, 4
            
            # Check bold headings
            match = re.match(r'^\*\*([^*]+)\*\*$', line)
            if match:
                title = match.group(1).strip()
                return title, 2
            
            # Check ALL CAPS with colon
            if line.isupper() and line.endswith(':'):
                title = line[:-1].strip()  # Remove colon
                return title, 2
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting heading: {e}")
            return None
    
    def _classify_section(self, title: str) -> str:
        """Classify a section based on its title"""
        try:
            title_lower = title.lower()
            
            # Check each section type
            for section_type, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    if pattern.search(title_lower):
                        return section_type
            
            # Default classification based on title characteristics
            if any(word in title_lower for word in ['check', 'verify', 'confirm', 'test']):
                return 'validate'
            elif any(word in title_lower for word in ['step', 'procedure', 'process', 'method']):
                return 'fix'
            elif any(word in title_lower for word in ['note', 'important', 'warning', 'caution']):
                return 'gotchas'
            elif any(word in title_lower for word in ['what', 'why', 'how', 'when', 'where']):
                return 'background'
            elif any(word in title_lower for word in ['policy', 'rule', 'standard', 'requirement']):
                return 'policy'
            else:
                return 'background'  # Default fallback
                
        except Exception as e:
            logger.error(f"Error classifying section: {e}")
            return 'background'
    
    def _build_hpath(self, title: str, level: int, existing_sections: List[Section]) -> str:
        """Build hierarchical path for a section"""
        try:
            # Clean title for path
            clean_title = re.sub(r'[^\w\s-]', '', title.lower())
            clean_title = re.sub(r'\s+', '-', clean_title).strip('-')
            
            if level == 1:
                return clean_title
            
            # Find parent section
            parent_section = None
            for section in reversed(existing_sections):
                if section.level < level:
                    parent_section = section
                    break
            
            if parent_section:
                return f"{parent_section.hpath}/{clean_title}"
            else:
                return clean_title
                
        except Exception as e:
            logger.error(f"Error building hpath: {e}")
            return title.lower().replace(' ', '-')
    
    def _post_process_sections(self, sections: List[Section]) -> List[Section]:
        """Post-process sections to improve classification and metadata"""
        try:
            for section in sections:
                # Enhance metadata with content analysis
                section.metadata.update({
                    'bullet_points': self._count_bullet_points(section.content),
                    'code_blocks': self._count_code_blocks(section.content),
                    'links': self._count_links(section.content),
                    'content_length': len(section.content),
                    'has_commands': self._has_commands(section.content),
                    'has_metrics': self._has_metrics(section.content)
                })
                
                # Refine section type based on content
                refined_type = self._refine_section_type(section)
                if refined_type != section.section_type:
                    section.section_type = refined_type
                    section.metadata['section_type'] = refined_type
                    section.metadata['original_type'] = section.section_type
            
            return sections
            
        except Exception as e:
            logger.error(f"Error post-processing sections: {e}")
            return sections
    
    def _count_bullet_points(self, content: str) -> int:
        """Count bullet points in section content"""
        try:
            bullet_patterns = [r'^\s*[•\-*]\s+', r'^\s*\d+\.\s+', r'^\s*[A-Z]\.\s+']
            count = 0
            for pattern in bullet_patterns:
                count += len(re.findall(pattern, content, re.MULTILINE))
            return count
        except Exception as e:
            logger.error(f"Error counting bullet points: {e}")
            return 0
    
    def _count_code_blocks(self, content: str) -> int:
        """Count code blocks in section content"""
        try:
            # Count markdown code blocks
            code_block_pattern = r'```[\s\S]*?```'
            inline_code_pattern = r'`[^`]+`'
            
            code_blocks = len(re.findall(code_block_pattern, content))
            inline_codes = len(re.findall(inline_code_pattern, content))
            
            return code_blocks + inline_codes
        except Exception as e:
            logger.error(f"Error counting code blocks: {e}")
            return 0
    
    def _count_links(self, content: str) -> int:
        """Count links in section content"""
        try:
            # Count markdown links and URLs
            markdown_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
            urls = len(re.findall(r'https?://[^\s]+', content))
            
            return markdown_links + urls
        except Exception as e:
            logger.error(f"Error counting links: {e}")
            return 0
    
    def _has_commands(self, content: str) -> bool:
        """Check if section contains command examples"""
        try:
            command_patterns = [
                r'`[^`]*\b(?:ssh|curl|wget|git|docker|kubectl|helm|terraform|ansible|make|npm|yarn|pip|apt|yum|brew)\b[^`]*`',
                r'```[\s\S]*?\b(?:ssh|curl|wget|git|docker|kubectl|helm|terraform|ansible|make|npm|yarn|pip|apt|yum|brew)\b[\s\S]*?```'
            ]
            
            for pattern in command_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for commands: {e}")
            return False
    
    def _has_metrics(self, content: str) -> bool:
        """Check if section contains metrics or measurements"""
        try:
            metric_patterns = [
                r'\b\d+(?:\.\d+)?\s*(?:ms|s|min|hour|day|%|MB|GB|TB|KB|bps|req/s|ops/s)\b',
                r'\b(?:high|low|medium|critical|warning|error|success|failure)\b',
                r'\b(?:threshold|limit|quota|rate|latency|throughput|availability|uptime)\b'
            ]
            
            for pattern in metric_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for metrics: {e}")
            return False
    
    def _refine_section_type(self, section: Section) -> str:
        """Refine section type based on content analysis"""
        try:
            content_lower = section.content.lower()
            
            # Check for strong indicators in content
            if section.metadata['has_commands'] and section.metadata['bullet_points'] > 2:
                if section.section_type in ['background', 'policy']:
                    return 'fix'
            
            if section.metadata['has_metrics'] and section.metadata['bullet_points'] > 1:
                if section.section_type in ['background', 'policy']:
                    return 'validate'
            
            if section.metadata['bullet_points'] > 5:
                if section.section_type == 'background':
                    return 'fix'
            
            # Check content keywords for refinement
            if any(word in content_lower for word in ['check', 'verify', 'confirm', 'test']):
                if section.section_type == 'background':
                    return 'validate'
            
            if any(word in content_lower for word in ['step', 'procedure', 'process', 'method']):
                if section.section_type == 'background':
                    return 'fix'
            
            return section.section_type
            
        except Exception as e:
            logger.error(f"Error refining section type: {e}")
            return section.section_type
    
    def get_section_summary(self, sections: List[Section]) -> Dict[str, Any]:
        """Get summary statistics for detected sections"""
        try:
            summary = {
                'total_sections': len(sections),
                'section_types': {},
                'hierarchy_levels': {},
                'content_stats': {
                    'total_bullet_points': 0,
                    'total_code_blocks': 0,
                    'total_links': 0,
                    'sections_with_commands': 0,
                    'sections_with_metrics': 0
                }
            }
            
            for section in sections:
                # Count section types
                section_type = section.section_type
                summary['section_types'][section_type] = summary['section_types'].get(section_type, 0) + 1
                
                # Count hierarchy levels
                level = section.level
                summary['hierarchy_levels'][level] = summary['hierarchy_levels'].get(level, 0) + 1
                
                # Aggregate content stats
                summary['content_stats']['total_bullet_points'] += section.metadata.get('bullet_points', 0)
                summary['content_stats']['total_code_blocks'] += section.metadata.get('code_blocks', 0)
                summary['content_stats']['total_links'] += section.metadata.get('links', 0)
                
                if section.metadata.get('has_commands', False):
                    summary['content_stats']['sections_with_commands'] += 1
                
                if section.metadata.get('has_metrics', False):
                    summary['content_stats']['sections_with_metrics'] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating section summary: {e}")
            return {}
    
    def export_sections_markdown(self, sections: List[Section]) -> str:
        """Export detected sections as markdown for review"""
        try:
            markdown = "# Document Sections Analysis\n\n"
            
            for section in sections:
                markdown += f"## {section.title}\n\n"
                markdown += f"**Type:** {section.section_type}\n"
                markdown += f"**Level:** {section.level}\n"
                markdown += f"**Path:** {section.hpath}\n"
                markdown += f"**Lines:** {section.start_line + 1}-{section.end_line + 1}\n\n"
                
                # Add metadata
                markdown += "**Metadata:**\n"
                for key, value in section.metadata.items():
                    if key not in ['title', 'level', 'hpath', 'start_line', 'end_line']:
                        markdown += f"- {key}: {value}\n"
                markdown += "\n"
                
                # Add content preview
                content_preview = section.content[:200] + "..." if len(section.content) > 200 else section.content
                markdown += f"**Content Preview:**\n```\n{content_preview}\n```\n\n"
                markdown += "---\n\n"
            
            return markdown
            
        except Exception as e:
            logger.error(f"Error exporting sections markdown: {e}")
            return f"Error exporting sections: {str(e)}"

