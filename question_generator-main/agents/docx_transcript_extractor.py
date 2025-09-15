#!/usr/bin/env python3
"""
DOCX Transcript Extractor
Extract transcript content from DOCX files for question generation
"""

import logging
from typing import List, Dict, Optional
import re
from datetime import timedelta

logger = logging.getLogger(__name__)

class DocxTranscriptExtractor:
    """
    Extract transcript content from DOCX files and convert to segments
    """
    
    def __init__(self):
        self.timestamp_patterns = [
            r'(\d{1,2}):(\d{2}):(\d{2})',  # HH:MM:SS
            r'(\d{1,2}):(\d{2})',  # MM:SS
            r'(\d+):(\d{2})',  # M:SS
        ]
    
    def extract_transcript_from_docx(self, docx_path: str) -> List[Dict]:
        """
        Extract transcript segments from DOCX file
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            List of transcript segments with timestamps and text
        """
        try:
            # Try importing docx library
            try:
                from docx import Document
            except ImportError:
                logger.error("python-docx not installed. Install with: pip install python-docx")
                return self._fallback_text_extraction(docx_path)
            
            logger.info(f"📄 Extracting transcript from: {docx_path}")
            
            # Load DOCX document
            doc = Document(docx_path)
            
            # Extract all paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)
            
            logger.info(f"📝 Extracted {len(paragraphs)} paragraphs from DOCX")
            
            # Process paragraphs into segments
            segments = self._process_paragraphs_to_segments(paragraphs)
            
            logger.info(f"✅ Converted to {len(segments)} transcript segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Error extracting from DOCX: {str(e)}")
            return []
    
    def _fallback_text_extraction(self, docx_path: str) -> List[Dict]:
        """
        Fallback method if python-docx is not available
        """
        logger.warning("Using fallback text extraction (limited functionality)")
        
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            # DOCX is a ZIP file with XML content
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # Extract the main document XML
                content = docx_zip.read('word/document.xml')
                
                # Parse XML and extract text
                root = ET.fromstring(content)
                
                # Find all text elements
                text_elements = []
                for elem in root.iter():
                    if elem.text:
                        text_elements.append(elem.text.strip())
                
                # Join text elements into paragraphs
                full_text = ' '.join([t for t in text_elements if t])
                paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
                
                logger.info(f"📝 Fallback extraction: {len(paragraphs)} text segments")
                
                # Process into segments
                return self._process_paragraphs_to_segments(paragraphs)
                
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {str(e)}")
            return []
    
    def _process_paragraphs_to_segments(self, paragraphs: List[str]) -> List[Dict]:
        """
        Process paragraphs into timestamped segments
        """
        try:
            segments = []
            current_timestamp = "00:00:00"
            segment_counter = 0
            
            for paragraph in paragraphs:
                # Look for timestamp patterns
                timestamp_match = self._find_timestamp_in_text(paragraph)
                
                if timestamp_match:
                    current_timestamp = timestamp_match
                    # Remove timestamp from text
                    clean_text = self._remove_timestamp_from_text(paragraph)
                else:
                    clean_text = paragraph
                
                # Skip very short texts
                if len(clean_text) < 20:
                    continue
                
                # Create segment
                segment = {
                    'timestamp': current_timestamp,
                    'time': current_timestamp,  # Alternative key
                    'text': clean_text,
                    'index': segment_counter
                }
                
                segments.append(segment)
                segment_counter += 1
                
                # Auto-increment timestamp if no explicit timestamp found
                if not timestamp_match:
                    current_timestamp = self._increment_timestamp(current_timestamp, 10)  # +10 seconds
            
            return segments
            
        except Exception as e:
            logger.error(f"Error processing paragraphs: {str(e)}")
            return []
    
    def _find_timestamp_in_text(self, text: str) -> Optional[str]:
        """Find timestamp pattern in text"""
        try:
            for pattern in self.timestamp_patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 3:
                        h, m, s = match.groups()
                        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                    elif len(match.groups()) == 2:
                        m, s = match.groups()
                        return f"00:{int(m):02d}:{int(s):02d}"
            return None
        except:
            return None
    
    def _remove_timestamp_from_text(self, text: str) -> str:
        """Remove timestamp patterns from text"""
        try:
            for pattern in self.timestamp_patterns:
                text = re.sub(pattern, '', text)
            
            # Clean up extra whitespace
            text = ' '.join(text.split())
            return text.strip()
        except:
            return text
    
    def _increment_timestamp(self, timestamp: str, seconds_to_add: int) -> str:
        """Increment timestamp by specified seconds"""
        try:
            h, m, s = map(int, timestamp.split(':'))
            total_seconds = h * 3600 + m * 60 + s + seconds_to_add
            
            new_h = total_seconds // 3600
            new_m = (total_seconds % 3600) // 60
            new_s = total_seconds % 60
            
            return f"{new_h:02d}:{new_m:02d}:{new_s:02d}"
        except:
            return timestamp
    
    def save_as_vtt(self, segments: List[Dict], output_path: str) -> bool:
        """
        Save segments as VTT file for compatibility
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(segments):
                    timestamp = segment.get('timestamp', '00:00:00')
                    text = segment.get('text', '')
                    
                    # Calculate end timestamp (assume 10 seconds per segment)
                    end_timestamp = self._increment_timestamp(timestamp, 10)
                    
                    f.write(f"{i+1}\n")
                    f.write(f"{timestamp}.000 --> {end_timestamp}.000\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"✅ Saved VTT file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving VTT: {str(e)}")
            return False
