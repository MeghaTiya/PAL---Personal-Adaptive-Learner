"""
Agent 4: Difficulty Rater  
Hybrid strategy combining rule-based classification with LLM fallback
"""

import logging
import re
from typing import Dict, Any
import requests
import json
import os

logger = logging.getLogger(__name__)

class DifficultyRater:
    """
    Rates question difficulty using hybrid approach:
    1. Rule-based classification
    2. LLM fallback for uncertain cases
    """
    
    def __init__(self):
        # Initialize Ollama client
        self.llm_available = False
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.model_name = os.getenv('OLLAMA_MODEL', 'llama3.1:8b-instruct-q4_K_M')
        
        try:
            # Test Ollama connection
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.model_name in available_models:
                    self.llm_available = True
                    logger.info(f"Ollama initialized with model: {self.model_name}")
                else:
                    # Try to find any available instruct model
                    instruct_models = [m for m in available_models if 'instruct' in m.lower()]
                    if instruct_models:
                        self.model_name = instruct_models[0]
                        self.llm_available = True
                        logger.info(f"Using available model: {self.model_name}")
                    else:
                        logger.warning("No suitable instruct model found in Ollama")
            else:
                logger.warning("Could not connect to Ollama server")
        except Exception as e:
            logger.warning(f"Could not initialize Ollama: {str(e)}")
        
        # Rule-based classification patterns
        self.easy_patterns = [
            # Recall/Recognition keywords
            r'\b(?:define|definition|what is|name|list|identify|recall|state)\b',
            r'\b(?:who|when|where|which)\b',
            # Simple factual patterns
            r'\bmeans?\b',
            r'\bcalled\b',
            r'\brefers? to\b',
        ]
        
        self.medium_patterns = [
            # Comprehension/Understanding keywords  
            r'\b(?:why|explain|describe|compare|contrast|summarize)\b',
            r'\b(?:reason|cause|effect|purpose|significance)\b',
            r'\b(?:how does|how is|how are)\b',
            r'\b(?:relationship|difference|similarity)\b',
        ]
        
        self.hard_patterns = [
            # Application/Analysis/Synthesis keywords
            r'\b(?:apply|use|implement|solve|predict|analyze)\b',
            r'\b(?:evaluate|assess|judge|critique|argue)\b', 
            r'\b(?:create|design|develop|propose|formulate)\b',
            r'\b(?:scenario|situation|case|given|if.*then)\b',
            r'\b(?:what would happen|what if|suppose)\b',
        ]
    
    def rate_difficulty(self, question: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Rate question difficulty using hybrid approach
        
        Args:
            question: Question dictionary with text and metadata
            context: Context used to generate the question
            
        Returns:
            Difficulty level: 'easy', 'medium', or 'hard'
        """
        question_text = question.get("text", "").lower()
        question_type = question.get("type", "")
        
        # Step 1: Try rule-based classification
        rule_based_difficulty = self._rule_based_classification(question_text, question_type)
        
        if rule_based_difficulty:
            logger.info(f"Rule-based classification: {rule_based_difficulty}")
            return rule_based_difficulty
        
        # Step 2: Use content-based heuristics
        content_difficulty = self._content_based_rating(question, context)
        if content_difficulty:
            logger.info(f"Content-based rating: {content_difficulty}")
            return content_difficulty
        
        # Step 3: Fallback to LLM if available
        if self.llm_available:
            try:
                llm_difficulty = self._llm_classification(question, context)
                if llm_difficulty:
                    logger.info(f"LLM classification: {llm_difficulty}")
                    return llm_difficulty
            except Exception as e:
                logger.warning(f"LLM classification failed: {str(e)}")
        
        # Final fallback based on question type
        type_difficulty = self._type_based_fallback(question_type)
        logger.info(f"Type-based fallback: {type_difficulty}")
        return type_difficulty
    
    def _rule_based_classification(self, question_text: str, question_type: str) -> str:
        """
        Classify difficulty using keyword patterns
        
        Args:
            question_text: Question text (lowercase)
            question_type: Question type
            
        Returns:
            Difficulty or empty string if uncertain
        """
        # Check for hard patterns first (most specific)
        for pattern in self.hard_patterns:
            if re.search(pattern, question_text, re.IGNORECASE):
                return "hard"
        
        # Then medium patterns
        for pattern in self.medium_patterns:
            if re.search(pattern, question_text, re.IGNORECASE):
                return "medium"
        
        # Finally easy patterns
        for pattern in self.easy_patterns:
            if re.search(pattern, question_text, re.IGNORECASE):
                return "easy"
        
        return ""  # Uncertain
    
    def _content_based_rating(self, question: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Rate difficulty based on content complexity
        
        Args:
            question: Question dictionary
            context: Context dictionary
            
        Returns:
            Difficulty level or empty string if uncertain
        """
        transcript = context.get("transcript_snippet", "")
        question_text = question.get("text", "")
        answer = question.get("answer", "")
        
        complexity_score = 0
        
        # Answer length (longer = potentially more complex)
        if len(answer) > 200:
            complexity_score += 2
        elif len(answer) > 100:
            complexity_score += 1
        
        # Technical vocabulary (more = higher complexity)
        technical_terms = self._count_technical_terms(transcript + " " + question_text)
        complexity_score += min(technical_terms, 3)
        
        # Multiple concepts (indicated by conjunctions)
        conjunctions = ["and", "but", "however", "therefore", "because", "since"]
        conjunction_count = sum(1 for conj in conjunctions if conj in transcript.lower())
        complexity_score += min(conjunction_count, 2)
        
        # Numbers and formulas (indicate complexity)
        if re.search(r'\d+', transcript) or re.search(r'[=<>]', transcript):
            complexity_score += 1
        
        # Classification based on score
        if complexity_score >= 5:
            return "hard"
        elif complexity_score >= 3:
            return "medium"
        elif complexity_score >= 1:
            return "easy"
        
        return ""  # Still uncertain
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""
        # Simple heuristics for technical terms
        technical_indicators = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b[a-z]+(?:tion|sion|ment|ance|ence|ness|ity)\b',  # Abstract nouns
            r'\b[A-Z][a-z]*[A-Z][a-z]*\b',  # CamelCase
            r'\b\w{8,}\b',  # Long words (often technical)
        ]
        
        count = 0
        for pattern in technical_indicators:
            matches = re.findall(pattern, text)
            count += len(matches)
        
        return count
    
    def _llm_classification(self, question: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Use Ollama LLM to classify difficulty
        
        Args:
            question: Question dictionary
            context: Context dictionary
            
        Returns:
            Difficulty level from LLM
        """
        question_text = question.get("text", "")
        transcript = context.get("transcript_snippet", "")
        
        prompt = f"""You are an educational assessment expert. Rate the difficulty of this educational question on a scale of easy/medium/hard.

Question: {question_text}
Context: {transcript[:500]}

Difficulty levels:
- easy: Simple recall, recognition, or basic factual questions (What is X? Define Y.)
- medium: Questions requiring understanding, explanation, or comparison (Why does X happen? How does Y work?)
- hard: Questions requiring application, analysis, evaluation, or synthesis (Apply X to solve Y. What would happen if Z?)

Respond with only one word: easy, medium, or hard."""
        
        try:
            # Ollama API call
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 10
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                difficulty = result.get("response", "").strip().lower()
                
                # Extract just the difficulty word if there's extra text
                for level in ["easy", "medium", "hard"]:
                    if level in difficulty:
                        return level
                
                logger.warning(f"Unexpected Ollama response: {difficulty}")
                return ""
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Ollama classification error: {str(e)}")
            return ""
    
    def _type_based_fallback(self, question_type: str) -> str:
        """
        Final fallback based on question type
        
        Args:
            question_type: Type of question
            
        Returns:
            Default difficulty for the type
        """
        type_defaults = {
            "factual": "easy",
            "conceptual": "medium", 
            "application": "hard"
        }
        
        return type_defaults.get(question_type, "medium")
