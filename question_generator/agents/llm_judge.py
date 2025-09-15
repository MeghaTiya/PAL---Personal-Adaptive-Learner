"""
LLM Judge for Question and Answer Quality Validation
Uses Ollama to validate and improve generated questions and answers
"""

import logging
import requests
import json
import re
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class LLMJudge:
    """
    Uses local LLM to validate and improve question quality
    """
    
    def __init__(self, ollama_url="http://localhost:11434", model_name="llama3.2:3b-instruct-q4_K_M"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available and has the model"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                return self.model_name in available_models
            return False
        except Exception as e:
            logger.warning(f"LLM Judge not available: {e}")
            return False
    
    def judge_question(self, question: dict, context: dict) -> dict:
        """
        Judge the quality of a question and return comprehensive evaluation
        
        Args:
            question: Question object with 'text', 'answer', etc.
            context: Context from validation
            
        Returns:
            Dictionary with score, difficulty, tags, and feedback
        """
        try:
            if not self.available:
                # If no LLM available, do basic validation
                logger.warning("LLM Judge not available, performing basic validation")
                
                # Basic quality checks
                question_text = question.get('text', '').lower()
                topic = question.get('topic', '').lower()
                
                # Check for nonsensical topics (filler words)
                filler_words = {'okay', 'today', 'yeah', 'um', 'uh', 'like', 'so', 'well', 'now', 'then'}
                if topic in filler_words or len(topic) < 3:
                    return {
                        'score': 2.0,  # Very low score for filler word questions
                        'difficulty': 'invalid',
                        'tags': ['invalid', 'filler_word'],
                        'feedback': f'Question topic "{topic}" appears to be a filler word, not an educational concept'
                    }
                
                # Check for very short or meaningless questions
                if len(question_text) < 10 or '?' not in question_text:
                    return {
                        'score': 3.0,
                        'difficulty': 'invalid', 
                        'tags': ['invalid', 'malformed'],
                        'feedback': 'Question appears to be malformed or too short'
                    }
                
                # If passes basic checks, give moderate score
                return {
                    'score': 6.0,  # Just below threshold to encourage manual review
                    'difficulty': 'medium',
                    'tags': [question.get('type', 'factual')],
                    'feedback': 'LLM Judge not available - basic validation passed'
                }
            
            # Extract question details
            question_text = question.get('text', '')
            question_answer = question.get('answer', '')
            question_type = question.get('type', 'factual')
            options = question.get('options', [])
            
            if not question_text or not question_answer:
                return {
                    'score': 0.0,
                    'difficulty': 'invalid',
                    'tags': ['invalid'],
                    'feedback': 'Question or answer is missing'
                }
            
            # Create comprehensive evaluation prompt
            prompt = f"""
You are an expert educational assessment evaluator. Evaluate this question comprehensively:

Question: {question_text}
Answer: {question_answer}
Type: {question_type}
"""
            
            if options:
                prompt += f"Options: {', '.join(options)}\n"
            
            prompt += f"""
Context: {context.get('summary', 'Educational video content')}

Provide a comprehensive evaluation:

1. QUALITY SCORE (1-10): Rate overall question quality
2. DIFFICULTY LEVEL: Classify as easy/medium/hard/expert
3. COGNITIVE LEVEL: Identify Bloom's taxonomy level (remember/understand/apply/analyze/evaluate/create)
4. SUBJECT TAGS: List relevant subject/topic tags
5. FEEDBACK: Brief improvement suggestions

Format as JSON:
{{
    "score": 8.5,
    "difficulty": "medium",
    "cognitive_level": "apply",
    "subject_tags": ["statistics", "correlation", "research_methods"],
    "quality_aspects": {{
        "clarity": 9,
        "relevance": 8,
        "educational_value": 9,
        "answer_quality": 8
    }},
    "feedback": "Well-structured question with clear educational purpose"
}}
"""

            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,  # Low temperature for consistent evaluation
                            "top_k": 10,
                            "top_p": 0.8
                        }
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_output = result.get('response', '').strip()
                    
                    # Parse JSON response
                    try:
                        import json
                        json_start = llm_output.find('{')
                        json_end = llm_output.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = llm_output[json_start:json_end]
                            evaluation = json.loads(json_str)
                            
                            # Ensure required fields
                            evaluation['score'] = float(evaluation.get('score', 7.0))
                            evaluation['difficulty'] = evaluation.get('difficulty', 'medium')
                            evaluation['tags'] = evaluation.get('subject_tags', [question_type])
                            evaluation['cognitive_level'] = evaluation.get('cognitive_level', 'understand')
                            
                            logger.debug(f"LLM Judge evaluation: {evaluation['score']}/10, {evaluation['difficulty']}")
                            return evaluation
                        
                    except Exception as e:
                        logger.warning(f"JSON parsing error: {e}, using fallback evaluation")
                
                # Fallback: extract score from text
                import re
                score_match = re.search(r'(\d+\.?\d*)\s*/\s*10', llm_output)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    score = 7.0
                
                return {
                    'score': score,
                    'difficulty': 'medium',
                    'tags': [question_type],
                    'cognitive_level': 'understand',
                    'feedback': 'Evaluated with basic parsing'
                }
                    
            except Exception as e:
                logger.error(f"LLM Judge API error: {e}")
                return {
                    'score': 7.0,
                    'difficulty': 'medium',
                    'tags': [question_type],
                    'cognitive_level': 'understand',
                    'feedback': f'API error: {str(e)}'
                }
                
        except Exception as e:
            logger.error(f"Error in judge_question: {e}")
            return {
                'score': 7.0,
                'difficulty': 'medium',
                'tags': [question.get('type', 'factual')],
                'cognitive_level': 'understand',
                'feedback': f'Evaluation error: {str(e)}'
            }

    def validate_and_improve_question(self, question_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and improve a question using LLM
        
        Args:
            question_obj: Question object from pipeline
            
        Returns:
            Improved question object or None if invalid
        """
        if not self.available:
            return question_obj  # Return as-is if no LLM
        
        question = question_obj['question']
        context = question_obj['context']
        
        # Extract clean content
        slide_text = context.get('slide_text', '').strip()
        transcript = self._clean_transcript(context.get('transcript_snippet', ''))
        options = question.get('options', [])
        
        # Special handling for MCQ validation
        if options and len(options) > 0:
            mcq_result = self._validate_mcq_options(
                question['text'], 
                question['answer'], 
                options,
                slide_text,
                transcript
            )
            if not mcq_result:
                # Convert to short answer if MCQ validation fails
                question_obj['question']['options'] = []
                question_obj['question']['type'] = 'short_answer'
        
        # Validate and improve
        improved_qa = self._improve_question_and_answer(
            question['text'], 
            question['answer'], 
            slide_text, 
            transcript,
            question['type']
        )
        
        if not improved_qa:
            return None  # Question failed validation
        
        # Update the question object
        question_obj['question']['text'] = improved_qa['question']
        question_obj['question']['answer'] = improved_qa['answer']
        question_obj['question']['concept'] = improved_qa['concept']
        question_obj['question']['difficulty'] = improved_qa['difficulty']
        question_obj['quality_score'] = improved_qa['quality_score']
        
        return question_obj
    
    def _improve_question_and_answer(self, question: str, answer: str, slide_text: str, 
                                   transcript: str, question_type: str) -> Optional[Dict[str, Any]]:
        """Use LLM to improve question and generate proper answer"""
        
        # Prepare context for LLM
        context = f"""
SLIDE CONTENT: {slide_text[:500] if slide_text else 'No slide content'}

TRANSCRIPT: {transcript[:300] if transcript else 'No transcript'}
""".strip()
        
        prompt = f"""You are an educational content expert. Given the educational content below, create a high-quality question and answer.

{context}

CURRENT QUESTION: {question}
CURRENT ANSWER: {answer[:200]}

Task: Create a better educational question and complete answer based on the content above.

Requirements:
1. Question should be clear, educational, and well-formed
2. Answer should be complete, accurate, and based on the provided content
3. Focus on key educational concepts from the slide content
4. Question type should be: {question_type}

Output format (JSON only):
{{
    "question": "improved question text",
    "answer": "complete accurate answer",
    "concept": "main educational concept",
    "difficulty": "easy|medium|hard",
    "quality_score": 1-10,
    "reasoning": "why this is a good question"
}}"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_output = result.get("response", "").strip()
                
                # Try to parse JSON output
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                    if json_match:
                        improved_qa = json.loads(json_match.group(0))
                        
                        # Validate output
                        required_fields = ['question', 'answer', 'concept', 'difficulty', 'quality_score']
                        if all(field in improved_qa for field in required_fields):
                            # Quality threshold
                            if improved_qa.get('quality_score', 0) >= 6:
                                return improved_qa
                            else:
                                logger.info(f"Question quality too low: {improved_qa.get('quality_score')}")
                                return None
                        else:
                            logger.warning("LLM output missing required fields")
                            return None
                    else:
                        logger.warning("No JSON found in LLM response")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM JSON output: {e}")
                    return None
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling LLM judge: {e}")
            return None
    
    def _clean_transcript(self, transcript: str) -> str:
        """Clean transcript text of artifacts"""
        if not transcript:
            return ""
        
        # Remove UUID artifacts
        cleaned = re.sub(r'ffcb0144-[a-f0-9-]+/\d+-\d+', '', transcript)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _validate_mcq_options(self, question: str, answer: str, options: List[str], 
                             slide_text: str, transcript: str) -> bool:
        """
        Validate MCQ options for quality issues
        
        Returns:
            bool: True if options are acceptable, False if they should be removed
        """
        
        if not options or len(options) < 2:
            return False
        
        # Check for common quality issues
        issues = []
        
        # Check for duplicates or near-duplicates
        unique_options = set()
        for option in options:
            clean_option = option.replace(' (incorrect)', '').strip().lower()
            if clean_option in unique_options:
                issues.append("duplicate_options")
            unique_options.add(clean_option)
        
        # Check for nonsensical patterns
        for option in options:
            if option.startswith('Not ') and not any(word in option.lower() for word in ['not applicable', 'not possible', 'not correct']):
                issues.append("nonsensical_not_prefix")
            
            if option.endswith(' that you') or option.endswith(' key that you'):
                issues.append("incomplete_sentence")
            
            if 'rwase' in option or any(artifact in option for artifact in ['ffcb0144', '°', '©']):
                issues.append("spelling_artifacts")
            
            if option.startswith('/') or option.isupper() and len(option) > 10:
                issues.append("title_fragment")
        
        # If any major issues found, reject the MCQ
        return len(issues) == 0
