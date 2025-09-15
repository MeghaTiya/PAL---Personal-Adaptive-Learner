#!/usr/bin/env python3
"""
Strategic Question Generator
Generates Easy/Medium/Hard questions for each validated timestamp using Frame + Transcript analysis
"""

import logging
import cv2
import base64
import requests
import json
import re
import random
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import timedelta
from .video_processor import VideoProcessor

logger = logging.getLogger(__name__)

class StrategicQuestionGenerator:
    """
    Generate 3-tier difficulty questions (Easy/Medium/Hard) for each validated educational moment
    Uses Frame + Transcript hybrid analysis
    """
    
    def __init__(self, ollama_url="http://localhost:11434", vlm_model="llava:7b"):
        self.ollama_url = ollama_url
        self.vlm_model = vlm_model
        self.llm_model = "llama3.1:8b-instruct-q4_K_M"  # For educational concept extraction
        self.video_processor = VideoProcessor()
        
        # Question generation strategy
        self.DIFFICULTY_TIERS = {
            'easy': {
                'cognitive_levels': ['remember', 'understand'],
                'question_types': ['factual', 'true_false', 'mcq'],
                'complexity': 'simple',
                'description': 'Basic recall and comprehension'
            },
            'medium': {
                'cognitive_levels': ['apply', 'analyze'],
                'question_types': ['mcq', 'msq', 'short_answer'],
                'complexity': 'moderate',
                'description': 'Application and analysis'
            },
            'hard': {
                'cognitive_levels': ['evaluate', 'create'],
                'question_types': ['msq', 'nat', 'essay'],
                'complexity': 'complex',
                'description': 'Critical thinking and synthesis'
            }
        }
        
        # Check VLM availability
        self.vlm_available = self._check_vlm_availability()
        logger.info(f"Strategic Question Generator initialized - VLM Available: {self.vlm_available}")
    
    def _check_vlm_availability(self) -> bool:
        """Check if VLM is available for frame analysis"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                return self.vlm_model in available_models
            return False
        except:
            return False
    
    def generate_strategic_questions(self, video_path: str, validated_segments: List[Dict], 
                                   target_questions_per_segment: int = 3) -> List[Dict]:
        """
        Main method: Generate strategic questions for each validated segment
        
        Args:
            video_path: Path to video file
            validated_segments: List of validated transcript segments with timestamps
            target_questions_per_segment: Questions per segment (default 3 for Easy/Medium/Hard)
            
        Returns:
            List of strategically generated questions with difficulty tiers
        """
        try:
            logger.info(f"🎯 Starting strategic question generation")
            logger.info(f"📊 Input: {len(validated_segments)} validated segments")
            logger.info(f"🎪 Target: {target_questions_per_segment} questions per segment")
            
            if not self.vlm_available:
                logger.warning("⚠️ VLM not available, using transcript-only analysis")
            
            all_questions = []
            
            # Process each validated segment
            for i, segment in enumerate(validated_segments):
                logger.info(f"🔍 Processing segment {i+1}/{len(validated_segments)}: {segment.get('timestamp', 'unknown')}")
                
                try:
                    # Step 1: Get frame at timestamp
                    frame_data = None
                    if self.vlm_available and video_path:
                        frame_data = self._extract_frame_at_timestamp(video_path, segment)
                    
                    # Step 2: Analyze educational content (Frame + Transcript)
                    educational_analysis = self._analyze_educational_content(segment, frame_data)
                    
                    # More lenient confidence check - if we have good transcript analysis, proceed
                    transcript_confidence = educational_analysis.get('transcript_analysis_confidence', 0)
                    overall_confidence = educational_analysis.get('confidence', 0)
                    has_topics = len(educational_analysis.get('topics', [])) > 0
                    
                    # Very lenient thresholds for debugging
                    if overall_confidence < 0.1 and transcript_confidence < 0.1 and not has_topics:
                        logger.warning(f"⚠️ Very low confidence analysis for segment {i+1} (overall: {overall_confidence:.2f}, transcript: {transcript_confidence:.2f}, topics: {len(educational_analysis.get('topics', []))}), skipping")
                        continue
                    else:
                        logger.info(f"✅ Proceeding with segment {i+1} - Overall: {overall_confidence:.2f}, Transcript: {transcript_confidence:.2f}, Topics: {len(educational_analysis.get('topics', []))}")
                    
                    # Step 3: Generate 3-tier questions (Easy/Medium/Hard)
                    segment_questions = self._generate_tiered_questions(
                        educational_analysis, 
                        segment, 
                        target_questions_per_segment
                    )
                    
                    # Step 4: Add metadata and tags
                    for question in segment_questions:
                        question.update({
                            'segment_index': i,
                            'timestamp': segment.get('timestamp', '00:00:00'),
                            'source': 'strategic_hybrid_analysis',
                            'educational_confidence': educational_analysis.get('confidence', 0),
                            'content_topics': educational_analysis.get('topics', []),
                            'visual_elements': educational_analysis.get('visual_elements', ''),
                            'transcript_text': segment.get('text', '')[:100] + '...',
                            
                            # NEW: Add detailed analysis tracking as requested
                            'vlm_analysis': educational_analysis.get('vlm_analysis', 'No VLM analysis available'),
                            'transcript_analysis': educational_analysis.get('transcript_analysis', {}),
                            'frame_analysis_confidence': educational_analysis.get('frame_analysis_confidence', 0),
                            'transcript_analysis_confidence': educational_analysis.get('transcript_analysis_confidence', 0),
                            'educational_indicators': educational_analysis.get('educational_indicators', []),
                            'concept_extraction_method': educational_analysis.get('concept_extraction_method', 'unknown')
                        })
                    
                    all_questions.extend(segment_questions)
                    logger.info(f"✅ Generated {len(segment_questions)} strategic questions for segment {i+1}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing segment {i+1}: {str(e)}")
                    continue
            
            logger.info(f"🎉 Strategic generation complete: {len(all_questions)} total questions")
            
            # Step 5: Final quality ranking and distribution check
            return self._optimize_question_distribution(all_questions)
            
        except Exception as e:
            logger.error(f"❌ Strategic question generation failed: {str(e)}")
            return []
    
    def _extract_frame_at_timestamp(self, video_path: str, segment: Dict) -> Optional[np.ndarray]:
        """Extract frame at specific timestamp"""
        try:
            timestamp_str = segment.get('timestamp', segment.get('time', '00:00:00'))
            
            # Parse timestamp to seconds
            if ':' in timestamp_str:
                parts = timestamp_str.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(float, parts)
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                else:
                    total_seconds = float(parts[0]) * 60 + float(parts[1])
            else:
                total_seconds = float(timestamp_str)
            
            # Extract frame using video processor
            frame = self.video_processor.get_frame_at_timestamp(video_path, total_seconds)
            return frame
            
        except Exception as e:
            logger.error(f"Error extracting frame at timestamp {segment.get('timestamp')}: {str(e)}")
            return None
    
    def _analyze_educational_content(self, segment: Dict, frame_data: Optional[np.ndarray]) -> Dict:
        """
        Analyze educational content using Frame + Transcript hybrid approach with detailed analysis tracking
        """
        try:
            transcript_text = segment.get('text', '').strip()
            
            # Initialize detailed analysis tracking
            vlm_analysis_text = "No VLM analysis performed"
            visual_context = ""
            frame_confidence = 0.0
            
            # Get visual context from frame analysis
            if frame_data is not None and self.vlm_available:
                logger.info(f"🎥 Performing VLM frame analysis...")
                try:
                    frame_analysis = self._analyze_frame_with_vlm(frame_data, transcript_text)
                    if frame_analysis:
                        visual_context = frame_analysis.get('visual_elements', '')
                        vlm_analysis_text = frame_analysis.get('raw_analysis', 'VLM analysis completed')
                        frame_confidence = 0.6
                        logger.info(f"✅ VLM analysis complete: {len(vlm_analysis_text)} chars")
                    else:
                        logger.warning("⚠️ VLM analysis returned no results, using transcript-only mode")
                        vlm_analysis_text = "VLM analysis failed - no results returned"
                except Exception as e:
                    logger.warning(f"⚠️ VLM analysis failed ({str(e)[:100]}...), using transcript-only mode")
                    vlm_analysis_text = f"VLM analysis failed: {str(e)[:100]}..."
            
            # Use improved transcript analysis
            logger.info(f"🔍 Analyzing transcript educational content: {transcript_text[:100]}...")
            educational_analysis = self._analyze_transcript_content(transcript_text)
            
            # Map the returned structure to expected fields
            transcript_confidence = min(len(educational_analysis.get('topics', [])) * 0.2 + 
                                      educational_analysis.get('educational_indicators', 0) * 0.1, 0.8)
            
            # Build comprehensive analysis with detailed tracking
            analysis = {
                'timestamp': segment.get('timestamp', '00:00:00'),
                'confidence': transcript_confidence + frame_confidence,
                'topics': educational_analysis.get('topics', []),
                'concepts': educational_analysis.get('concepts', []),
                'visual_elements': visual_context,
                'learning_objectives': educational_analysis.get('learning_objectives', f"Understanding concepts: {', '.join(educational_analysis.get('topics', [])[:3])}"),
                'content_complexity': 'intermediate',
                'educational_domain': 'statistical_analysis',
                'question_opportunities': educational_analysis.get('educational_indicators', []),
                'segment_text': transcript_text,  # Add actual transcript text for question generation
                
                # NEW: Detailed analysis tracking for output
                'vlm_analysis': vlm_analysis_text,
                'transcript_analysis': {
                    'primary_concepts': educational_analysis.get('topics', []),
                    'educational_indicators': educational_analysis.get('educational_indicators', 0),
                    'content_quality': transcript_confidence,
                    'extraction_method': 'rule_based_analysis'
                },
                'frame_analysis_confidence': frame_confidence,
                'transcript_analysis_confidence': transcript_confidence,
                'concept_extraction_method': 'rule_based_analysis',
                'extraction_method': 'hybrid' if frame_confidence > 0 else 'transcript_only'
            }
            
            # Quality assessment with bonuses
            if len(analysis['topics']) >= 2 and analysis['confidence'] > 0.3:
                analysis['confidence'] += 0.2  # Bonus for having good topics
                logger.info(f"✅ Quality bonus applied for {len(analysis['topics'])} topics")
            
            if visual_context and any(term in visual_context.lower() for term in ['diagram', 'chart', 'slide', 'graph']):
                analysis['confidence'] += 0.2  # Bonus for visual educational content
                logger.info(f"✅ Visual education bonus applied")
            
            analysis['confidence'] = min(analysis['confidence'], 1.0)
            
            logger.info(f"📊 Final analysis - Topics: {len(analysis['topics'])}, Confidence: {analysis['confidence']:.2f}, Method: {analysis['extraction_method']}")
            logger.info(f"🎯 Extracted topics: {analysis['topics'][:3]}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing educational content: {str(e)}")
            return {
                'confidence': 0.0, 
                'topics': [], 
                'concepts': [],
                'vlm_analysis': 'Analysis failed',
                'transcript_analysis': {},
                'frame_analysis_confidence': 0,
                'transcript_analysis_confidence': 0,
                'concept_extraction_method': 'failed'
            }
    
    def _analyze_transcript_content(self, transcript_text: str) -> Dict:
        """Analyze transcript content for educational indicators using LLM"""
        try:
            # Use LLM for better educational concept extraction
            if hasattr(self, 'llm_model') and self.llm_model:
                return self._extract_concepts_with_llm(transcript_text)
            else:
                return self._extract_concepts_rule_based(transcript_text)
                
        except Exception as e:
            logger.error(f"Error analyzing transcript: {str(e)}")
            return {'topics': [], 'concepts': []}
    
    def _extract_concepts_with_llm(self, transcript_text: str) -> Dict:
        """Extract educational concepts using LLM for better quality"""
        try:
            prompt = f"""
