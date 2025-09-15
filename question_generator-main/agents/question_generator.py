"""
Agent 3: Question Generator
Enhanced with frame-by-frame VLM analysis for better question-content alignment
"""

import logging
import re
from typing import Dict, Any, List, Optional
import random
import os
from .frame_based_question_generator import FrameBasedQuestionGenerator
from .video_processor import VideoProcessor

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Enhanced question generator with frame-by-frame VLM analysis capability
    """
    
    def __init__(self):
        # Traditional timestamp-based templates (fallback)
        self.factual_templates = [
            "What is {concept}?",
            "Define {concept}.",
            "What does {concept} mean?",
            "How is {concept} defined?",
            "What is the definition of {concept}?",
        ]
        
        self.conceptual_templates = [
            "Why is {concept} important?",
            "What is the purpose of {concept}?",
            "How does {concept} work?",
            "What are the key features of {concept}?",
            "Explain the significance of {concept}.",
        ]
        
        self.application_templates = [
            "How would you apply {concept} in practice?",
            "Give an example of how {concept} is used.",
            "What would happen if you used {concept}?",
            "How can {concept} be implemented?",
            "When would you use {concept}?",
            "What are practical applications of {concept}?",
            "How does {concept} solve real-world issues?",
            "In what situations is {concept} most useful?",
        ]
        
        # Initialize frame-based components
        self.frame_generator = FrameBasedQuestionGenerator()
        self.video_processor = VideoProcessor()
        
        # NEW: Initialize strategic generator for hybrid frame+transcript approach
        from .strategic_question_generator import StrategicQuestionGenerator
        self.strategic_generator = StrategicQuestionGenerator()
        
        # Analysis modes
        self.ANALYSIS_MODES = {
            'timestamp_based': 'Traditional timestamp-based analysis',
            'frame_based': 'Frame-by-frame VLM analysis',
            'hybrid': 'Combined timestamp and frame analysis',
            'strategic_hybrid': 'Strategic 3-tier questions per validated timestamp'  # NEW
        }
        
        logger.info("QuestionGenerator initialized with frame-based VLM capabilities")
    
    def generate_questions(self, context: dict, num_questions: int = 5, include_mcq: bool = True, 
                          analysis_mode: str = 'strategic_hybrid', video_path: str = None) -> list:
        """
        Generate questions using either timestamp-based or frame-based analysis
        
        Args:
            context: Context dictionary from validator
            num_questions: Number of questions to generate
            include_mcq: Whether to include MCQ/MSQ/NAT questions
            analysis_mode: 'timestamp_based', 'frame_based', or 'hybrid'
            video_path: Path to video file (required for frame_based analysis)
            
        Returns:
            List of generated questions with proper types and tagging
        """
        try:
            logger.info(f"🎯 Starting question generation: {num_questions} questions using {analysis_mode} analysis")
            
            # Check analysis mode and prerequisites
            if analysis_mode in ['frame_based', 'hybrid', 'strategic_hybrid']:
                if not video_path or not os.path.exists(video_path):
                    logger.warning("❌ Video path required for frame-based analysis, falling back to timestamp-based")
                    analysis_mode = 'timestamp_based'
                elif analysis_mode == 'strategic_hybrid' and not self.strategic_generator.vlm_available:
                    logger.warning("❌ VLM not available for strategic hybrid analysis, falling back to timestamp-based")
                    analysis_mode = 'timestamp_based'
                elif analysis_mode in ['frame_based', 'hybrid'] and not self.frame_generator.available:
                    logger.warning("❌ VLM not available for frame-based analysis, falling back to timestamp-based")
                    analysis_mode = 'timestamp_based'
                else:
                    logger.info("✅ VLM available for advanced analysis")
            
            # Route to appropriate generation method
            if analysis_mode == 'strategic_hybrid':
                return self._generate_questions_strategic_hybrid(context, video_path, num_questions)
            elif analysis_mode == 'frame_based':
                return self._generate_questions_frame_based(video_path, num_questions)
            elif analysis_mode == 'hybrid':
                return self._generate_questions_hybrid(context, video_path, num_questions)
            else:
                return self._generate_questions_timestamp_based(context, num_questions, include_mcq)
                
        except Exception as e:
            logger.error(f"❌ Question generation failed: {str(e)}")
            return []
    
    def _generate_questions_strategic_hybrid(self, context: dict, video_path: str, num_questions: int) -> List[Dict]:
        """
        NEW: Strategic hybrid approach - Generate Easy/Medium/Hard questions for each validated timestamp
        Uses Frame + Transcript analysis with 3-tier difficulty system
        """
        try:
            logger.info(f"🎯 Starting Strategic Hybrid Analysis")
            logger.info(f"📊 Target: {num_questions} total questions with 3-tier difficulty system")
            
            # Get validated segments from context
            segments = context.get('segments', [])
            if not segments:
                logger.warning("No segments available for strategic analysis")
                return []
            
            # Calculate how many segments we need to process
            # Each segment will generate 3 questions (Easy/Medium/Hard)
            questions_per_segment = 3
            target_segments = min(len(segments), num_questions // questions_per_segment)
            
            # Select best segments (longer content, meaningful text)
            validated_segments = self._select_best_segments(segments, target_segments)
            logger.info(f"🔍 Selected {len(validated_segments)} validated segments for strategic analysis")
            
            # Generate strategic questions using the specialized generator
            strategic_questions = self.strategic_generator.generate_strategic_questions(
                video_path,
                validated_segments,
                questions_per_segment
            )
            
            # Convert to expected format and add metadata
            formatted_questions = []
            for i, question in enumerate(strategic_questions):
                formatted_question = {
                    'question': question,
                    'timestamp': question.get('timestamp', '00:00:00'),
                    'segment_text': question.get('transcript_text', 'Strategic analysis content'),
                    'question_type': question.get('type', 'strategic'),
                    'analysis_mode': 'strategic_hybrid',
                    'source': 'strategic_frame_transcript_analysis',
                    'strategic_tier': question.get('strategic_difficulty', 'medium'),
                    'cognitive_level': question.get('cognitive_level', 'understand'),
                    'educational_confidence': question.get('educational_confidence', 0.7),
                    'tags': self._generate_strategic_tags(question)
                }
                formatted_questions.append(formatted_question)
            
            # Trim to requested count if needed
            if len(formatted_questions) > num_questions:
                formatted_questions = formatted_questions[:num_questions]
            
            logger.info(f"✅ Strategic hybrid generation complete: {len(formatted_questions)} questions")
            
            # Log distribution
            tier_counts = {}
            type_counts = {}
            for q in formatted_questions:
                tier = q.get('strategic_tier', 'unknown')
                q_type = q.get('question_type', 'unknown')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
                type_counts[q_type] = type_counts.get(q_type, 0) + 1
            
            logger.info(f"📊 Strategic Distribution - Tiers: {tier_counts}, Types: {type_counts}")
            
            return formatted_questions
            
        except Exception as e:
            logger.error(f"❌ Strategic hybrid generation failed: {str(e)}")
            return []
    
    def _select_best_segments(self, segments: List[Dict], target_count: int) -> List[Dict]:
        """
        Select the best segments for strategic question generation
        Based on content length, educational indicators, and timestamp distribution
        """
        try:
            # Score each segment
            scored_segments = []
            for segment in segments:
                score = self._score_segment_quality(segment)
                scored_segments.append((score, segment))
            
            # Sort by score (highest first)
            scored_segments.sort(key=lambda x: x[0], reverse=True)
            
            # Select top segments with some distribution across the video
            selected_segments = []
            timestamps_used = set()
            
            for score, segment in scored_segments:
                if len(selected_segments) >= target_count:
                    break
                
                # Ensure some temporal distribution
                timestamp = segment.get('timestamp', '00:00:00')
                time_key = timestamp[:5]  # First 5 chars (HH:MM)
                
                if time_key not in timestamps_used or len(selected_segments) < target_count // 2:
                    selected_segments.append(segment)
                    timestamps_used.add(time_key)
            
            # Fill remaining slots if needed
            remaining_needed = target_count - len(selected_segments)
            for score, segment in scored_segments:
                if remaining_needed <= 0:
                    break
                if segment not in selected_segments:
                    selected_segments.append(segment)
                    remaining_needed -= 1
            
            return selected_segments[:target_count]
            
        except Exception as e:
            logger.error(f"Error selecting best segments: {str(e)}")
            return segments[:target_count]
    
    def _score_segment_quality(self, segment: Dict) -> float:
        """Score segment quality for strategic question generation"""
        try:
            score = 0.0
            text = segment.get('text', '').lower()
            
            # Length bonus
            if len(text) > 100:
                score += 30
            elif len(text) > 50:
                score += 15
            elif len(text) > 20:
                score += 5
            
            # Educational content indicators
            educational_terms = ['define', 'explain', 'because', 'therefore', 'example', 'such as', 
                               'first', 'second', 'then', 'finally', 'important', 'key', 'concept']
            
            # Statistical/research method terms (specific to this content)
            domain_specific_terms = ['correlation', 'causation', 'causal', 'hypothesis', 'data', 
                                   'variable', 'relationship', 'statistic', 'analysis', 'study', 
                                   'research', 'factor', 'counterfactual', 'confounding', 'bias']
            
            educational_count = sum(1 for term in educational_terms if term in text)
            domain_count = sum(1 for term in domain_specific_terms if term in text)
            
            score += educational_count * 5
            score += domain_count * 10  # Higher bonus for domain-specific terms
            
            # Penalty for filler-heavy segments
            filler_words = ['okay', 'um', 'uh', 'like', 'you know', 'so', 'well']
            filler_count = sum(text.count(filler) for filler in filler_words)
            score -= min(filler_count * 2, 20)  # Cap penalty
            
            # Bonus for question-answer patterns
            if any(pattern in text for pattern in ['?', 'question', 'answer', 'what is', 'how', 'why']):
                score += 10
            
            return max(score, 0)  # Ensure non-negative
            
            # Question words (good for generating questions)
            question_indicators = ['what', 'how', 'why', 'when', 'where', 'which']
            question_count = sum(1 for word in question_indicators if word in text.lower())
            score += question_count * 2
            
            # Technical terms (proper nouns, capitalized words)
            technical_terms = len(re.findall(r'\b[A-Z][a-z]+\b', text))
            score += min(technical_terms * 1.5, 10)  # Cap at 10 points
            
            # Sentence structure (multiple sentences usually mean more content)
            sentence_count = len([s for s in text.split('.') if len(s.strip()) > 10])
            score += min(sentence_count * 2, 12)  # Cap at 12 points
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring segment: {str(e)}")
            return 10.0  # Default moderate score
    
    def _generate_strategic_tags(self, question: Dict) -> List[str]:
        """Generate tags for strategic questions"""
        try:
            tags = []
            
            # Strategic tier tag
            tier = question.get('strategic_difficulty', 'medium')
            tags.append(f"tier:{tier}")
            
            # Question type tag
            q_type = question.get('type', 'unknown')
            tags.append(f"type:{q_type}")
            
            # Cognitive level tag
            cognitive_level = question.get('cognitive_level', 'understand')
            tags.append(f"cognitive:{cognitive_level}")
            
            # Confidence tag
            confidence = question.get('confidence', 0.5)
            if confidence >= 0.8:
                tags.append("quality:high")
            elif confidence >= 0.6:
                tags.append("quality:medium")
            else:
                tags.append("quality:low")
            
            # Source tags
            tags.append("source:strategic_hybrid")
            tags.append("analysis:frame_transcript")
            
            # Topic tag
            topic = question.get('topic', '')
            if topic and len(topic) > 2:
                clean_topic = re.sub(r'[^a-zA-Z0-9_]', '_', topic.lower())
                tags.append(f"topic:{clean_topic}")
            
            return tags
            
        except Exception as e:
            logger.error(f"Error generating strategic tags: {str(e)}")
            return ["analysis:strategic_hybrid"]
    
    def _generate_questions_frame_based(self, video_path: str, num_questions: int) -> List[Dict]:
        """
        Generate questions using pure frame-by-frame VLM analysis
        """
        try:
            logger.info(f"🎬 Starting frame-based question generation from {video_path}")
            
            # Check video format
            if not self.video_processor.is_supported_format(video_path):
                logger.info("📹 Converting video to supported format...")
                converted_path = self.video_processor.convert_to_supported_format(video_path)
                if converted_path:
                    video_path = converted_path
                else:
                    logger.error("❌ Video conversion failed")
                    return []
            
            # Get video info
            video_info = self.video_processor.extract_video_info(video_path)
            logger.info(f"📊 Video info: {video_info.get('duration_seconds', 0):.1f}s, "
                       f"{video_info.get('fps', 0):.1f} fps, {video_info.get('total_frames', 0)} frames")
            
            # Generate questions using frame analysis
            questions = self.frame_generator.generate_questions_from_video(video_path, num_questions)
            
            logger.info(f"✅ Frame-based generation complete: {len(questions)} questions")
            
            # Convert to expected format and add metadata
            formatted_questions = []
            for i, question in enumerate(questions):
                formatted_question = {
                    'question': question,
                    'timestamp': question.get('timestamp', '00:00:00'),
                    'segment_text': f"Frame analysis at {question.get('timestamp', '00:00:00')}",
                    'question_type': question.get('type', 'unknown'),
                    'analysis_mode': 'frame_based',
                    'source': 'vlm_frame_analysis',
                    'tags': self._generate_frame_tags(question)
                }
                formatted_questions.append(formatted_question)
            
            return formatted_questions
            
        except Exception as e:
            logger.error(f"❌ Frame-based generation failed: {str(e)}")
            return []
    
    def _generate_questions_hybrid(self, context: dict, video_path: str, num_questions: int) -> List[Dict]:
        """
        Generate questions using combined timestamp and frame analysis
        """
        try:
            logger.info("🔄 Starting hybrid question generation")
            
            # Split questions between frame-based and timestamp-based
            frame_questions_count = int(num_questions * 0.7)  # 70% frame-based
            timestamp_questions_count = num_questions - frame_questions_count  # 30% timestamp-based
            
            logger.info(f"📊 Hybrid split: {frame_questions_count} frame-based, {timestamp_questions_count} timestamp-based")
            
            # Generate frame-based questions
            frame_questions = []
            if frame_questions_count > 0:
                frame_questions = self._generate_questions_frame_based(video_path, frame_questions_count)
            
            # Generate timestamp-based questions
            timestamp_questions = []
            if timestamp_questions_count > 0:
                timestamp_questions = self._generate_questions_timestamp_based(context, timestamp_questions_count, True)
                # Mark timestamp questions
                for q in timestamp_questions:
                    q['analysis_mode'] = 'timestamp_based'
                    q['source'] = 'transcript_analysis'
            
            # Combine and shuffle
            all_questions = frame_questions + timestamp_questions
            random.shuffle(all_questions)
            
            logger.info(f"✅ Hybrid generation complete: {len(all_questions)} total questions")
            return all_questions
            
        except Exception as e:
            logger.error(f"❌ Hybrid generation failed: {str(e)}")
            return []
    
    def _generate_questions_timestamp_based(self, context: dict, num_questions: int, include_mcq: bool) -> List[Dict]:
        """
        Traditional timestamp-based question generation (fallback method)
        """
        try:
            segments = context.get('segments', [])
            if not segments:
                logger.warning("No segments found in context")
                return []

            questions = []
            # Enhanced question types including MCQ, MSQ, NAT
            question_types = [
                'factual', 'conceptual', 'application', 'analysis',
                'mcq', 'msq', 'numerical', 'true_false'
            ]
            
            logger.info(f"📝 Generating {num_questions} timestamp-based questions from {len(segments)} segments")
            
            # Generate questions from different segments
            for i in range(num_questions):
                if i < len(segments):
                    segment = segments[i]
                else:
                    # Cycle through segments if we need more questions
                    segment = segments[i % len(segments)]
                
                try:
                    # Select question type (rotate through all types)
                    question_type = question_types[i % len(question_types)]
                    
                    # Generate question using LLM
                    question = self._generate_llm_question(segment, question_type)
                    
                    logger.debug(f"Question generation attempt {i+1} ({question_type}): {question}")
                    
                    if question and question.get('question') and question['question'].get('text'):
                        # Add metadata and tagging
                        question['question']['segment_index'] = i % len(segments)
                        question['question']['generated_type'] = question_type
                        question['question']['question_id'] = f"Q_{i+1:03d}"
                        question['question']['difficulty_level'] = 'auto'  # Will be determined by LLM Judge
                        
                        questions.append({
                            'question': question['question'],
                            'timestamp': segment.get('time', segment.get('timestamp', '00:00:00')),
                            'segment_text': segment.get('text', '')[:100] + '...' if len(segment.get('text', '')) > 100 else segment.get('text', ''),
                            'question_type': question_type,
                            'tags': self._generate_tags(segment.get('text', ''), question_type)
                        })
                        
                        logger.info(f"Generated question {i+1} ({question_type}): {question['question']['text'][:50]}...")
                        
                    else:
                        logger.warning(f"Failed to generate question {i+1}")
                        
                except Exception as e:
                    logger.error(f"Error generating question {i+1}: {str(e)}")
                    continue
            
            logger.info(f"✅ Timestamp-based generation complete: {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Timestamp-based generation failed: {str(e)}")
            return []
    
    def _generate_frame_tags(self, question: Dict) -> List[str]:
        """Generate tags for frame-based questions"""
        try:
            tags = []
            
            # Add question type tag
            q_type = question.get('type', 'unknown')
            tags.append(f"type:{q_type}")
            
            # Add difficulty tag
            difficulty = question.get('difficulty', 'medium')
            tags.append(f"difficulty:{difficulty}")
            
            # Add topic tag
            topic = question.get('topic', 'general')
            if topic and topic != 'general':
                tags.append(f"topic:{topic.lower().replace(' ', '_')}")
            
            # Add confidence tag
            confidence = question.get('confidence', 0.5)
            if confidence >= 0.8:
                tags.append("quality:high")
            elif confidence >= 0.6:
                tags.append("quality:medium")
            else:
                tags.append("quality:low")
            
            # Add frame analysis tag
            tags.append("source:vlm")
            tags.append("analysis:frame_based")
            
            return tags
            
        except Exception as e:
            logger.error(f"Error generating frame tags: {str(e)}")
            return ["analysis:frame_based"]

    def generate_question(self, segment: dict, timestamp: str) -> dict:
        """
        Generate questions for ALL difficulty levels from a single segment
        
        Args:
            segment: Dictionary with context from ContextValidator
            timestamp: Timestamp for the questions
            
        Returns:
            Dictionary with questions for easy, medium, and hard difficulty levels
        """
        try:
            logger.debug(f"QuestionGenerator.generate_question called with segment keys: {list(segment.keys()) if segment else 'None'}")
            logger.debug(f"Segment content: {segment}")
            
            # Handle different context formats (traditional vs Visual-First)
            if segment.get('method') == 'visual_first':
                # Visual-First format: use question_content or slide_content + transcript_text
                text = segment.get('question_content') or (
                    segment.get('slide_content', '') + ' ' + segment.get('transcript_text', '')
                ).strip()
                logger.debug(f"Using Visual-First format, extracted text length: {len(text)}")
                
                # Create normalized segment with 'text' field for downstream methods
                normalized_segment = dict(segment)
                normalized_segment['text'] = text
                segment = normalized_segment
            else:
                # Traditional format: use 'text' field
                text = segment.get('text', '').strip()
                logger.debug(f"Using traditional format, text length: {len(text)}")
            
            if not text or len(text) < 10:
                logger.debug(f"Segment text too short: '{text}'")
                return None

            # Generate one question for each difficulty level
            difficulties = ['easy', 'medium', 'hard']
            questions = {}
            
            for difficulty in difficulties:
                logger.debug(f"Generating {difficulty} question for timestamp {timestamp}")
                
                # Prefer MCQ for better assessment, fallback to other types
                question_data = self._generate_enhanced_mcq_question(segment, timestamp, difficulty)
                
                if not question_data:
                    # Fallback to other question types
                    if difficulty == 'easy':
                        question_data = self._generate_factual_question(segment, timestamp, difficulty)
                    elif difficulty == 'medium':
                        question_data = self._generate_enhanced_msq_question(segment, timestamp, difficulty)
                    else:  # hard
                        question_data = self._generate_enhanced_nat_question(segment, timestamp, difficulty)
                
                if question_data:
                    question_data['difficulty'] = difficulty
                    questions[f'{difficulty}_question'] = question_data
                    logger.debug(f"Generated {difficulty} {question_data.get('type', 'unknown')} question")
                else:
                    logger.warning(f"Failed to generate {difficulty} question for {timestamp}")
            
            if questions:
                logger.info(f"Generated {len(questions)} difficulty-level questions for {timestamp}")
                return {'questions': questions, 'timestamp': timestamp}
            else:
                logger.warning(f"No questions generated for any difficulty level at {timestamp}")
                return None
                
        except Exception as e:
            logger.error(f"Error in generate_question: {str(e)}")
            return None
    
    def _generate_with_llm(self, transcript: str, slide_text: str, timestamp: str) -> Optional[dict]:
        """Generate question using LLM for better quality and relevance"""
        try:
            import requests
            
            # Combine all available content
            content = f"Transcript: {transcript}"
            if slide_text:
                content += f"\nSlide Content: {slide_text}"
            
            # Create intelligent prompt for question generation
            prompt = f"""You are an expert educator creating assessment questions from educational video content.

