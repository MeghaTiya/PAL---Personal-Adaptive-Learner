#!/usr/bin/env python3
"""
Frame-by-Frame VLM Question Generator
Analyzes video frames with VLM to generate contextually aligned questions
"""

import cv2
import base64
import logging
import requests
import json
import re
import numpy as np
from typing import Dict, List, Optional, Tuple
import tempfile
import os
from datetime import timedelta

logger = logging.getLogger(__name__)

class FrameBasedQuestionGenerator:
    """
    Generate questions by analyzing video frames with VLM
    """
    
    def __init__(self, ollama_url="http://localhost:11434", vlm_model="llava:7b"):
        self.ollama_url = ollama_url
        self.vlm_model = vlm_model
        self.available = self._check_vlm_availability()
        
        # Frame analysis parameters
        self.frame_interval = 30  # Analyze every 30 frames (1 second at 30fps)
        self.similarity_threshold = 0.15  # Threshold for detecting slide changes
        self.min_content_confidence = 0.7  # Minimum confidence for generating questions
        
        # Question generation parameters
        self.question_types = ['mcq', 'msq', 'nat', 'short_answer', 'true_false']
        self.max_questions_per_slide = 3
        
    def _check_vlm_availability(self) -> bool:
        """Check if VLM is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                return self.vlm_model in available_models
            return False
        except:
            return False
    
    def generate_questions_from_video(self, video_path: str, num_questions: int = 150) -> List[Dict]:
        """
        Main method to generate questions from video using frame analysis
        
        Args:
            video_path: Path to video file
            num_questions: Target number of questions
            
        Returns:
            List of generated questions with metadata
        """
        if not self.available:
            logger.error("VLM not available for frame analysis")
            return []
        
        try:
            logger.info(f"Starting frame-by-frame analysis of {video_path}")
            
            # Step 1: Extract key frames
            key_frames = self._extract_key_frames(video_path)
            logger.info(f"Extracted {len(key_frames)} key frames")
            
            # Step 2: Analyze each frame with VLM
            frame_analyses = []
            for i, (frame_data, timestamp) in enumerate(key_frames):
                logger.info(f"Analyzing frame {i+1}/{len(key_frames)} at {timestamp}")
                analysis = self._analyze_frame_with_vlm(frame_data, timestamp)
                if analysis:
                    frame_analyses.append(analysis)
            
            logger.info(f"Successfully analyzed {len(frame_analyses)} frames")
            
            # Step 3: Generate questions from frame analyses
            all_questions = []
            questions_per_frame = max(1, num_questions // len(frame_analyses)) if frame_analyses else 0
            
            for analysis in frame_analyses:
                frame_questions = self._generate_questions_from_frame_analysis(
                    analysis, 
                    min(questions_per_frame, self.max_questions_per_slide)
                )
                all_questions.extend(frame_questions)
                
                if len(all_questions) >= num_questions:
                    break
            
            # Step 4: Post-process and rank questions
            ranked_questions = self._rank_and_filter_questions(all_questions, num_questions)
            
            logger.info(f"Generated {len(ranked_questions)} high-quality questions")
            return ranked_questions
            
        except Exception as e:
            logger.error(f"Error in frame-based question generation: {str(e)}")
            return []
    
    def _extract_key_frames(self, video_path: str) -> List[Tuple[np.ndarray, str]]:
        """
        Extract key frames from video by detecting content changes
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            key_frames = []
            prev_frame = None
            frame_count = 0
            
            logger.info(f"Processing video: {total_frames} frames at {fps} fps")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every nth frame based on interval
                if frame_count % self.frame_interval == 0:
                    # Convert to grayscale for comparison
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Check if this frame is significantly different from previous
                    if self._is_key_frame(gray_frame, prev_frame):
                        timestamp = self._frame_to_timestamp(frame_count, fps)
                        key_frames.append((frame, timestamp))
                        prev_frame = gray_frame
                        logger.debug(f"Key frame detected at {timestamp}")
                
                frame_count += 1
                
                # Progress logging
                if frame_count % 1000 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"Processing frames: {progress:.1f}% complete")
            
            cap.release()
            logger.info(f"Extracted {len(key_frames)} key frames from video")
            return key_frames
            
        except Exception as e:
            logger.error(f"Error extracting key frames: {str(e)}")
            return []
    
    def _is_key_frame(self, current_frame: np.ndarray, prev_frame: np.ndarray) -> bool:
        """
        Determine if current frame is a key frame (significant change from previous)
        """
        if prev_frame is None:
            return True
        
        try:
            # Calculate structural similarity
            diff = cv2.absdiff(current_frame, prev_frame)
            non_zero_count = np.count_nonzero(diff)
            total_pixels = diff.size
            
            change_ratio = non_zero_count / total_pixels
            return change_ratio > self.similarity_threshold
            
        except Exception:
            return True  # If comparison fails, treat as key frame
    
    def _frame_to_timestamp(self, frame_number: int, fps: float) -> str:
        """Convert frame number to timestamp string"""
        seconds = frame_number / fps
        td = timedelta(seconds=seconds)
        
        hours = int(td.seconds // 3600)
        minutes = int((td.seconds % 3600) // 60)
        secs = int(td.seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _analyze_frame_with_vlm(self, frame: np.ndarray, timestamp: str) -> Optional[Dict]:
        """
        Analyze a single frame with VLM to extract educational content
        """
        try:
            # Encode frame as base64
            frame_b64 = self._encode_frame_base64(frame)
            if not frame_b64:
                return None
            
            # Create educational analysis prompt
            prompt = """
Analyze this educational video frame and extract key learning content. Identify:

1. MAIN TOPIC: What is the primary subject being discussed?
2. KEY CONCEPTS: List 3-5 important concepts, terms, or ideas shown
3. VISUAL ELEMENTS: Describe charts, diagrams, equations, or text visible
4. LEARNING OBJECTIVES: What should students learn from this content?
5. QUESTION OPPORTUNITIES: What types of questions could test understanding?
6. DIFFICULTY LEVEL: Rate content difficulty (beginner/intermediate/advanced)
7. CONTENT TYPE: Is this definition, explanation, example, or demonstration?

Focus on extracting specific, factual information that can be used to create educational questions.
Be precise and detailed in your analysis.
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
                        "temperature": 0.3,
                        "top_k": 10,
                        "top_p": 0.9
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                if analysis_text and len(analysis_text) > 50:
                    # Parse the analysis into structured data
                    parsed_analysis = self._parse_vlm_analysis(analysis_text, timestamp)
                    parsed_analysis['raw_frame'] = frame
                    return parsed_analysis
                else:
                    logger.warning(f"VLM analysis too short for frame at {timestamp}")
                    return None
            else:
                logger.error(f"VLM API error for frame at {timestamp}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing frame at {timestamp}: {str(e)}")
            return None
    
    def _encode_frame_base64(self, frame: np.ndarray) -> Optional[str]:
        """Encode frame as base64 string"""
        try:
            # Resize frame if too large (for API efficiency)
            height, width = frame.shape[:2]
            if width > 1024:
                scale = 1024 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            return frame_b64
            
        except Exception as e:
            logger.error(f"Error encoding frame: {str(e)}")
            return None
    
    def _parse_vlm_analysis(self, analysis_text: str, timestamp: str) -> Dict:
        """
        Parse VLM analysis text into structured data
        """
        try:
            # Extract sections using regex patterns
            sections = {}
            
            patterns = {
                'main_topic': r'(?:MAIN TOPIC|main topic)[:\s]+([^\n]+)',
                'key_concepts': r'(?:KEY CONCEPTS|key concepts)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)',
                'visual_elements': r'(?:VISUAL ELEMENTS|visual elements)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)',
                'learning_objectives': r'(?:LEARNING OBJECTIVES|learning objectives)[:\s]+([^\n]+(?:\n[^\n]*)*?)(?=\n\d\.|\n[A-Z]|\Z)',
                'difficulty_level': r'(?:DIFFICULTY LEVEL|difficulty level)[:\s]+([^\n]+)',
                'content_type': r'(?:CONTENT TYPE|content type)[:\s]+([^\n]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE)
                sections[key] = match.group(1).strip() if match else ""
            
            # Extract concepts as list
            concepts_text = sections.get('key_concepts', '')
            concepts = [c.strip() for c in re.split(r'[,;]\s*|\d+\.\s*', concepts_text) if c.strip()]
            
            return {
                'timestamp': timestamp,
                'main_topic': sections.get('main_topic', 'Unknown Topic'),
                'key_concepts': concepts,
                'visual_elements': sections.get('visual_elements', ''),
                'learning_objectives': sections.get('learning_objectives', ''),
                'difficulty_level': sections.get('difficulty_level', 'intermediate'),
                'content_type': sections.get('content_type', 'explanation'),
                'raw_analysis': analysis_text,
                'confidence': self._assess_analysis_confidence(analysis_text)
            }
            
        except Exception as e:
            logger.error(f"Error parsing VLM analysis: {str(e)}")
            return {
                'timestamp': timestamp,
                'main_topic': 'Analysis Error',
                'key_concepts': [],
                'confidence': 0.0,
                'raw_analysis': analysis_text
            }
    
    def _assess_analysis_confidence(self, analysis_text: str) -> float:
        """
        Assess confidence in VLM analysis based on content quality
        """
        try:
            # Simple heuristics for confidence assessment
            confidence = 0.5  # Base confidence
            
            # Length bonus
            if len(analysis_text) > 200:
                confidence += 0.2
            
            # Educational terms bonus
            edu_terms = ['concept', 'theory', 'principle', 'definition', 'example', 'explanation', 'diagram', 'chart', 'equation', 'formula']
            term_count = sum(1 for term in edu_terms if term in analysis_text.lower())
            confidence += min(term_count * 0.05, 0.3)
            
            # Structure bonus (if sections are identified)
            sections = ['topic', 'concept', 'objective', 'visual', 'difficulty']
            section_count = sum(1 for section in sections if section in analysis_text.lower())
            confidence += min(section_count * 0.04, 0.2)
            
            return min(confidence, 1.0)
            
        except:
            return 0.5
    
    def _generate_questions_from_frame_analysis(self, analysis: Dict, num_questions: int) -> List[Dict]:
        """
        Generate questions from a single frame analysis
        """
        try:
            if analysis.get('confidence', 0) < self.min_content_confidence:
                logger.debug(f"Skipping low-confidence frame at {analysis.get('timestamp')}")
                return []
            
            questions = []
            concepts = analysis.get('key_concepts', [])
            main_topic = analysis.get('main_topic', '')
            visual_elements = analysis.get('visual_elements', '')
            
            if not concepts and not main_topic:
                logger.debug(f"No concepts found in frame at {analysis.get('timestamp')}")
                return []
            
            # Generate different types of questions
            for i in range(num_questions):
                question_type = self.question_types[i % len(self.question_types)]
                
                if question_type == 'mcq':
                    question = self._generate_frame_mcq(analysis, concepts, main_topic)
                elif question_type == 'msq':
                    question = self._generate_frame_msq(analysis, concepts, main_topic)
                elif question_type == 'nat':
                    question = self._generate_frame_nat(analysis, visual_elements)
                elif question_type == 'true_false':
                    question = self._generate_frame_tf(analysis, concepts, main_topic)
                else:
                    question = self._generate_frame_short_answer(analysis, concepts, main_topic)
                
                if question:
                    question.update({
                        'timestamp': analysis.get('timestamp'),
                        'frame_confidence': analysis.get('confidence', 0),
                        'source': 'frame_analysis'
                    })
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions from frame analysis: {str(e)}")
            return []
    
    def _generate_frame_mcq(self, analysis: Dict, concepts: List[str], main_topic: str) -> Optional[Dict]:
        """Generate MCQ from frame analysis"""
        if not concepts and not main_topic:
            return None
        
        try:
            concept = concepts[0] if concepts else main_topic
            visual_info = analysis.get('visual_elements', '')
            
            # Create contextual question
            if 'diagram' in visual_info.lower() or 'chart' in visual_info.lower():
                question_text = f"Based on the visual representation shown, what does {concept} demonstrate?"
            elif 'equation' in visual_info.lower() or 'formula' in visual_info.lower():
                question_text = f"In the equation shown, what role does {concept} play?"
            else:
                question_text = f"According to the slide content, what is the key characteristic of {concept}?"
            
            # Generate answer from analysis
            correct_answer = self._extract_answer_from_analysis(analysis, concept)
            
            # Generate distractors
            distractors = self._generate_contextual_distractors(correct_answer, concept, analysis)
            
            # Create options
            options = [correct_answer] + distractors[:3]
            import random
            random.shuffle(options)
            correct_index = options.index(correct_answer)
            
            return {
                'text': question_text,
                'answer': chr(65 + correct_index),
                'detailed_answer': correct_answer,
                'options': options,
                'type': 'mcq',
                'difficulty': analysis.get('difficulty_level', 'intermediate'),
                'topic': concept,
                'confidence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error generating frame MCQ: {str(e)}")
            return None
    
    def _generate_frame_msq(self, analysis: Dict, concepts: List[str], main_topic: str) -> Optional[Dict]:
        """Generate MSQ from frame analysis"""
        if len(concepts) < 2:
            return None
        
        try:
            question_text = f"Which of the following are mentioned in relation to {main_topic}? (Select all that apply)"
            
            # Use concepts as correct answers
            correct_statements = [f"{concept} is a key component" for concept in concepts[:4]]
            
            # Generate distractors
            distractors = [
                f"{main_topic} is not relevant to this field",
                "This content is outdated information",
                "No clear relationship is established"
            ]
            
            # Combine options
            all_options = correct_statements + distractors[:2]
            import random
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
                'difficulty': 'medium',
                'topic': main_topic,
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"Error generating frame MSQ: {str(e)}")
            return None
    
    def _generate_frame_nat(self, analysis: Dict, visual_elements: str) -> Optional[Dict]:
        """Generate NAT from frame analysis (if numbers are present)"""
        try:
            # Look for numbers in visual elements or analysis
            import re
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', visual_elements + analysis.get('raw_analysis', ''))
            
            if not numbers:
                return None
            
            number = numbers[0]
            context = self._find_number_context_in_analysis(analysis, number)
            
            if context:
                return {
                    'text': f"What numerical value is associated with {context} in the content shown?",
                    'answer': number,
                    'detailed_answer': f"The value is {number} as shown in the visual content",
                    'type': 'nat',
                    'numeric_answer': float(number),
                    'difficulty': 'easy',
                    'topic': context,
                    'confidence': 0.6
                }
            
        except Exception as e:
            logger.error(f"Error generating frame NAT: {str(e)}")
        
        return None
    
    def _generate_frame_tf(self, analysis: Dict, concepts: List[str], main_topic: str) -> Optional[Dict]:
        """Generate True/False question from frame analysis"""
        if not concepts and not main_topic:
            return None
        
        try:
            concept = concepts[0] if concepts else main_topic
            
            # Create true statement from analysis
            true_statement = f"{concept} is a key element in {main_topic}"
            
            import random
            if random.choice([True, False]):
                # True question
                return {
                    'text': f"True or False: {true_statement}",
                    'answer': 'True',
                    'detailed_answer': f"True. {concept} is indeed discussed as an important element in the content.",
                    'type': 'true_false',
                    'difficulty': 'easy',
                    'topic': concept,
                    'confidence': 0.7
                }
            else:
                # False question
                false_statement = f"{concept} is irrelevant to {main_topic}"
                return {
                    'text': f"True or False: {false_statement}",
                    'answer': 'False',
                    'detailed_answer': f"False. {concept} is actually a relevant and important element in the discussion of {main_topic}.",
                    'type': 'true_false',
                    'difficulty': 'easy',
                    'topic': concept,
                    'confidence': 0.7
                }
                
        except Exception as e:
            logger.error(f"Error generating frame T/F: {str(e)}")
            return None
    
    def _generate_frame_short_answer(self, analysis: Dict, concepts: List[str], main_topic: str) -> Optional[Dict]:
        """Generate short answer question from frame analysis"""
        if not concepts and not main_topic:
            return None
        
        try:
            concept = concepts[0] if concepts else main_topic
            
            question_text = f"Explain the significance of {concept} in the context shown."
            answer = self._extract_answer_from_analysis(analysis, concept)
            
            return {
                'text': question_text,
                'answer': answer,
                'detailed_answer': answer,
                'type': 'short_answer',
                'difficulty': analysis.get('difficulty_level', 'intermediate'),
                'topic': concept,
                'confidence': 0.6
            }
            
        except Exception as e:
            logger.error(f"Error generating frame short answer: {str(e)}")
            return None
    
    def _extract_answer_from_analysis(self, analysis: Dict, concept: str) -> str:
        """Extract answer from VLM analysis"""
        try:
            raw_analysis = analysis.get('raw_analysis', '')
            learning_obj = analysis.get('learning_objectives', '')
            visual_elements = analysis.get('visual_elements', '')
            
            # Look for relevant information about the concept
            relevant_info = []
            
            if concept.lower() in raw_analysis.lower():
                # Find sentences containing the concept
                sentences = raw_analysis.split('.')
                for sentence in sentences:
                    if concept.lower() in sentence.lower():
                        relevant_info.append(sentence.strip())
            
            if relevant_info:
                return relevant_info[0]
            elif learning_obj:
                return learning_obj[:150] + "..." if len(learning_obj) > 150 else learning_obj
            elif visual_elements:
                return f"Key information about {concept} as shown in the visual content"
            else:
                return f"{concept} is a fundamental element discussed in this educational content"
                
        except:
            return f"Important concept related to {concept}"
    
    def _generate_contextual_distractors(self, correct_answer: str, concept: str, analysis: Dict) -> List[str]:
        """Generate contextual distractors based on frame analysis"""
        distractors = []
        
        # Generic academic distractors
        generic_options = [
            f"{concept} is not addressed in this content",
            f"The relationship with {concept} is unclear",
            f"{concept} contradicts established theories",
            f"Further research is needed on {concept}"
        ]
        
        distractors.extend(generic_options)
        
        # Create modified versions of correct answer
        if len(correct_answer) > 30:
            words = correct_answer.split()
            if len(words) > 5:
                # Create slightly modified version
                modified = words[:]
                modified[len(words)//2] = "alternative"
                distractors.append(' '.join(modified))
        
        return distractors[:3]
    
    def _find_number_context_in_analysis(self, analysis: Dict, number: str) -> Optional[str]:
        """Find context for a number in the analysis"""
        raw_text = analysis.get('raw_analysis', '') + ' ' + analysis.get('visual_elements', '')
        
        contexts = {
            'percentage': ['percent', '%', 'percentage'],
            'count': ['number', 'count', 'quantity', 'amount'],
            'measurement': ['value', 'measurement', 'size', 'length', 'width'],
            'score': ['score', 'rating', 'grade', 'result']
        }
        
        number_pos = raw_text.find(number)
        if number_pos == -1:
            return None
        
        # Get context around number
        start = max(0, number_pos - 50)
        end = min(len(raw_text), number_pos + 50)
        context_text = raw_text[start:end].lower()
        
        for context_type, keywords in contexts.items():
            if any(keyword in context_text for keyword in keywords):
                return context_type
        
        return "value"
    
    def _rank_and_filter_questions(self, questions: List[Dict], target_count: int) -> List[Dict]:
        """
        Rank questions by quality and filter to target count
        """
        try:
            # Score each question
            scored_questions = []
            for question in questions:
                score = self._score_question_quality(question)
                scored_questions.append((score, question))
            
            # Sort by score (highest first)
            scored_questions.sort(key=lambda x: x[0], reverse=True)
            
            # Return top questions
            return [q for _, q in scored_questions[:target_count]]
            
        except Exception as e:
            logger.error(f"Error ranking questions: {str(e)}")
            return questions[:target_count]
    
    def _score_question_quality(self, question: Dict) -> float:
        """
        Score question quality based on various factors
        """
        try:
            score = 0.0
            
            # Base score from confidence
            score += question.get('confidence', 0) * 30
            score += question.get('frame_confidence', 0) * 20
            
            # Question text quality
            question_text = question.get('text', '')
            if len(question_text) > 20:
                score += 10
            if len(question_text.split()) >= 8:
                score += 10
            
            # Answer quality
            answer = question.get('detailed_answer', '')
            if len(answer) > 30:
                score += 10
            
            # Question type bonus
            q_type = question.get('type', '')
            type_bonuses = {'mcq': 15, 'msq': 10, 'true_false': 8, 'nat': 12, 'short_answer': 5}
            score += type_bonuses.get(q_type, 0)
            
            # Difficulty appropriateness
            difficulty = question.get('difficulty', 'medium')
            if difficulty in ['easy', 'intermediate', 'medium']:
                score += 5
            
            return min(score, 100.0)
            
        except:
            return 50.0  # Default medium score
