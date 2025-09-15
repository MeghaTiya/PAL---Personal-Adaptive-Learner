"""
Agent-based pipeline for video question generation
Implements the 3+1 agent architecture for educational content processing
"""

import cv2
import pytesseract
import json
import logging
from typing import List, Dict, Any, Optional
from .transcript_analyzer import TranscriptAnalyzer
from .context_validator import ContextValidator  
from .question_generator import QuestionGenerator
from .difficulty_rater import DifficultyRater

logger = logging.getLogger(__name__)

class TriPlusOnePipeline:
    """
    Main pipeline orchestrating the 4 agents:
    1. Transcript Analyzer - finds candidate timestamps
    2. Context Validator - validates visual/slide alignment  
    3. Question Generator - generates questions from context
    4. Difficulty Rater - rates question difficulty
    """
    
    def __init__(self, use_vlm: bool = True):
        """
        Initialize the pipeline with VLM-enhanced agents
        
        Args:
            use_vlm: Use Vision Language Model for better context extraction (default: True)
        """
        logger.info("Initializing Educational Question Generation Pipeline")
        
        # Initialize agents with VLM capability
        self.transcript_analyzer = TranscriptAnalyzer()
        self.context_validator = ContextValidator(use_vlm=use_vlm)  # VLM-enabled
        self.question_generator = QuestionGenerator()
        self.difficulty_rater = DifficultyRater()
        
        logger.info(f"Pipeline initialized with {'VLM' if use_vlm else 'OCR'} context extraction")
        logger.debug(f"Components: TranscriptAnalyzer={type(self.transcript_analyzer)}, ContextValidator={type(self.context_validator)}, QuestionGenerator={type(self.question_generator)}, DifficultyRater={type(self.difficulty_rater)}")
        
    def run(self, video_path: str, transcript: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Execute the complete pipeline
        
        Args:
            video_path: Path to the video file
            transcript: List of transcript segments with time and text
            
        Returns:
            List of enriched question objects
        """
        logger.info("=== PIPELINE START ===")
        logger.info(f"Video: {video_path}")
        logger.info(f"Transcript segments: {len(transcript)}")
        
        # Step 1: Find candidate timestamps
        logger.info("STEP 1: Finding candidate timestamps via TranscriptAnalyzer")
        candidates = self.transcript_analyzer.find_candidates(transcript)
        logger.info(f"TranscriptAnalyzer found {len(candidates)} candidate segments")
        logger.debug(f"Candidates: {[c.get('time', 'unknown') for c in candidates[:5]]}...")
        
        enriched_questions = []
        
        for i, segment in enumerate(candidates):
            try:
                logger.info(f"--- Processing segment {i+1}/{len(candidates)} ---")
                timestamp = segment["time"]
                snippet = segment["text"]
                logger.debug(f"Timestamp: {timestamp}")
                logger.debug(f"Text snippet: {snippet[:100]}...")
                
                # Step 2: Context Validation (VLM-enhanced)
                logger.info("STEP 2: Visual context validation")
                context = self.context_validator.validate(video_path, {
                    'start': timestamp,
                    'text': snippet
                })
                
                if not context:
                    logger.warning(f"ContextValidator rejected segment {timestamp} - no valid context")
                    continue
                
                logger.info(f"ContextValidator accepted segment {timestamp}")
                logger.debug(f"Context keys: {list(context.keys())}")
                logger.debug(f"Educational concepts: {context.get('educational_concepts', [])}")
                
                # Step 3: Generate Questions (Easy, Medium, Hard)
                logger.info("STEP 3: Multi-difficulty question generation")
                question_obj = self.question_generator.generate_question(context, timestamp)
                
                if not question_obj or not question_obj.get('questions'):
                    logger.warning(f"QuestionGenerator failed for segment {timestamp}")
                    continue
                
                # Process each difficulty level
                difficulty_questions = question_obj.get('questions', {})
                logger.info(f"QuestionGenerator created {len(difficulty_questions)} questions for {timestamp}")
                
                # Add all difficulty-level questions to results
                for difficulty_key, question_data in difficulty_questions.items():
                    if question_data:
                        logger.debug(f"Processing {difficulty_key}: {question_data.get('type', 'unknown')} question")
                        
                        # Extract difficulty from key (easy_question -> easy)
                        difficulty_level = difficulty_key.replace('_question', '')
                        
                        # Ensure consistency between outer and inner difficulty
                        question_data['difficulty'] = difficulty_level
                        
                        # Create individual question object
                        individual_question = {
                            'question': question_data,
                            'timestamp': timestamp,
                            'segment_context': context
                        }
                        
                        # Step 4: Rate Quality (difficulty already set by generator)
                        logger.debug(f"STEP 4: Quality rating for {difficulty_key}")
                        try:
                            quality_score = self.difficulty_rater.rate_quality(individual_question, context) if hasattr(self.difficulty_rater, 'rate_quality') else 8.0
                        except:
                            quality_score = 8.0
                        individual_question["question"]["quality_score"] = quality_score
                        
                        enriched_questions.append(individual_question)
                        logger.info(f"Successfully processed {difficulty_key} question for segment {timestamp}")
                
            except Exception as e:
                logger.error(f"Error processing segment {timestamp}: {str(e)}", exc_info=True)
                continue
        
        logger.info("=== PIPELINE END ===")
        logger.info(f"Generated {len(enriched_questions)} total questions from {len(candidates)} candidates")
        return enriched_questions