Content from video at {timestamp}:
{content}

Generate ONE high-quality educational question based on this content. The question should:
1. Be directly relevant to the specific content provided
2. Test meaningful understanding, not just recall
3. Have a clear, accurate answer
4. Be appropriate for the subject matter

Respond with a JSON object in this exact format:
{{
    "text": "Your question here?",
    "answer": "Complete answer explaining the concept",
    "type": "factual/conceptual/application",
    "difficulty": "easy/medium/hard"
}}

Focus on the most important concept or idea from the content. Make the question specific and meaningful."""

            # Try to use local LLM (Ollama)
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2:3b-instruct-q4_K_M",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get('response', '').strip()
                    
                    # Parse JSON response
                    try:
                        import json
                        # Extract JSON from response (handle cases where LLM adds extra text)
                        json_start = llm_response.find('{')
                        json_end = llm_response.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = llm_response[json_start:json_end]
                            question_data = json.loads(json_str)
                            
                            # Validate required fields
                            if all(key in question_data for key in ['text', 'answer', 'type']):
                                return question_data
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"LLM generation failed: {str(e)}")
                
            # Fallback to improved template-based generation if LLM fails
            return self._generate_template_fallback(transcript, slide_text)
            
        except Exception as e:
            logger.error(f"Error in LLM question generation: {str(e)}")
            return None
    
    def _generate_mcq_fallback(self, text: str, timestamp: str, difficulty: str) -> dict:
        """Fallback MCQ generation when LLM is not available"""
        try:
            # Extract meaningful concepts using pattern matching
            concepts = self._extract_smart_concepts(text)
            if not concepts:
                return None
            
            # Select the most important concept
            main_concept = concepts[0]
            
            # Create difficulty-appropriate question
            if difficulty == 'easy':
                question_text = f"What is {main_concept}?"
                correct_answer = self._extract_definition_from_text(text, main_concept) or f"{main_concept} is a key concept discussed in this content."
            elif difficulty == 'medium':
                question_text = f"How does {main_concept} relate to the broader context?"
                correct_answer = self._extract_explanation_from_text(text, main_concept) or f"{main_concept} plays an important role in this context."
            else:  # hard
                question_text = f"What would be the implications of {main_concept} in real-world applications?"
                correct_answer = self._extract_application_from_text(text, main_concept) or f"{main_concept} has significant practical applications."
            
            # Generate simple distractors
            distractors = [
                "This concept is not directly addressed in the given content",
                "Multiple confounding factors influence this outcome", 
                "The relationship between variables remains unclear"
            ]
            
            # Create options
            options = [correct_answer] + distractors[:3]
            random.shuffle(options)
            correct_index = options.index(correct_answer)
            
            return {
                'text': question_text,
                'answer': chr(65 + correct_index),  # A, B, C, D
                'detailed_answer': correct_answer,
                'options': options,
                'type': 'mcq',
                'difficulty': difficulty,
                'topic': main_concept,
                'timestamp': timestamp,
                'confidence': 0.6,
                'generation_method': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Error in MCQ fallback generation: {str(e)}")
            return None

    def _extract_primary_topic(self, text: str) -> str:
        """Extract the primary topic/concept from text"""
        try:
            # Simple extraction of key terms
            concepts = self._extract_smart_concepts(text)
            if concepts:
                return concepts[0]
            
            # Fallback: use first significant word
            words = text.split()
            for word in words:
                if len(word) > 4 and word.lower() not in ['this', 'that', 'with', 'from', 'they', 'have', 'been', 'will', 'would', 'could', 'should']:
                    return word.title()
            
            return "Concept"
        except:
            return "Topic"
    
    def _generate_factual_question(self, segment: dict, timestamp: str, difficulty: str = 'easy') -> dict:
        """Generate factual questions with difficulty consideration"""
        try:
            text = segment.get('text', '').strip()
            if not text or len(text) < 10:
                return None
            
            # Extract main topic
            topic = self._extract_primary_topic(text)
            
            # Create difficulty-appropriate question
            if difficulty == 'easy':
                question_text = f"What is {topic}?"
            elif difficulty == 'medium':
                question_text = f"How does {topic} work in this context?"
            else:  # hard
                question_text = f"What would be the implications of {topic} in practice?"
            
            return {
                'text': question_text,
                'answer': text[:100] + "..." if len(text) > 100 else text,
                'type': 'factual',
                'difficulty': difficulty,
                'topic': topic,
                'timestamp': timestamp,
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"Error generating factual question: {str(e)}")
            return None
    
    def _generate_enhanced_msq_question(self, segment: dict, timestamp: str, difficulty: str = 'medium') -> dict:
        """Generate Multiple Select Questions with difficulty consideration"""
        try:
            text = segment.get('text', '').strip()
            if not text or len(text) < 30:
                return None
            
            # Use LLM for MSQ generation
            return self._generate_msq_with_llm(text, difficulty, timestamp)
            
        except Exception as e:
            logger.error(f"Error generating MSQ: {str(e)}")
            return None
    
    def _generate_enhanced_nat_question(self, segment: dict, timestamp: str, difficulty: str = 'hard') -> dict:
        """Generate Numerical Answer Type questions with difficulty consideration"""
        try:
            text = segment.get('text', '').strip()
            if not text or len(text) < 20:
                return None
            
            # Use LLM for NAT generation
            return self._generate_nat_with_llm(text, difficulty, timestamp)
            
        except Exception as e:
            logger.error(f"Error generating NAT: {str(e)}")
            return None
    
    def _generate_msq_with_llm(self, text: str, difficulty: str, timestamp: str) -> dict:
        """Generate MSQ using LLM"""
        try:
            import requests
            import json
            
            prompt = f"""Create a multiple select question (multiple correct answers) from this content:

