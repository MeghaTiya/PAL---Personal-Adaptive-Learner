"""
Agent 2: Context Validator
Extracts visual and slide context to validate transcript alignment
"""

import cv2
import logging
from typing import Dict, Optional, Any
import os
from datetime import datetime, timedelta
import re

# Try to import pytesseract, handle gracefully if not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

logger = logging.getLogger(__name__)

class ContextValidator:
    """
    Validates transcript segments by extracting and analyzing visual context
    """
    
    def __init__(self, use_vlm: bool = False):  # Default to False since we use VLM in StrategicQuestionGenerator
        """Initialize the context validator with VLM or OCR capabilities"""
        self.use_vlm = use_vlm
        self.vlm_validator = None
        self.tesseract_available = self._check_tesseract()
        
        if use_vlm:
            try:
                from .vlm_context_validator import VLMContextValidator
                self.vlm_validator = VLMContextValidator()
                if self.vlm_validator.available:
                    logger.info("VLM (Vision Language Model) ready for context extraction")
                else:
                    logger.warning("VLM not available, falling back to OCR")
                    self.use_vlm = False
            except ImportError:
                logger.info("VLM module not found, using OCR")
                self.use_vlm = False
        
        if not self.use_vlm and not self.tesseract_available:
            logger.warning("Neither VLM nor Tesseract OCR available. Install Tesseract with: sudo apt-get install tesseract-ocr")
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available"""
        return TESSERACT_AVAILABLE
    
    def validate_context(self, video_path: str, transcript_path: str) -> dict:
        """
        Main entry point for context validation - processes entire transcript
        
        Args:
            video_path: Path to the video file
            transcript_path: Path to the transcript file
            
        Returns:
            Dictionary containing full context analysis
        """
        try:
            # Load transcript - handle DOCX files specially
            from .transcript_loader import TranscriptLoader
            transcript_loader = TranscriptLoader()
            
            # Check if it's a DOCX file and handle appropriately
            file_extension = os.path.splitext(transcript_path)[1].lower()
            if file_extension == '.docx':
                # Use DOCX transcript extractor
                try:
                    from .docx_transcript_extractor import DocxTranscriptExtractor
                    docx_extractor = DocxTranscriptExtractor()
                    transcript_segments = docx_extractor.extract_transcript_from_docx(transcript_path)
                    logger.info(f"Extracted {len(transcript_segments)} segments from DOCX file")
                except ImportError:
                    logger.error("DOCX transcript extractor not available")
                    return {
                        'summary': 'DOCX extractor not available',
                        'segments': [],
                        'visual_elements': [],
                        'processing_stats': {
                            'total_segments': 0,
                            'validated_segments': 0,
                            'method_used': 'none'
                        }
                    }
            else:
                transcript_segments = transcript_loader.load(transcript_path)  # Changed from load_transcript to load
            
            if not transcript_segments:
                logger.warning("No transcript segments found")
                return {
                    'summary': 'No transcript content available',
                    'segments': [],
                    'visual_elements': [],
                    'processing_stats': {
                        'total_segments': 0,
                        'validated_segments': 0,
                        'method_used': 'none'
                    }
                }
            
            # Process segments and extract context
            validated_segments = []
            all_visual_elements = []
            
            logger.info(f"Processing {len(transcript_segments)} transcript segments")
            
            for i, segment in enumerate(transcript_segments):
                try:
                    # Validate each segment
                    result = self.validate(video_path, segment)
                    
                    if result:
                        validated_segments.append(result)
                        if result.get('visual_elements'):
                            all_visual_elements.extend(result['visual_elements'])
                        
                except Exception as e:
                    logger.error(f"Error processing segment {i}: {str(e)}")
                    continue
            
            # Generate summary
            summary = self._generate_summary(validated_segments, all_visual_elements)
            
            return {
                'summary': summary,
                'segments': validated_segments,
                'visual_elements': all_visual_elements,
                'processing_stats': {
                    'total_segments': len(transcript_segments),
                    'validated_segments': len(validated_segments),
                    'method_used': 'VLM' if self.use_vlm else 'OCR',
                    'visual_elements_found': len(all_visual_elements)
                }
            }
            
        except Exception as e:
            logger.error(f"Context validation failed: {str(e)}")
            return {
                'summary': f'Context validation error: {str(e)}',
                'segments': [],
                'visual_elements': [],
                'processing_stats': {
                    'total_segments': 0,
                    'validated_segments': 0,
                    'method_used': 'error'
                }
            }
    
    def _generate_summary(self, segments: list, visual_elements: list) -> str:
        """Generate a summary of the processed content"""
        if not segments:
            return "No content could be processed from the video"
        
        total_text = " ".join([seg.get('text', '') for seg in segments])
        word_count = len(total_text.split())
        
        summary_parts = [
            f"Processed {len(segments)} segments containing {word_count} words."
        ]
        
        if visual_elements:
            summary_parts.append(f"Found {len(visual_elements)} visual elements including slides, diagrams, and text.")
        
        # Extract key topics (simple keyword extraction)
        common_words = self._extract_key_topics(total_text)
        if common_words:
            summary_parts.append(f"Key topics: {', '.join(common_words[:5])}")
        
        return " ".join(summary_parts)
    
    def _extract_key_topics(self, text: str) -> list:
        """Simple keyword extraction for topic identification"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top words by frequency
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)

    def validate(self, video_path: str, snippet: dict) -> dict:
        """
        VISUAL-FIRST validation: Extract educational content primarily from slide visuals,
        use transcript as context for instructor explanations
        """
        try:
            timestamp = snippet.get('start', snippet.get('timestamp', '00:00:00'))
            transcript_text = snippet.get('text', '')
            
            logger.debug(f"ContextValidator.validate() called for timestamp: {timestamp}")
            logger.debug(f"Transcript text length: {len(transcript_text)} chars")
            logger.debug(f"VLM available: {self.use_vlm}")
            
            # Step 1: Extract frame (PRIMARY SOURCE for educational content)
            logger.debug("Extracting frame at timestamp")
            frame = self._extract_frame(video_path, timestamp)
            if frame is None:
                logger.warning(f"Could not extract frame at {timestamp}")
                return None
            
            logger.debug(f"Frame extracted successfully, shape: {frame.shape if hasattr(frame, 'shape') else 'unknown'}")
            
            # Step 2: Extract visual educational content (MAIN FOCUS)
            logger.debug("Analyzing visual content")
            if self.use_vlm and hasattr(self, 'vlm_validator') and self.vlm_validator and self.vlm_validator.available:
                # Use VLM for comprehensive visual analysis
                logger.debug("Using VLM for visual content extraction")
                visual_content = self._extract_visual_content_vlm(frame, transcript_text)
            else:
                # Use OCR for text extraction from slides
                logger.debug("Using OCR for visual content extraction")
                visual_content = self._extract_visual_content_ocr(frame)
            
            logger.debug(f"Visual content extraction result: {visual_content}")
            
            if not visual_content or not visual_content.get('educational_concepts'):
                logger.debug(f"No educational content found in visuals at {timestamp}")
                return None
            
            # Step 3: Build context (Visual Primary + Audio Context)
            context = {
                'timestamp': timestamp,
                'method': 'visual_first',
                
                # PRIMARY: What's shown on the slide
                'slide_content': visual_content.get('slide_text', ''),
                'educational_concepts': visual_content.get('educational_concepts', []),
                'visual_elements': visual_content.get('visual_elements', []),
                'slide_type': visual_content.get('slide_type', 'text_slide'),
                
                # SECONDARY: What instructor says about the visual
                'transcript_text': transcript_text,
                'instructor_context': transcript_text,
                
                # FOR QUESTIONS: Combined understanding
                'question_content': visual_content.get('slide_text', '') + '. ' + transcript_text,
                'confidence': visual_content.get('confidence', 0.0),
                'visual_elements': [f"Slide content: {visual_content.get('slide_text', '')[:100]}..."],
                
                # VLM ANALYSIS: Visual content analysis for question enrichment
                'vlm_analysis': {
                    'slide_text': visual_content.get('slide_text', ''),
                    'educational_concepts': visual_content.get('educational_concepts', []),
                    'visual_elements': visual_content.get('visual_elements', []),
                    'slide_type': visual_content.get('slide_type', 'text_slide'),
                    'confidence': visual_content.get('confidence', 0.0),
                    'analysis_method': 'VLM' if self.use_vlm else 'OCR',
                    'frame_analysis': f"Frame at {timestamp} contains slide with {len(visual_content.get('educational_concepts', []))} educational concepts"
                }
            }
            
            logger.info(f"Visual-first context extracted at {timestamp}: {len(visual_content.get('educational_concepts', []))} concepts")
            logger.debug(f"Context created with keys: {list(context.keys())}")
            logger.debug(f"Educational concepts found: {visual_content.get('educational_concepts', [])}")
            return context
            
        except Exception as e:
            logger.error(f"Visual-first validation failed: {str(e)}", exc_info=True)
            return None
    
    def _extract_visual_content_vlm(self, frame, transcript_context: str) -> dict:
        """Extract educational content from slide using VLM"""
        try:
            logger.debug("_extract_visual_content_vlm() called")
            if hasattr(self, 'vlm_validator') and self.vlm_validator:
                logger.debug("VLM validator available, calling analyze_frame")
                # Use existing VLM functionality
                result = self.vlm_validator.analyze_frame(frame, transcript_context)
                logger.debug(f"VLM analyze_frame result: {result}")
                
                extracted_result = {
                    'slide_text': result.get('extracted_text', ''),
                    'educational_concepts': result.get('concepts', []),
                    'visual_elements': result.get('visual_elements', []),
                    'slide_type': result.get('slide_type', 'text_slide'),
                    'confidence': result.get('confidence', 0.0)
                }
                logger.debug(f"VLM extraction result: {extracted_result}")
                return extracted_result
            else:
                logger.debug("VLM validator not available, falling back to OCR")
                return self._extract_visual_content_ocr(frame)
        except Exception as e:
            logger.warning(f"VLM visual extraction failed: {e}")
            logger.debug("Falling back to OCR due to VLM failure")
            return self._extract_visual_content_ocr(frame)
    
    def _extract_visual_content_ocr(self, frame) -> dict:
        """Extract text content from slide using OCR"""
        try:
            logger.debug("_extract_visual_content_ocr() called")
            if not self.tesseract_available:
                logger.warning("Tesseract not available for OCR")
                return {'slide_text': '', 'educational_concepts': [], 'confidence': 0.0}
            
            logger.debug("Running OCR on frame")
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(frame, config='--psm 6')
            logger.debug(f"OCR extracted text: {extracted_text[:200]}...")
            
            # Simple concept extraction from slide text
            logger.debug("Extracting concepts from OCR text")
            concepts = self._extract_concepts_from_text(extracted_text)
            logger.debug(f"Concepts extracted: {concepts}")
            
            result = {
                'slide_text': extracted_text.strip(),
                'educational_concepts': concepts,
                'visual_elements': ['Text slide with educational content'],
                'slide_type': 'text_slide',
                'confidence': 0.7 if len(concepts) > 0 else 0.3
            }
            
            logger.debug(f"OCR result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OCR visual extraction failed: {e}", exc_info=True)
            return {'slide_text': '', 'educational_concepts': [], 'confidence': 0.0}
    
    def _extract_concepts_from_text(self, text: str) -> list:
        """Extract educational concepts from slide text"""
        if not text or len(text.strip()) < 10:
            return []
        
        # Look for educational terms in slide text
        educational_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized terms
            r'\b\w+tion\b', r'\b\w+ment\b', r'\b\w+ness\b',  # Educational suffixes
            r'\b\w+ology\b', r'\b\w+ism\b', r'\b\w+ics\b'     # Academic suffixes
        ]
        
        concepts = []
        for pattern in educational_patterns:
            matches = re.findall(pattern, text)
            concepts.extend([match for match in matches if len(match) > 3])
        
        # Filter and deduplicate
        filtered_concepts = []
        common_words = {'the', 'and', 'but', 'for', 'are', 'with', 'this', 'that', 'from'}
        for concept in set(concepts):
            if concept.lower() not in common_words and len(concept) > 2:
                filtered_concepts.append(concept)
        
        return filtered_concepts[:10]  # Limit to top 10
    
    def _should_use_vlm(self, transcript_text: str) -> bool:
        """Determine if VLM would be beneficial for this segment"""
        
        # Use VLM for segments that likely have visual content
        vlm_indicators = [
            'chart', 'graph', 'diagram', 'figure', 'table', 'plot',
            'correlation', 'scatter', 'shows', 'see', 'look', 'example',
            'this is', 'here we', 'as you can see'
        ]
        
        text_lower = transcript_text.lower()
        return any(indicator in text_lower for indicator in vlm_indicators)
    
    def _validate_with_ocr(self, video_path: str, snippet: dict) -> dict:
        """Legacy OCR validation method"""
        
        timestamp = snippet.get('start', snippet.get('timestamp', '00:00:00'))
        transcript_text = snippet.get('text', '')
        
        try:
            # Extract frame at timestamp
            frame = self._extract_frame(video_path, timestamp)
            if frame is None:
                logger.warning(f"Could not extract frame at {timestamp}")
                return None
            
            # Extract text from slide/screen
            slide_text = self._extract_slide_text(frame)
            
            # Get visual description (placeholder for now)
            visual_desc = self._describe_visuals(frame)
            
            # Create context object
            context = {
                "timestamp": timestamp,
                "transcript_snippet": transcript_text,
                "slide_text": slide_text,
                "visual_description": visual_desc,
                "frame_width": frame.shape[1],
                "frame_height": frame.shape[0],
                "extraction_method": "OCR"
            }
            
            # Validation rules
            if self._is_valid_context(context):
                return context
            else:
                logger.info(f"Context validation failed for {timestamp}")
                return None
                
        except Exception as e:
            logger.error(f"Error validating context for {timestamp}: {str(e)}")
            return None
    
    def _extract_frame(self, video_path: str, timestamp: str) -> Optional[Any]:
        """
        Extract a frame from video at given timestamp
        
        Args:
            video_path: Path to video file
            timestamp: Timestamp string (HH:MM:SS)
            
        Returns:
            OpenCV frame or None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return None
            
            # Handle both string timestamps and float seconds
            if isinstance(timestamp, float) or isinstance(timestamp, int):
                total_seconds = float(timestamp)
            else:
                # Convert string timestamp to seconds
                time_parts = str(timestamp).split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = map(float, time_parts)
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                elif len(time_parts) == 2:
                    minutes, seconds = map(float, time_parts)
                    total_seconds = minutes * 60 + seconds
                else:
                    total_seconds = float(time_parts[0])
            
            # Get video FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(total_seconds * fps)
            
            # Set frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
            else:
                logger.warning(f"Could not read frame at {timestamp}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting frame: {str(e)}")
            return None
    
    def _extract_slide_text(self, frame) -> str:
        """
        Extract text from slide/screen using OCR
        
        Args:
            frame: OpenCV frame
            
        Returns:
            Extracted text
        """
        if not self.tesseract_available:
            logger.warning("Tesseract not available - cannot extract slide text")
            return ""
            
        try:
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply some preprocessing
            # Increase contrast
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (1, 1), 0)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(gray, lang='eng')
            
            # Clean up the text
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting slide text: {str(e)}")
            return ""
    
    def _describe_visuals(self, frame) -> str:
        """
        Generate visual description of the frame
        In production, this would use a vision model like BLIP or LLaVA
        
        Args:
            frame: OpenCV frame
            
        Returns:
            Visual description
        """
        # Placeholder - in production would use vision model
        # For now, do basic image analysis
        try:
            height, width = frame.shape[:2]
            
            # Basic color analysis
            mean_color = cv2.mean(frame)
            brightness = sum(mean_color[:3]) / 3
            
            # Edge detection for complexity
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = cv2.countNonZero(edges) / (height * width)
            
            description = f"Frame {width}x{height}, brightness: {brightness:.1f}"
            
            if edge_density > 0.1:
                description += ", complex visual content"
            elif edge_density > 0.05:
                description += ", moderate visual content"
            else:
                description += ", simple visual content"
            
            return description
            
        except Exception as e:
            logger.error(f"Error describing visuals: {str(e)}")
            return "Unable to analyze visual content"
    
    def _is_valid_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate if context is sufficient for question generation
        
        Args:
            context: Context dictionary
            
        Returns:
            True if valid, False otherwise
        """
        slide_text = context.get("slide_text", "").strip()
        visual_desc = context.get("visual_description", "").strip()
        transcript = context.get("transcript_snippet", "").strip()
        
        # Require at least some transcript content
        if len(transcript) < 10:
            return False
        
        # Require at least some visual or slide content
        if not slide_text and not visual_desc:
            return False
        
        # If we have slide text, it should be meaningful
        if slide_text and len(slide_text) < 5:
            return False
        
        # Check for alignment between transcript and slide
        if slide_text:
            # Simple word overlap check
            transcript_words = set(transcript.lower().split())
            slide_words = set(slide_text.lower().split())
            
            # Require some word overlap (indicating alignment)
            overlap = len(transcript_words.intersection(slide_words))
            if overlap < 2 and len(slide_text) > 20:
                logger.info("Low alignment between transcript and slide text")
                # Don't reject entirely, but note the issue
        
        return True