Analyze this educational transcript and extract key educational concepts:

Transcript: "{transcript_text}"

Extract ONLY genuine educational concepts, terms, and topics. Ignore filler words, casual expressions, and non-educational content.

Provide a JSON response with:
{{
    "primary_concepts": ["concept1", "concept2", "concept3"],
    "educational_indicators": ["indicator1", "indicator2"],
    "content_quality": 0.8,
    "subject_domain": "statistics/psychology/etc"
}}

Focus on:
- Technical terms and academic concepts
- Subject-specific vocabulary  
- Key ideas and principles
- Methodological concepts

Exclude:
- Filler words (okay, um, today, yeah, etc.)
- Common conversational words
- Non-educational casual language
"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_k": 10,
                        "top_p": 0.8
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        extracted_data = json.loads(json_match.group())
                        
                        # Validate and clean the extracted data
                        primary_concepts = extracted_data.get('primary_concepts', [])
                        # Filter out common filler words
                        filler_words = {'okay', 'today', 'yeah', 'um', 'uh', 'like', 'so', 'well', 'now', 'then'}
                        clean_concepts = [concept for concept in primary_concepts 
                                        if isinstance(concept, str) and concept.lower() not in filler_words and len(concept) > 2]
                        
                        return {
                            'topics': clean_concepts[:5],
                            'concepts': clean_concepts,
                            'educational_indicators': extracted_data.get('educational_indicators', []),
                            'content_quality': min(extracted_data.get('content_quality', 0.5), 1.0),
                            'subject_domain': extracted_data.get('subject_domain', 'general'),
                            'learning_objectives': f"Understand key concepts: {', '.join(clean_concepts[:3])}"
                        }
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Failed to parse LLM response as JSON: {e}")
                    
        except Exception as e:
            logger.warning(f"LLM concept extraction failed: {str(e)}")
        
        # Fallback to rule-based approach
        return self._extract_concepts_rule_based(transcript_text)
    
    def _extract_concepts_rule_based(self, transcript_text: str) -> Dict:
        """Fallback rule-based concept extraction with better filtering"""
    def _extract_concepts_rule_based(self, transcript_text: str) -> Dict:
        """Fallback rule-based concept extraction with better filtering"""
        try:
            analysis = {}
            
            # Educational keywords and phrases
            educational_indicators = {
                'definitions': ['is defined as', 'means', 'refers to', 'is called', 'known as'],
                'explanations': ['because', 'therefore', 'as a result', 'consequently', 'due to'],
                'examples': ['for example', 'such as', 'like', 'including', 'namely'],
                'processes': ['first', 'then', 'next', 'finally', 'steps', 'process'],
                'comparisons': ['compared to', 'versus', 'different from', 'similar to', 'unlike']
            }
            
            # Count educational indicators
            indicator_count = 0
            for category, phrases in educational_indicators.items():
                if any(phrase in transcript_text.lower() for phrase in phrases):
                    indicator_count += 1
            
            # Extract key terms with better filtering
            words = re.findall(r'\b[A-Za-z]+(?:\s+[A-Za-z]+){0,2}\b', transcript_text)
            
            # Enhanced filtering for educational content
            filler_words = {
                'okay', 'today', 'yeah', 'um', 'uh', 'like', 'so', 'well', 'now', 'then',
                'this', 'that', 'what', 'when', 'where', 'how', 'why', 'the', 'and', 'but', 
                'for', 'you', 'we', 'they', 'have', 'will', 'can', 'could', 'would', 'should',
                'just', 'really', 'very', 'much', 'many', 'some', 'all', 'any', 'each', 'every'
            }
            
            # Look for educational terms (longer, technical-sounding words)
            educational_terms = []
            for word in words:
                clean_word = word.strip().lower()
                if (len(clean_word) > 4 and 
                    clean_word not in filler_words and 
                    not clean_word.isdigit() and
                    clean_word.isalpha()):
                    
                    # Prefer terms that sound technical/educational
                    if (any(edu_term in clean_word for edu_term in 
                           ['tion', 'ment', 'ness', 'ity', 'ism', 'ogy', 'ics', 'sis', 'logy']) or
                        len(clean_word) > 6):
                        educational_terms.append(word.strip())
            
            # Remove duplicates and limit
            concepts = list(set(educational_terms))[:10]
            
            analysis['topics'] = concepts[:5]  # Top 5 as topics
            analysis['concepts'] = concepts
            analysis['learning_objectives'] = f"Understand key concepts: {', '.join(concepts[:3])}" if concepts else "General educational content"
            analysis['educational_indicators'] = indicator_count
            analysis['content_quality'] = min(0.3 + (len(concepts) * 0.1) + (indicator_count * 0.05), 0.8)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in rule-based concept extraction: {str(e)}")
            return {'topics': [], 'concepts': [], 'content_quality': 0.0}
    
    def _analyze_frame_with_vlm(self, frame: np.ndarray, transcript_context: str) -> Optional[Dict]:
        """Analyze frame using VLM with transcript context"""
        try:
            # Encode frame
            frame_b64 = self._encode_frame_base64(frame)
            if not frame_b64:
                return None
            
            # Create contextual prompt
            prompt = f"""
Analyze this educational video frame with the following transcript context:
"{transcript_context}"

Extract:
1. VISUAL ELEMENTS: Describe any diagrams, charts, equations, text, or educational graphics visible
2. TOPICS: List 3-5 key educational topics shown in the frame
3. CONCEPTS: Identify specific concepts, terms, or ideas visible
4. EDUCATIONAL VALUE: Rate how suitable this frame is for generating educational questions (1-10)
5. COMPLEXITY LEVEL: Rate the complexity (beginner/intermediate/advanced)

Focus on content that can be used to create meaningful educational questions.
Be specific and factual in your analysis.
"""

            # Call VLM
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.vlm_model,
                    "prompt": prompt,
                    "images": [frame_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_k": 10,
                        "top_p": 0.8
                    }
                },
                timeout=90  # Increased timeout to 90 seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                if analysis_text and len(analysis_text) > 30:
                    parsed_analysis = self._parse_frame_analysis(analysis_text)
                    # Add raw analysis text for detailed tracking
                    parsed_analysis['raw_analysis'] = analysis_text
                    return parsed_analysis
                    
        except Exception as e:
            logger.error(f"VLM frame analysis error: {str(e)}")
        
        return None
    
    def _encode_frame_base64(self, frame: np.ndarray) -> Optional[str]:
        """Encode frame as base64 for VLM"""
        try:
            # Resize if too large
            height, width = frame.shape[:2]
            if width > 800:
                scale = 800 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return base64.b64encode(buffer).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Frame encoding error: {str(e)}")
            return None
    
    def _parse_frame_analysis(self, analysis_text: str) -> Dict:
        """Parse VLM analysis into structured data"""
        try:
            analysis = {'topics': [], 'concepts': [], 'visual_elements': ''}
            
            # Extract visual elements
            visual_match = re.search(r'(?:VISUAL ELEMENTS|visual elements)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)', 
                                   analysis_text, re.IGNORECASE | re.MULTILINE)
            if visual_match:
                analysis['visual_elements'] = visual_match.group(1).strip()
            
            # Extract topics
            topics_match = re.search(r'(?:TOPICS|topics)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)', 
                                   analysis_text, re.IGNORECASE | re.MULTILINE)
            if topics_match:
                topics_text = topics_match.group(1).strip()
                topics = [t.strip() for t in re.split(r'[,;]\s*|\d+\.\s*', topics_text) if t.strip()]
                analysis['topics'] = topics[:5]
            
            # Extract concepts
            concepts_match = re.search(r'(?:CONCEPTS|concepts)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)', 
                                     analysis_text, re.IGNORECASE | re.MULTILINE)
            if concepts_match:
                concepts_text = concepts_match.group(1).strip()
                concepts = [c.strip() for c in re.split(r'[,;]\s*|\d+\.\s*', concepts_text) if c.strip()]
                analysis['concepts'] = concepts[:7]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing frame analysis: {str(e)}")
            return {'topics': [], 'concepts': [], 'visual_elements': ''}
    
    def _generate_tiered_questions(self, educational_analysis: Dict, segment: Dict, 
                                  target_count: int) -> List[Dict]:
        """
        Generate Easy/Medium/Hard questions for the educational content
        """
        try:
            questions = []
            topics = educational_analysis.get('topics', [])
            concepts = educational_analysis.get('concepts', [])
            visual_elements = educational_analysis.get('visual_elements', '')
            
            if not topics and not concepts:
                logger.warning("No topics or concepts found for question generation")
                return []
            
            # Ensure we have content to work with
            primary_topic = topics[0] if topics else concepts[0] if concepts else "the content"
            
            # Generate questions for each difficulty tier
            difficulties = ['easy', 'medium', 'hard']
            questions_per_difficulty = max(1, target_count // len(difficulties))
            
            for difficulty in difficulties:
                tier_config = self.DIFFICULTY_TIERS[difficulty]
                
                # Generate questions for this difficulty level
                for i in range(questions_per_difficulty):
                    question_type = random.choice(tier_config['question_types'])
                    
                    if question_type == 'mcq':
                        question = self._generate_strategic_mcq(
                            difficulty, primary_topic, concepts, visual_elements, educational_analysis
                        )
                    elif question_type == 'msq':
                        question = self._generate_strategic_msq(
                            difficulty, primary_topic, concepts, visual_elements, educational_analysis
                        )
                    elif question_type == 'nat':
                        question = self._generate_strategic_nat(
                            difficulty, primary_topic, visual_elements, educational_analysis
                        )
                    elif question_type == 'true_false':
                        question = self._generate_strategic_tf(
                            difficulty, primary_topic, concepts, educational_analysis
                        )
                    else:
                        question = self._generate_strategic_factual(
                            difficulty, primary_topic, concepts, educational_analysis
                        )
                    
                    if question:
                        # Add strategic metadata
                        question.update({
                            'strategic_difficulty': difficulty,
                            'cognitive_level': random.choice(tier_config['cognitive_levels']),
                            'complexity': tier_config['complexity'],
                            'tier_description': tier_config['description']
                        })
                        questions.append(question)
                        
                        if len(questions) >= target_count:
                            break
                
                if len(questions) >= target_count:
                    break
            
            logger.debug(f"Generated {len(questions)} tiered questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating tiered questions: {str(e)}")
            return []
    
    def _generate_strategic_mcq(self, difficulty: str, topic: str, concepts: List[str], 
                              visual_elements: str, analysis: Dict) -> Optional[Dict]:
        """Generate contextually relevant MCQ using actual content understanding"""
        try:
            # Get actual transcript content for context
            transcript_text = analysis.get('segment_text', analysis.get('transcript_text', ''))
            
            # Use LLM to generate meaningful questions based on actual content
            prompt = f"""
You are creating educational questions for a statistics/research methods course about correlation vs causation.

Based on this actual lecture transcript:
"{transcript_text}"

Visual context: {visual_elements}
Key concepts from content: {', '.join(concepts)}

Generate a {difficulty}-level multiple choice question that tests understanding of correlation, causation, statistical relationships, or research methodology based on what's actually discussed.

{difficulty} level requirements:
- Easy: Test basic understanding of definitions and concepts mentioned
- Medium: Test application of concepts to scenarios or examples given
- Hard: Test critical evaluation of relationships and methodology

Create a specific question about the content discussed, not generic templates. Focus on:
- Correlation vs causation concepts
- Statistical relationships
- Research methodology
- Hypothesis testing
- Data interpretation

Format as JSON:
{{
    "question": "Specific question based on actual content",
    "correct_answer": "A", 
    "options": [
        "Correct answer with specific details from content",
        "Plausible wrong answer based on common misconceptions",
        "Another plausible distractor", 
        "Third distractor option"
    ],
    "explanation": "Brief explanation of correct answer"
}}

Make it educational and specific to correlation/causation topics discussed.
"""

            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.llm_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '')
                    
                    # Try to extract JSON
                    import json
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        question_data = json.loads(json_match.group())
                        
                        question_text = question_data.get('question', '')
                        options = question_data.get('options', [])
                        
                        # Validate that we got good content
                        if (len(question_text) > 20 and len(options) >= 4 and 
                            'key concept discussed' not in question_text.lower() and
                            'educational content' not in question_text.lower()):
                            
                            correct_answer = question_data.get('correct_answer', 'A')
                            correct_index = ord(correct_answer.upper()) - ord('A') if correct_answer else 0
                            
                            return {
                                'text': question_text,
                                'answer': correct_answer,
                                'detailed_answer': question_data.get('explanation', options[correct_index]),
                                'options': options,
                                'type': 'mcq',
                                'difficulty': difficulty,
                                'topic': topic,
                                'confidence': 0.9,
                                'strategic_difficulty': difficulty,
                                'cognitive_level': self._get_cognitive_level(difficulty),
                                'complexity': self._get_complexity(difficulty),
                                'tier_description': self.DIFFICULTY_TIERS[difficulty]['description']
                            }
                        else:
                            logger.warning("LLM generated generic question, falling back")
            except Exception as e:
                logger.warning(f"LLM question generation failed: {str(e)}")
            
            # If LLM fails or generates poor content, return None instead of generic fallback
            logger.warning(f"Skipping generic question generation for topic: {topic}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating strategic MCQ: {str(e)}")
            return None
    
    def _generate_strategic_msq(self, difficulty: str, topic: str, concepts: List[str], 
                              visual_elements: str, analysis: Dict) -> Optional[Dict]:
        """Generate MSQ based on strategic difficulty"""
        try:
            if len(concepts) < 2:
                return None
                
            if difficulty == 'easy':
                question_text = f"Which of the following are mentioned in relation to {topic}? (Select all that apply)"
                correct_statements = [f"{concept} is discussed" for concept in concepts[:3]]
                
            elif difficulty == 'medium':
                question_text = f"Which statements correctly describe the characteristics of {topic}? (Select all that apply)"
                concept_statements = [f"{concept} relates to {topic}" for concept in concepts[:2]]
                correct_statements = [f"{topic} is relevant to the educational objectives"] + concept_statements
                correct_statements = correct_statements[:3]
                
            else:
                question_text = f"Analyze the relationships shown. Which statements represent valid conclusions about {topic}? (Select all that apply)"
                correct_statements = [
                    f"{topic} demonstrates complex interactions with related concepts",
                    f"The analysis reveals multiple dimensions of {topic}",
                    f"{concepts[0]} and {topic} show interconnected relationships" if concepts else f"{topic} has multifaceted implications"
                ]
            
            # Generate distractors
            distractors = [
                f"{topic} is not addressed in this content",
                f"The relationship with {topic} contradicts established theory",
                f"No clear evidence supports {topic} in this context"
            ]
            
            # Combine and shuffle
            all_options = correct_statements + distractors[:2]
            random.shuffle(all_options)
            
            # Find correct indices
            correct_indices = [i for i, option in enumerate(all_options) if option in correct_statements]
            correct_answers = [chr(65 + i) for i in correct_indices]
            
            return {
                'text': question_text,
                'answer': ', '.join(correct_answers),
                'detailed_answer': '; '.join(correct_statements),
                'options': all_options,
                'type': 'msq',
                'correct_count': len(correct_answers),
                'difficulty': difficulty,
                'topic': topic,
                'confidence': 0.80
            }
            
        except Exception as e:
            logger.error(f"Error generating strategic MSQ: {str(e)}")
            return None
    
    def _generate_strategic_nat(self, difficulty: str, topic: str, visual_elements: str, 
                              analysis: Dict) -> Optional[Dict]:
        """Generate NAT based on strategic difficulty"""
        try:
            # Look for numbers in visual elements or generate contextual numbers
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', visual_elements + str(analysis))
            
            if numbers:
                number = numbers[0]
                context = "the value shown"
            else:
                # Generate contextual numerical question
                if difficulty == 'easy':
                    number = "3"
                    context = "key components"
                elif difficulty == 'medium':
                    number = "5"
                    context = "main factors"
                else:
                    number = "7"
                    context = "critical elements"
            
            if difficulty == 'easy':
                question_text = f"How many {context} are mentioned in relation to {topic}?"
            elif difficulty == 'medium':
                question_text = f"Calculate the number of {context} that directly influence {topic}."
            else:
                question_text = f"Analyze and determine the total number of {context} that contribute to the complex understanding of {topic}."
            
            return {
                'text': question_text,
                'answer': number,
                'detailed_answer': f"The answer is {number} based on the analysis of {context} related to {topic}",
                'type': 'nat',
                'numeric_answer': float(number),
                'difficulty': difficulty,
                'topic': topic,
                'confidence': 0.70
            }
            
        except Exception as e:
            logger.error(f"Error generating strategic NAT: {str(e)}")
            return None
    
    def _generate_strategic_tf(self, difficulty: str, topic: str, concepts: List[str], 
                             analysis: Dict) -> Optional[Dict]:
        """Generate True/False based on strategic difficulty"""
        try:
            is_true = random.choice([True, False])
            
            if difficulty == 'easy':
                if is_true:
                    statement = f"{topic} is discussed in the educational content"
                    answer = "True"
                    explanation = f"True. {topic} is indeed mentioned and discussed in the content."
                else:
                    statement = f"{topic} is completely unrelated to the educational content"
                    answer = "False"
                    explanation = f"False. {topic} is actually relevant and discussed in the educational content."
                    
            elif difficulty == 'medium':
                if is_true:
                    statement = f"{topic} demonstrates practical applications in the context presented"
                    answer = "True"
                    explanation = f"True. The content shows how {topic} can be applied practically."
                else:
                    statement = f"{topic} has no practical relevance to the concepts discussed"
                    answer = "False"
                    explanation = f"False. {topic} actually has significant practical relevance to the educational objectives."
                    
            else:
                if is_true:
                    statement = f"The analysis of {topic} reveals complex interdependencies with related educational concepts"
                    answer = "True"
                    explanation = f"True. {topic} shows sophisticated relationships with other concepts in the educational framework."
                else:
                    statement = f"{topic} operates independently without connection to other educational elements discussed"
                    answer = "False"
                    explanation = f"False. {topic} is actually interconnected with multiple educational elements and concepts."
            
            return {
                'text': f"True or False: {statement}",
                'answer': answer,
                'detailed_answer': explanation,
                'type': 'true_false',
                'difficulty': difficulty,
                'topic': topic,
                'confidence': 0.75
            }
            
        except Exception as e:
            logger.error(f"Error generating strategic T/F: {str(e)}")
            return None
    
    def _generate_strategic_factual(self, difficulty: str, topic: str, concepts: List[str], 
                                  analysis: Dict) -> Optional[Dict]:
        """Generate factual question based on strategic difficulty"""
        try:
            if difficulty == 'easy':
                question_text = f"What is {topic}?"
                answer = f"{topic} is a fundamental concept discussed in the educational content with clear relevance to the learning objectives."
                
            elif difficulty == 'medium':
                question_text = f"Explain how {topic} contributes to the overall understanding of the subject matter."
                answer = f"{topic} contributes by providing essential knowledge that connects with other concepts and enables deeper comprehension of the educational material."
                
            else:
                question_text = f"Critically analyze the role of {topic} in the broader educational context and evaluate its significance."
                answer = f"{topic} plays a crucial role in the educational framework by serving as a foundational element that enables advanced understanding, connects multiple concepts, and provides practical applications for real-world scenarios."
            
            return {
                'text': question_text,
                'answer': answer,
                'detailed_answer': answer,
                'type': 'factual',
                'difficulty': difficulty,
                'topic': topic,
                'confidence': 0.75
            }
            
        except Exception as e:
            logger.error(f"Error generating strategic factual: {str(e)}")
            return None
    
    def _generate_strategic_distractors(self, correct_answer: str, topic: str, 
                                      concepts: List[str], difficulty: str) -> List[str]:
        """Generate difficulty-appropriate distractors"""
        distractors = []
        
        if difficulty == 'easy':
            # Simple, obviously wrong distractors
            distractors.extend([
                f"{topic} is not mentioned in the content",
                f"{topic} is irrelevant to education",
                f"No information is provided about {topic}"
            ])
        elif difficulty == 'medium':
            # Plausible but incorrect distractors
            distractors.extend([
                f"{topic} contradicts the established educational principles",
                f"{topic} requires additional research to understand fully",
                f"{topic} is only theoretical without practical application"
            ])
        else:
            # Sophisticated distractors requiring careful analysis
            distractors.extend([
                f"{topic} represents a paradigm shift that challenges traditional understanding",
                f"{topic} introduces complexity that may obscure rather than clarify the educational objectives",
                f"{topic} demonstrates limitations in the current educational framework"
            ])
        
        return distractors[:3]
    
    def _optimize_question_distribution(self, questions: List[Dict]) -> List[Dict]:
        """Optimize question distribution across difficulties and types"""
        try:
            # Count by difficulty
            difficulty_counts = {'easy': 0, 'medium': 0, 'hard': 0}
            type_counts = {}
            
            for question in questions:
                difficulty = question.get('strategic_difficulty', 'medium')
                q_type = question.get('type', 'factual')
                
                difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
                type_counts[q_type] = type_counts.get(q_type, 0) + 1
            
            logger.info(f"📊 Question Distribution:")
            logger.info(f"   Difficulty: {difficulty_counts}")
            logger.info(f"   Types: {type_counts}")
            
            # Sort by confidence and balance
            questions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error optimizing distribution: {str(e)}")
            return questions