Content: {text}

Create a {difficulty} difficulty question with 5-6 options where 2-3 are correct.

Format as JSON:
{{
    "question": "Which of the following are correct about...?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
    "correct_answers": ["A", "C", "D"],
    "explanation": "Explanation of correct answers"
}}"""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b-instruct-q4_K_M",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result.get('response', '')
                
                start = llm_output.find('{')
                end = llm_output.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = llm_output[start:end]
                    llm_data = json.loads(json_str)
                    
                    return {
                        'text': llm_data.get('question', ''),
                        'answer': ','.join(llm_data.get('correct_answers', [])),
                        'detailed_answer': llm_data.get('explanation', ''),
                        'options': llm_data.get('options', []),
                        'correct_answers': llm_data.get('correct_answers', []),
                        'type': 'msq',
                        'difficulty': difficulty,
                        'topic': self._extract_primary_topic(text),
                        'timestamp': timestamp,
                        'confidence': 0.8
                    }
        except Exception as e:
            logger.warning(f"LLM MSQ generation failed: {str(e)}")
        
        return None
    
    def _generate_nat_with_llm(self, text: str, difficulty: str, timestamp: str) -> dict:
        """Generate NAT using LLM"""
        try:
            import requests
            import json
            
            prompt = f"""Create a numerical answer question from this content:

