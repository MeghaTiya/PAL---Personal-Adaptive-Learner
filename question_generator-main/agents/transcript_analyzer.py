"""
Agent 1: Transcript Analyzer
Scans transcript to detect candidate timestamps using linguistic cues
"""

import logging
from typing import List, Dict
import re

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    """
    Analyzes transcript to find segments suitable for question generation
    """
    
    def __init__(self):
        # Keywords that indicate good question candidates
        self.definition_keywords = [
            "is defined as", "means that", "refers to", "is called",
            "definition of", "term for", "describes"
        ]
        
        self.emphasis_keywords = [
            "important", "note that", "remember", "key point",
            "significant", "crucial", "essential", "critical"
        ]
        
        self.example_keywords = [
            "for example", "for instance", "such as", "like",
            "consider", "imagine", "suppose"
        ]
        
        self.transition_keywords = [
            "now let's", "next we", "moving on", "another",
            "furthermore", "additionally", "moreover"
        ]
    
    def find_candidates(self, transcript: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Find candidate segments for question generation
        
        Args:
            transcript: List of transcript segments with 'time' and 'text' keys
            
        Returns:
            List of candidate segments
        """
        candidates = []
        
        for segment in transcript:
            text = segment["text"].lower().strip()
            
            if not text or len(text) < 20:  # Skip very short segments
                continue
            
            score = self._calculate_segment_score(text)
            
            if score > 0:
                candidate = {
                    "time": segment["time"],
                    "text": segment["text"],
                    "score": score
                }
                candidates.append(candidate)
        
        # Sort by score (highest first) and return top candidates
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit to top 50 candidates to avoid overwhelming
        max_candidates = min(50, len(candidates))
        
        logger.info(f"Selected {max_candidates} candidates from {len(transcript)} segments")
        return candidates[:max_candidates]
    
    def _calculate_segment_score(self, text: str) -> int:
        """
        Calculate a score for how likely a segment is to be good for questions
        
        Args:
            text: Transcript text segment
            
        Returns:
            Score (higher = better candidate)
        """
        score = 0
        
        # Check for definition patterns
        for keyword in self.definition_keywords:
            if keyword in text:
                score += 3
        
        # Check for emphasis patterns
        for keyword in self.emphasis_keywords:
            if keyword in text:
                score += 2
        
        # Check for example patterns
        for keyword in self.example_keywords:
            if keyword in text:
                score += 2
        
        # Check for transition patterns
        for keyword in self.transition_keywords:
            if keyword in text:
                score += 1
        
        # Bonus for question words (might be rhetorical questions being answered)
        question_words = ["what", "why", "how", "when", "where", "who"]
        for word in question_words:
            if f" {word} " in text:
                score += 1
        
        # Bonus for longer segments (more content to work with)
        if len(text) > 100:
            score += 1
        if len(text) > 200:
            score += 1
        
        # Bonus for technical terms (likely educational content)
        technical_patterns = [
            r'\b[A-Z][a-z]*[A-Z][a-z]*\b',  # CamelCase words
            r'\b\w+ly\b',  # Adverbs (often used in explanations)
            r'\b\d+\.\d+\b',  # Numbers with decimals
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, text):
                score += 1
        
        return score