Content: {text}

Create a {difficulty} difficulty question that requires a numerical answer (number, percentage, or count).

Format as JSON:
{{
    "question": "What percentage of...?",
    "answer": "75",
    "explanation": "The numerical answer explanation",
    "unit": "%"
}}"""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b-instruct-q4_K_M",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result.get('response', '')
                
                start = llm_output.find('{')
                end = llm_output.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = llm_output[start:end]
                    llm_data = json.loads(json_str)
                    
                    return {
                        'text': llm_data.get('question', ''),
                        'answer': str(llm_data.get('answer', '')),
                        'detailed_answer': llm_data.get('explanation', ''),
                        'unit': llm_data.get('unit', ''),
                        'type': 'nat',
                        'difficulty': difficulty,
                        'topic': self._extract_primary_topic(text),
                        'timestamp': timestamp,
                        'confidence': 0.8
                    }
        except Exception as e:
            logger.warning(f"LLM NAT generation failed: {str(e)}")
        
        return None

    def _generate_template_fallback(self, transcript: str, slide_text: str) -> Optional[dict]:
        """Improved template-based fallback with better concept extraction"""
        try:
            # Extract meaningful concepts using better NLP
            combined_text = f"{transcript} {slide_text}".strip()
            
            if not combined_text:
                return None
                
            # Extract key terms more intelligently
            key_concepts = self._extract_key_concepts(combined_text)
            
            if not key_concepts:
                # Generate direct question from content
                return {
                    'text': f"What is discussed in this segment?",
                    'answer': combined_text[:200] + '...' if len(combined_text) > 200 else combined_text,
                    'type': 'factual',
                    'difficulty': 'easy'
                }
            
            # Use the best concept for question generation
            main_concept = key_concepts[0]
            question_type = self._determine_question_type(transcript, slide_text)
            
            # Select appropriate template
            if question_type == "conceptual":
                templates = self.conceptual_templates
            elif question_type == "application":
                templates = self.application_templates
            else:
                templates = self.factual_templates
            
            # Generate question
            template = random.choice(templates)
            question_text = template.format(concept=main_concept)
            
            # Generate contextual answer
            answer = self._generate_answer(main_concept, combined_text, question_type)
            
            return {
                'text': question_text,
                'answer': answer,
                'type': question_type,
                'difficulty': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Template fallback error: {str(e)}")
            return None
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts more intelligently"""
        try:
            # Remove common words and extract meaningful terms
            import re
            
            # Clean text
            text = re.sub(r'[^\s]', ' ', text.lower())
            words = text.split()
            
            # Remove stop words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
                'might', 'must', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
                'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
                'his', 'her', 'its', 'our', 'their', 'so', 'if', 'then', 'than', 'when',
                'where', 'why', 'how', 'what', 'who', 'which', 'about', 'into', 'through',
                'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off',
                'over', 'under', 'again', 'further', 'then', 'once'
            }
            
            # Filter meaningful words (3+ characters, not stop words)
            meaningful_words = [
                word for word in words 
                if len(word) >= 3 and word not in stop_words and word.isalpha()
            ]
            
            # Count frequency
            word_freq = {}
            for word in meaningful_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top concepts
            top_concepts = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)
            
            # Return top 3 concepts, capitalize properly
            return [concept.capitalize() for concept in top_concepts[:3]]
            
        except Exception as e:
            logger.error(f"Concept extraction error: {str(e)}")
            return []
    
    def _generate_answer(self, concept: str, context: str, question_type: str) -> str:
        """Generate a contextual answer based on available content"""
        try:
            if question_type == "factual":
                return f"{concept} is a key concept discussed in the content. Based on the available information: {context[:150]}..."
            elif question_type == "conceptual":
                return f"{concept} is important because it represents a fundamental idea in this subject. The content explains: {context[:150]}..."
            else:  # application
                return f"{concept} can be applied in practice. According to the content: {context[:150]}..."
        except:
            return f"This relates to {concept} as discussed in the educational content."
    
    def _determine_question_type(self, transcript: str, slide_text: str) -> str:
        """
        Determine the most appropriate question type based on content
        
        Args:
            transcript: Transcript text
            slide_text: Slide/OCR text
            
        Returns:
            Question type: 'factual', 'conceptual', or 'application'
        """
        text = (transcript + " " + slide_text).lower()
        
        # Factual indicators
        factual_indicators = [
            " is ", " are ", " was ", " were ",
            "definition", "defined as", "means that",
            "refers to", "called", "known as"
        ]
        
        # Conceptual indicators
        conceptual_indicators = [
            "why", "how", "because", "reason",
            "important", "significant", "purpose",
            "principle", "theory", "concept"
        ]
        
        # Application indicators  
        application_indicators = [
            "example", "instance", "practice", "use",
            "apply", "implementation", "scenario",
            "case", "situation", "problem"
        ]
        
        factual_score = sum(1 for indicator in factual_indicators if indicator in text)
        conceptual_score = sum(1 for indicator in conceptual_indicators if indicator in text)
        application_score = sum(1 for indicator in application_indicators if indicator in text)
        
        # Return the type with highest score, with factual as default
        if application_score > factual_score and application_score > conceptual_score:
            return "application"
        elif conceptual_score > factual_score:
            return "conceptual"
        else:
            return "factual"
    
    def _generate_by_type(self, transcript: str, slide_text: str, question_type: str) -> Dict[str, Any]:
        """
        Generate question based on determined type
        
        Args:
            transcript: Transcript text
            slide_text: Slide text
            question_type: Type of question to generate
            
        Returns:
            Question dictionary
        """
        if question_type == "factual":
            return self._generate_factual_question(transcript, slide_text)
        elif question_type == "conceptual":
            return self._generate_conceptual_question(transcript, slide_text)
        elif question_type == "application":
            return self._generate_application_question(transcript, slide_text)
        else:
            return self._generate_factual_question(transcript, slide_text)  # fallback
    
    def _generate_factual_question(self, transcript: str, slide_text: str) -> Dict[str, Any]:
        """Generate factual/recall question"""
        
        # Clean transcript of artifacts
        clean_transcript = self._clean_transcript(transcript)
        
        # Prefer slide text for concept extraction if available and substantial
        source_text = slide_text if slide_text and len(slide_text) > 50 else clean_transcript
        answer_text = slide_text if slide_text and len(slide_text) > 20 else clean_transcript
        
        # Extract key concept
        concept = self._extract_main_concept(source_text, slide_text)
        
        # Check for definition pattern in slide text first, then transcript
        definition_match = None
        if slide_text:
            definition_match = re.search(r'(.+?)\s+(?:is|are|means?|refers? to)\s+(.+)', slide_text, re.IGNORECASE)
        
        if not definition_match and clean_transcript:
            definition_match = re.search(r'(.+?)\s+(?:is|are|means?|refers? to)\s+(.+)', clean_transcript, re.IGNORECASE)
        
        if definition_match:
            concept_candidate = definition_match.group(1).strip()
            answer = definition_match.group(2).strip()
            
            # Clean up concept (remove common filler words)
            concept_candidate = self._clean_concept(concept_candidate)
            
            if len(concept_candidate.split()) <= 4 and concept_candidate.lower() not in ['so this', 'this', 'that']:
                concept = concept_candidate
                question_text = f"What is {concept}?"
            else:
                # Fallback to template
                template = random.choice(self.factual_templates)
                question_text = template.format(concept=concept)
                answer = self._clean_answer(answer_text)
        else:
            # Use template
            template = random.choice(self.factual_templates)
            question_text = template.format(concept=concept)
            answer = self._clean_answer(answer_text)
        
        return {
            "text": question_text,
            "type": "factual",
            "options": self._generate_mcq_options(answer) if len(answer) < 200 else [],
            "answer": answer,
            "concept": concept
        }

    # Enhanced question generation methods for MCQ, MSQ, and NAT types
    def _generate_enhanced_mcq_question(self, segment: dict, timestamp: str, difficulty: str = 'medium') -> dict:
        """Generate enhanced MCQ questions using LLM for better option generation"""
        try:
            text = segment.get('text', '').strip()
            if not text or len(text) < 20:
                return None
            
            # Use LLM to generate question and options
            llm_result = self._generate_mcq_with_llm(text, difficulty, timestamp)
            if llm_result:
                return llm_result
            
            # Fallback to pattern-based generation if LLM fails
            return self._generate_mcq_fallback(text, timestamp, difficulty)
            
        except Exception as e:
            logger.error(f"Error generating enhanced MCQ: {str(e)}")
            return None
    
    def _generate_mcq_with_llm(self, text: str, difficulty: str, timestamp: str) -> dict:
        """Generate MCQ using LLM for high-quality questions and options"""
        try:
            import requests
            
            # Create difficulty-specific prompt
            difficulty_prompts = {
                'easy': "Create a basic recall question about key facts or definitions.",
                'medium': "Create a comprehension question that requires understanding concepts.",
                'hard': "Create an analysis/application question that requires critical thinking."
            }
            
            prompt = f"""You are an expert educator creating a multiple choice question from educational content.

Content: {text}

Task: {difficulty_prompts.get(difficulty, difficulty_prompts['medium'])}

Requirements:
- Create 1 clear, {difficulty} difficulty question
- Provide 4 specific, meaningful options (A, B, C, D) with exactly 1 correct answer
- Make incorrect options plausible but clearly wrong
- Focus on educational concepts, not trivial details
- Options should be actual content-specific answers, NOT generic labels

Format your response as JSON:
{{
    "question": "Your question here?",
    "options": ["Specific meaningful option", "Another specific option", "Third specific option", "Fourth specific option"],
    "correct_answer": "A",
    "explanation": "Why this answer is correct"
}}

Example of good options: ["Correlation coefficient", "Standard deviation", "Mean absolute error", "P-value"]
Example of bad options: ["Option A", "Option B", "Option C", "Option D"]"""

            # Call Ollama LLM
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:3b-instruct-q4_K_M",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result.get('response', '')
                
                # Extract JSON from LLM response
                try:
                    import json
                    # Find JSON in the response
                    start = llm_output.find('{')
                    end = llm_output.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = llm_output[start:end]
                        llm_data = json.loads(json_str)
                        
                        # Find correct answer index
                        correct_letter = llm_data.get('correct_answer', 'A')
                        correct_index = ord(correct_letter.upper()) - ord('A')
                        
                        return {
                            'text': llm_data.get('question', ''),
                            'answer': correct_letter.upper(),
                            'detailed_answer': llm_data.get('explanation', ''),
                            'options': llm_data.get('options', []),
                            'type': 'mcq',
                            'difficulty': difficulty,
                            'topic': self._extract_primary_topic(text),
                            'timestamp': timestamp,
                            'confidence': 0.9,
                            'generation_method': 'llm'
                        }
                except json.JSONDecodeError:
                    logger.warning("LLM response was not valid JSON, falling back")
                    
        except Exception as e:
            logger.warning(f"LLM MCQ generation failed: {str(e)}")
            
        return None
    
    def _generate_mcq_fallback(self, text: str, timestamp: str, difficulty: str) -> dict:
        """Fallback MCQ generation when LLM is not available"""
        return None
    
    def _extract_smart_concepts(self, text: str) -> list:
        """Generate Multiple Select Questions (MSQ) with multiple correct answers"""
        try:
            text = segment.get('text', '').strip()
            if not text or len(text) < 50:
                return None
            
            # Extract multiple concepts/points
            concepts = self._extract_smart_concepts(text)
            if len(concepts) < 2:
                return None
            
            # Create question about multiple aspects
            question_text = f"Which of the following statements about the content are correct? (Select all that apply)"
            
            # Generate multiple correct statements
            correct_statements = []
            for concept in concepts[:3]:  # Up to 3 correct answers
                statement = self._create_factual_statement(text, concept)
                if statement:
                    correct_statements.append(statement)
            
            if len(correct_statements) < 2:
                return None
            
            # Generate distractors (incorrect statements)
            distractors = []
            for concept in concepts:
                distractor = self._create_incorrect_statement(concept)
                if distractor:
                    distractors.append(distractor)
            
            # Combine options
            all_options = correct_statements + distractors[:2]  # 2 distractors max
            random.shuffle(all_options)
            
            # Find correct indices
            correct_indices = [i for i, option in enumerate(all_options) if option in correct_statements]
            correct_answers = [chr(65 + i) for i in correct_indices]  # A, B, C, etc.
            
            return {
                'text': question_text,
                'answer': ', '.join(correct_answers),
                'detailed_answer': '; '.join(correct_statements),
                'options': all_options,
                'type': 'msq',
                'correct_count': len(correct_answers),
                'difficulty': 'medium',  # MSQs are typically medium difficulty
                'topic': concepts[0],
                'timestamp': timestamp,
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced MSQ: {str(e)}")
            return None
    
    def _generate_enhanced_nat_question(self, segment: dict, timestamp: str) -> dict:
        """Generate Numerical Answer Type (NAT) questions"""
        try:
            text = segment.get('text', '').strip()
            if not text:
                return None
            
            # Extract numbers from text
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
            if not numbers:
                return None
            
            # Find context for the number
            for num in numbers:
                # Look for context around the number
                num_context = self._find_number_context(text, num)
                if num_context:
                    question_text = f"What is the {num_context} mentioned in the content?"
                    
                    return {
                        'text': question_text,
                        'answer': num,
                        'detailed_answer': f"The {num_context} is {num}",
                        'type': 'nat',
                        'numeric_answer': float(num),
                        'unit': self._extract_unit_from_context(text, num),
                        'difficulty': 'easy',  # NAT questions are typically easier
                        'topic': num_context,
                        'timestamp': timestamp,
                        'confidence': 0.6
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating enhanced NAT: {str(e)}")
            return None
    
    def _extract_smart_concepts(self, text: str) -> list:
        """Extract meaningful concepts from text using NLP patterns"""
        if not isinstance(text, str):
            return []
            
        concepts = []
        
        # Look for technical terms (words with specific patterns)
        technical_terms = re.findall(r'\b(?:correlation|causation|analysis|research|study|data|model|theory|hypothesis|experiment|variable|factor|method|process|system|algorithm|technique|approach|statistics|probability|sample|population|bias|significance|confidence|interval|regression|classification|prediction|machine|learning|artificial|intelligence|neural|network|deep|supervised|unsupervised|training|testing|validation|accuracy|precision|recall|feature|dataset|optimization|dataset|variable|measurement|outcome|result|finding|conclusion|evidence|pattern|trend|relationship|association|effect|impact|influence|factor|element|component|aspect|dimension|parameter|criterion|indicator|metric|score|rating|value|number|percentage|proportion|ratio|rate|frequency|distribution|variance|deviation|error|uncertainty|risk|probability|likelihood|chance|odds|prediction|forecast|estimation|calculation|computation|evaluation|assessment|comparison|contrast|difference|similarity|variation|change|improvement|increase|decrease|reduction|enhancement|development|progress|advancement|innovation|discovery|breakthrough|insight|understanding|knowledge|expertise|skill|competence|ability|capability|capacity|potential|opportunity|challenge|problem|issue|concern|limitation|constraint|barrier|obstacle|difficulty|complexity|simplicity|clarity|precision|accuracy|reliability|validity|consistency|stability|robustness|effectiveness|efficiency|performance|quality|standard|benchmark|threshold|criteria|requirement|specification|guideline|protocol|procedure|methodology|framework|structure|organization|system|platform|infrastructure|foundation|basis|principle|concept|idea|notion|theory|hypothesis|assumption|premise|argument|reasoning|logic|rationale|explanation|interpretation|analysis|synthesis|evaluation|judgment|decision|conclusion|recommendation|suggestion|proposal|solution|answer|response|result|outcome|consequence|implication|significance|importance|relevance|applicability|utility|value|benefit|advantage|disadvantage|strength|weakness|limitation|challenge|opportunity|threat|risk)\b', text, re.IGNORECASE)
        concepts.extend([term.title() for term in technical_terms if len(term) > 3])
        
        # Look for capitalized terms that might be important (but filter out common words)
        common_words = {'You', 'The', 'And', 'But', 'For', 'Are', 'Was', 'Were', 'Been', 'Have', 'Has', 'Had', 'Will', 'Would', 'Should', 'Could', 'Can', 'May', 'Might', 'Must', 'Shall', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 'Why', 'How', 'Who', 'Which', 'Whose', 'Whom'}
        
        defined_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for term in defined_terms:
            if term not in common_words and len(term) > 3 and term not in concepts:
                concepts.append(term)
        
        # Look for quoted terms or terms in parentheses
        quoted_terms = re.findall(r'["\']([^"\']{3,})["\']', text)
        concepts.extend(quoted_terms[:2])
        
        parentheses_terms = re.findall(r'\(([^)]{3,20})\)', text)
        concepts.extend(parentheses_terms[:2])
        
        # Remove duplicates and clean
        unique_concepts = []
        for concept in concepts:
            if concept and concept not in unique_concepts and len(concept.strip()) > 2:
                unique_concepts.append(concept.strip())
        
        # If no good concepts found, look for longer meaningful phrases
        if not unique_concepts:
            words = text.split()
            if len(words) >= 3:
                # Look for noun phrases (simple heuristic)
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if not any(word in phrase.lower() for word in ['the', 'and', 'or', 'but', 'you', 'i', 'we', 'they']):
                        unique_concepts.append(phrase)
                        if len(unique_concepts) >= 3:
                            break
        
        return unique_concepts[:5]  # Top 5 concepts
    
    def _extract_definition_from_text(self, text: str, concept: str) -> str:
        """Extract definition of a concept from text"""
        if not isinstance(text, str) or not isinstance(concept, str):
            return f"Key information about {concept}"
            
        try:
            # Look for definition patterns
            patterns = [
                rf'{re.escape(concept)}\s+is\s+([^.!?]+)',
                rf'{re.escape(concept)}\s+means\s+([^.!?]+)',
                rf'([^.!?]+)\s+is\s+called\s+{re.escape(concept)}',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            # Fallback: use surrounding context
            words = text.split()
            concept_words = concept.split()
            for i, word in enumerate(words):
                if len(concept_words) > 0 and word.lower() == concept_words[0].lower():
                    # Take context around the concept
                    start = max(0, i - 10)
                    end = min(len(words), i + 15)
                    context = ' '.join(words[start:end])
                    return context
            
            return f"A key concept discussed in relation to {concept}"
        except Exception as e:
            return f"Important concept: {concept}"
    
    def _extract_explanation_from_text(self, text: str, concept: str) -> str:
        """Extract explanation for why something is important"""
        # Look for explanation patterns
        patterns = [
            rf'because\s+([^.!?]+)',
            rf'since\s+([^.!?]+)', 
            rf'due to\s+([^.!?]+)',
            rf'therefore\s+([^.!?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return f"{concept} is important for understanding the key principles discussed"
    
    def _extract_process_from_text(self, text: str, concept: str) -> str:
        """Extract process or method description"""
        # Look for process patterns
        if 'steps' in text.lower() or 'process' in text.lower() or 'method' in text.lower():
            sentences = text.split('.')
            for sentence in sentences:
                if concept.lower() in sentence.lower():
                    return sentence.strip()
        
        return f"{concept} works through the mechanisms described in the content"
    
    def _generate_smart_distractors(self, correct_answer: str, concept: str, context: str) -> list:
        """Generate plausible but incorrect answer options"""
        distractors = []
        
        # Strategy 1: Create opposite or contrasting statements
        opposites = {
            'increases': 'decreases',
            'positive': 'negative', 
            'high': 'low',
            'strong': 'weak',
            'correlation': 'causation',
            'causation': 'correlation',
            'significant': 'insignificant',
            'accurate': 'inaccurate'
        }
        
        for word, opposite in opposites.items():
            if word in correct_answer.lower():
                distractor = correct_answer.lower().replace(word, opposite)
                distractors.append(distractor.capitalize())
                break
        
        # Strategy 2: Generic plausible academic answers
        generic_distractors = [
            "This concept is not directly addressed in the given content",
            "The relationship between variables remains unclear",
            "Multiple confounding factors influence this outcome",
            "Further research is needed to establish this connection"
        ]
        
        distractors.extend(generic_distractors)
        
        # Strategy 3: Modify the correct answer slightly
        if len(correct_answer) > 30:
            words = correct_answer.split()
            if len(words) > 5:
                # Replace a key word
                modified_words = words[:]
                modified_words[len(words)//2] = "different"
                distractors.append(' '.join(modified_words))
        
        # Return unique distractors
        unique_distractors = []
        for d in distractors:
            if d not in unique_distractors and d.lower() != correct_answer.lower():
                unique_distractors.append(d)
        
        return unique_distractors[:3]  # Maximum 3 distractors
    
    def _create_factual_statement(self, text: str, concept: str) -> str:
        """Create a factual statement about a concept from text"""
        # Extract sentences containing the concept
        sentences = text.split('.')
        for sentence in sentences:
            if concept.lower() in sentence.lower() and len(sentence.strip()) > 10:
                return sentence.strip()
        
        return f"{concept} is a key element discussed in this content"
    
    def _create_incorrect_statement(self, concept: str) -> str:
        """Create an incorrect statement about a concept"""
        incorrect_statements = [
            f"{concept} is not relevant to this field of study",
            f"{concept} has been proven to be outdated",
            f"{concept} only applies in very specific circumstances",
            f"{concept} contradicts established research findings"
        ]
        
        return random.choice(incorrect_statements)
    
    def _find_number_context(self, text: str, number: str) -> str:
        """Find context for a number in text"""
        # Look for common numerical contexts
        contexts = {
            'percent': ['percent', '%', 'percentage'],
            'year': ['year', 'years', '20'],
            'count': ['participants', 'subjects', 'samples', 'cases'],
            'measurement': ['cm', 'mm', 'inches', 'meters', 'kg', 'grams'],
            'score': ['score', 'rating', 'points', 'grade'],
            'time': ['minutes', 'hours', 'seconds', 'days'],
            'probability': ['probability', 'chance', 'likelihood']
        }
        
        number_pos = text.find(number)
        if number_pos == -1:
            return None
        
        # Get context around the number
        start = max(0, number_pos - 50)
        end = min(len(text), number_pos + 50)
        context_text = text[start:end].lower()
        
        for context_type, keywords in contexts.items():
            if any(keyword in context_text for keyword in keywords):
                return context_type
        
        return "value"
    
    def _extract_unit_from_context(self, text: str, number: str) -> str:
        """Extract unit of measurement for a number"""
        units = ['%', 'percent', 'years', 'minutes', 'hours', 'points', 'cm', 'mm', 'kg', 'grams']
        
        number_pos = text.find(number)
        if number_pos == -1:
            return ""
        
        # Look after the number for units
        after_number = text[number_pos + len(number):number_pos + len(number) + 20]
        for unit in units:
            if unit in after_number.lower():
                return unit
        
        return ""
    
    def _assess_difficulty(self, text: str, question: str) -> str:
        """Assess question difficulty based on content complexity"""
        # Simple heuristic based on text characteristics
        complex_terms = ['analysis', 'research', 'hypothesis', 'methodology', 'statistical', 'correlation', 'causation', 'regression', 'significance']
        
        if len(text) > 200 or any(term in text.lower() for term in complex_terms):
            return 'hard'
        elif len(text) > 100 or any(word in text.lower() for word in ['because', 'therefore', 'relationship', 'impact']):
            return 'medium'
        else:
            return 'easy'
    
    def _generate_conceptual_question(self, transcript: str, slide_text: str) -> Dict[str, Any]:
        """Generate conceptual/understanding question"""
        # Clean and prioritize slide text
        clean_transcript = self._clean_transcript(transcript)
        source_text = slide_text if slide_text and len(slide_text) > 50 else clean_transcript
        
        concept = self._extract_main_concept(source_text, slide_text)
        
        template = random.choice(self.conceptual_templates)
        question_text = template.format(concept=concept)
        
        # Use cleaner source for answer
        answer = self._clean_answer(slide_text if slide_text else clean_transcript)
        
        return {
            "text": question_text,
            "type": "conceptual", 
            "options": [],  # Conceptual questions typically open-ended
            "answer": answer,
            "concept": concept
        }
    
    def _generate_application_question(self, transcript: str, slide_text: str) -> Dict[str, Any]:
        """Generate application/analysis question"""
        # Clean and prioritize slide text
        clean_transcript = self._clean_transcript(transcript)
        source_text = slide_text if slide_text and len(slide_text) > 50 else clean_transcript
        
        concept = self._extract_main_concept(source_text, slide_text)
        
        # Try to extract scenario or problem context
        scenario = self._extract_scenario(source_text)
        problem = self._extract_problem_context(source_text)
        
        template = random.choice(self.application_templates)
        
        if scenario:
            question_text = template.format(concept=concept, scenario=scenario)
        elif problem:
            question_text = template.format(concept=concept, problem=problem)
        else:
            question_text = template.format(concept=concept, scenario="real-world situations")
        
        # Use cleaner source for answer
        answer = self._clean_answer(slide_text if slide_text else clean_transcript)
        
        return {
            "text": question_text,
            "type": "application",
            "options": [],  # Application questions typically open-ended
            "answer": answer,
            "concept": concept
        }
    
    def _extract_main_concept(self, transcript: str, slide_text: str) -> str:
        """Extract the main concept/topic from the text"""
        # Prioritize slide text for cleaner concept extraction
        primary_text = slide_text if slide_text and len(slide_text) > 30 else transcript
        secondary_text = transcript if slide_text else ""
        
        # Clean the text first
        clean_primary = self._clean_transcript(primary_text) if primary_text else ""
        clean_secondary = self._clean_transcript(secondary_text) if secondary_text else ""
        
        # Look for educational terms in slide text first
        if clean_primary:
            concept = self._extract_concept_from_text(clean_primary)
            if concept and concept != "the concept":
                return concept
        
        # Fallback to transcript
        if clean_secondary:
            concept = self._extract_concept_from_text(clean_secondary)
            if concept and concept != "the concept":
                return concept
        
        return "the concept"
    
    def _extract_concept_from_text(self, text: str) -> str:
        """Extract concept from a single text source"""
        if not text:
            return "the concept"
        
        # Look for capitalized terms (likely important concepts) 
        # but avoid common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By'}
        
        # Find capitalized multi-word terms
        capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        educational_terms = [term for term in capitalized_terms 
                           if len(term) > 3 and term not in common_words 
                           and not term.startswith(('So', 'But', 'And', 'Or'))]
        
        if educational_terms:
            # Return the first substantial educational term
            return educational_terms[0]
        
        # Look for key phrases that indicate definitions
        definition_patterns = [
            r'([A-Z][a-z\s]{3,20})\s+(?:is|are|means?|refers? to)',
            r'(?:called|known as)\s+([A-Z][a-z\s]{3,20})',
            r'([a-z\s]{3,20})\s+(?:definition|concept|theory|model|principle)'
        ]
        
        for pattern in definition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                concept = match.group(1).strip()
                concept = self._clean_concept(concept)
                if len(concept.split()) <= 4:
                    return concept
        
        # Look for subject of sentences (noun phrases)
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences[:3]:  # Check first 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 10:
                # Simple noun phrase extraction
                words = sentence.split()
                if len(words) >= 2:
                    # Look for noun phrases at start of sentence
                    candidate = ' '.join(words[:3])
                    candidate = re.sub(r'^(The|This|That|A|An)\s+', '', candidate, flags=re.IGNORECASE)
                    if len(candidate.split()) <= 2 and len(candidate) > 3:
                        return candidate.title()
        
        return "the concept"
    
    def _extract_scenario(self, transcript: str) -> str:
        """Extract scenario or context from transcript"""
        scenario_patterns = [
            r'(?:in|for|during|when|if)\s+(.+?)(?:\.|,|$)',
            r'(?:example|instance|case)(?:\s+of)?\s+(.+?)(?:\.|,|$)',
        ]
        
        for pattern in scenario_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                scenario = match.group(1).strip()
                if len(scenario.split()) <= 8:  # Keep it reasonable
                    return scenario
        
        return ""
    
    def _extract_problem_context(self, transcript: str) -> str:
        """Extract problem context from transcript"""
        problem_patterns = [
            r'(?:problem|issue|challenge|difficulty)\s+(?:of|with|in)\s+(.+?)(?:\.|,|$)',
            r'(?:solve|address|handle|deal with)\s+(.+?)(?:\.|,|$)',
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                problem = match.group(1).strip()
                if len(problem.split()) <= 8:
                    return problem
        
        return ""
    
    def _clean_transcript(self, transcript: str) -> str:
        """Clean transcript of artifacts and noise"""
        if not transcript:
            return ""
        
        # Remove UUID-like artifacts
        cleaned = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/\d+-\d+', '', transcript)
        
        # Remove other common artifacts
        cleaned = re.sub(r'\b[a-f0-9]{32,}\b', '', cleaned)  # Long hex strings
        cleaned = re.sub(r'\b\d{10,}\b', '', cleaned)        # Long number strings
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _clean_concept(self, concept: str) -> str:
        """Clean extracted concept"""
        if not concept:
            return "the concept"
        
        # Remove common filler phrases
        filler_phrases = [
            'so this', 'this is', 'that is', 'it is', 'we have', 'there is', 'there are',
            'but i\'m', 'i\'m', 'you know', 'like', 'um', 'uh', 'okay', 'right'
        ]
        
        concept_lower = concept.lower()
        for filler in filler_phrases:
            concept_lower = concept_lower.replace(filler, '').strip()
        
        # If nothing meaningful left, return original
        if len(concept_lower) < 3:
            return concept
        
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in concept_lower.split() if word)
    
    def _clean_answer(self, answer: str) -> str:
        """Clean answer text"""
        if not answer:
            return "No answer available"
        
        # Clean artifacts
        cleaned = self._clean_transcript(answer)
        
        # Limit length
        if len(cleaned) > 300:
            cleaned = cleaned[:300] + "..."
        
        return cleaned

    def _generate_mcq_options(self, answer: str, num_options: int = 4) -> List[str]:
        """
        Generate high-quality multiple choice options for factual questions
        
        Args:
            answer: Correct answer
            num_options: Number of total options (including correct)
            
        Returns:
            List of options including the correct answer, or empty if unsuitable
        """
        
        # Skip MCQ generation for complex answers
        if len(answer) > 150 or len(answer.split()) > 25:
            return []
        
        # Skip if answer contains artifacts or is incomplete
        artifacts = ['ffcb0144', '°', '©', 'fo}', 'that you', '/ ']
        if any(artifact in answer for artifact in artifacts):
            return []
        
        # Skip if answer is a title or fragment
        if answer.isupper() or answer.startswith('/') or answer.endswith(' that you'):
            return []
        
        # For now, disable problematic MCQ generation until we implement proper LLM-based option generation
        # The current simple rule-based approach creates poor quality options
        return []
        
        # TODO: Implement proper MCQ option generation using LLM
        # Should generate plausible distractors based on the educational content
        # Example approach:
        # 1. Use LLM to generate 3-4 plausible but incorrect alternatives
        # 2. Ensure options are grammatically correct and contextually relevant
        # 3. Avoid obvious patterns like "Not X" or simple tense changes
        # 4. Validate options don't duplicate or contradict each other

    def _generate_llm_question(self, segment: dict, question_type: str) -> dict:
        """
        Generate a question using LLM for different question types
        
        Args:
            segment: Text segment with content
            question_type: Type of question to generate
            
        Returns:
            Question object with text, answer, type, and options (for MCQ/MSQ)
        """
        try:
            content = segment.get('text', '').strip()
            if not content or len(content) < 20:
                return None
            
            # Different prompts for different question types
            if question_type == 'mcq':
                prompt = f"""
Create a multiple choice question (MCQ) based on this educational content:

Content: {content}

Generate:
1. A clear, specific question
2. Four options (A, B, C, D) where only ONE is correct
3. The correct answer (letter only)
4. Brief explanation

Format your response as JSON:
{{
    "text": "Your question here?",
    "type": "mcq",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct_answer": "A",
    "answer": "Brief explanation of why A is correct",
    "difficulty": "medium"
}}
"""

            elif question_type == 'msq':
                prompt = f"""
Create a multiple select question (MSQ) based on this educational content:

Content: {content}

Generate:
1. A question that has multiple correct answers
2. Four or more options where 2-3 are correct
3. List all correct answers
4. Brief explanation

Format your response as JSON:
{{
    "text": "Your question here?",
    "type": "msq", 
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct_answers": ["A", "C"],
    "answer": "Explanation of why A and C are correct",
    "difficulty": "medium"
}}
"""

            elif question_type == 'numerical':
                prompt = f"""
Create a numerical answer type (NAT) question based on this educational content:

Content: {content}

Generate:
1. A question requiring a numerical answer
2. The exact numerical answer
3. Units if applicable
4. Brief calculation/explanation

Format your response as JSON:
{{
    "text": "Your question here?",
    "type": "numerical",
    "numerical_answer": 42,
    "units": "percentage" or "none",
    "answer": "Brief explanation of the calculation",
    "difficulty": "medium"
}}
"""

            elif question_type == 'true_false':
                prompt = f"""
Create a true/false question based on this educational content:

Content: {content}

Generate:
1. A clear statement that can be true or false
2. The correct answer (true/false)
3. Brief explanation

Format your response as JSON:
{{
    "text": "Statement to evaluate as true or false",
    "type": "true_false",
    "correct_answer": "true",
    "answer": "Explanation of why this is true/false",
    "difficulty": "easy"
}}
"""

            else:  # factual, conceptual, application, analysis
                prompt = f"""
Create a {question_type} question based on this educational content:

Content: {content}

Question Type Guidelines:
- Factual: Tests recall of specific information
- Conceptual: Tests understanding of concepts and relationships  
- Application: Tests ability to apply knowledge to new situations
- Analysis: Tests ability to break down and examine information

Generate:
1. A clear, well-formed question appropriate for the type
2. A comprehensive answer
3. Difficulty level assessment

Format your response as JSON:
{{
    "text": "Your question here?",
    "type": "{question_type}",
    "answer": "Detailed answer explanation",
    "difficulty": "easy/medium/hard"
}}
"""

            # Call LLM to generate question
            import requests
            
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2:3b-instruct-q4_K_M",
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
                    llm_output = result.get('response', '').strip()
                    
                    # Try to parse JSON response
                    try:
                        import json
                        # Extract JSON from the response
                        json_start = llm_output.find('{')
                        json_end = llm_output.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = llm_output[json_start:json_end]
                            question_data = json.loads(json_str)
                            
                            return {'question': question_data}
                        
                    except Exception as e:
                        logger.error(f"JSON parsing error: {e}")
                        # Fallback: create structured response from text
                        return self._parse_text_response(llm_output, question_type)
                
            except Exception as e:
                logger.error(f"LLM API error: {e}")
                # Fallback to template-based generation
                return self._fallback_question_generation(content, question_type)
                
        except Exception as e:
            logger.error(f"Error in LLM question generation: {e}")
            return None

    def _generate_tags(self, content: str, question_type: str) -> list:
        """Generate relevant tags for the question"""
        tags = [question_type]
        
        # Add content-based tags
        content_lower = content.lower()
        
        # Subject tags
        if any(word in content_lower for word in ['correlation', 'causation', 'statistics']):
            tags.append('statistics')
        if any(word in content_lower for word in ['ai', 'artificial intelligence', 'machine learning']):
            tags.append('artificial_intelligence')
        if any(word in content_lower for word in ['research', 'study', 'analysis']):
            tags.append('research_methods')
        
        # Difficulty indicators
        if any(word in content_lower for word in ['complex', 'advanced', 'sophisticated']):
            tags.append('advanced')
        if any(word in content_lower for word in ['basic', 'simple', 'introduction']):
            tags.append('basic')
            
        return tags

    def _parse_text_response(self, text: str, question_type: str) -> dict:
        """Fallback parser for non-JSON LLM responses"""
        lines = text.split('\n')
        
        question_text = ""
        answer = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Question:') or line.startswith('Q:'):
                question_text = line.split(':', 1)[1].strip()
            elif line.startswith('Answer:') or line.startswith('A:'):
                answer = line.split(':', 1)[1].strip()
        
        if not question_text:
            question_text = lines[0] if lines else "Generated question"
        if not answer:
            answer = lines[-1] if lines else "Generated answer"
        
        return {
            'question': {
                'text': question_text,
                'type': question_type,
                'answer': answer,
                'difficulty': 'medium'
            }
        }

    def _fallback_question_generation(self, content: str, question_type: str) -> dict:
        """Fallback question generation when LLM is not available"""
        # Simple template-based fallback
        concepts = self._extract_key_concepts(content[:200])
        
        if not concepts:
            return None
            
        concept = concepts[0]
        
        if question_type == 'factual':
            question_text = f"What is {concept}?"
        elif question_type == 'conceptual':
            question_text = f"Explain the significance of {concept}."
        else:
            question_text = f"How can {concept} be applied?"
        
        return {
            'question': {
                'text': question_text,
                'type': question_type,
                'answer': f"Based on the content, {concept} is discussed in relation to the educational material.",
                'difficulty': 'medium'
            }
        }
