#!/usr/bin/env python3
"""
Enhanced Educational Content Analyzer
Proper extraction of educational concepts from noisy transcripts
"""

import logging
import re
from typing import List, Dict, Set, Optional
import requests
import json

logger = logging.getLogger(__name__)

class EducationalContentAnalyzer:
    """
    Extract meaningful educational concepts and filter out transcript noise
    """
    
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        
        # Educational domain indicators
        self.educational_domains = {
            'statistics': ['correlation', 'causation', 'regression', 'data', 'analysis', 'hypothesis', 'variable', 'sample'],
            'research': ['study', 'experiment', 'methodology', 'observation', 'evidence', 'findings', 'results'],
            'psychology': ['behavior', 'cognitive', 'learning', 'memory', 'perception', 'theory'],
            'science': ['theory', 'principle', 'law', 'phenomenon', 'process', 'mechanism', 'structure'],
            'mathematics': ['equation', 'formula', 'calculation', 'proof', 'theorem', 'function', 'variable'],
            'economics': ['market', 'supply', 'demand', 'price', 'inflation', 'investment', 'economy'],
            'general': ['concept', 'definition', 'example', 'principle', 'method', 'approach', 'system']
        }
        
        # Words to always exclude
        self.noise_words = {
            'filler': ['um', 'uh', 'ah', 'er', 'like', 'you know', 'basically', 'actually', 'literally'],
            'conversational': ['yeah', 'yes', 'no', 'okay', 'alright', 'well', 'so', 'now', 'today', 'here'],
            'pronouns': ['i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'],
            'articles': ['a', 'an', 'the'],
            'prepositions': ['in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'about'],
            'common': ['is', 'are', 'was', 'were', 'be', 'being', 'been', 'have', 'has', 'had', 'do', 'does', 'did'],
            'temporal': ['when', 'then', 'now', 'before', 'after', 'during', 'while', 'since'],
            'questioning': ['what', 'where', 'who', 'why', 'how', 'which'],
            'discourse': ['first', 'second', 'next', 'finally', 'also', 'moreover', 'however', 'therefore']
        }
        
        # Flatten noise words into a single set
        self.all_noise_words = set()
        for category in self.noise_words.values():
            self.all_noise_words.update([word.lower() for word in category])
    
    def extract_educational_concepts(self, transcript_text: str, visual_context: str = "") -> Dict:
        """
        Extract meaningful educational concepts from transcript and visual context
        """
        try:
            logger.info("🔍 Analyzing educational content...")
            
            # Step 1: Clean and preprocess text
            clean_text = self._preprocess_transcript(transcript_text)
            
            # Step 2: Use LLM to extract educational concepts
            educational_analysis = self._llm_concept_extraction(clean_text, visual_context)
            
            # Step 3: Validate and filter concepts
            validated_concepts = self._validate_educational_concepts(educational_analysis)
            
            # Step 4: Domain classification
            domain_info = self._classify_educational_domain(validated_concepts, clean_text)
            
            result = {
                'primary_concepts': validated_concepts.get('primary_concepts', []),
                'supporting_concepts': validated_concepts.get('supporting_concepts', []),
                'educational_domain': domain_info.get('domain', 'general'),
                'domain_confidence': domain_info.get('confidence', 0.5),
                'learning_objectives': self._generate_learning_objectives(validated_concepts),
                'question_focus': validated_concepts.get('primary_concepts', ['the topic'])[:3],
                'complexity_level': self._assess_content_complexity(clean_text, validated_concepts),
                'content_quality': self._assess_content_quality(validated_concepts)
            }
            
            logger.info(f"✅ Extracted {len(result['primary_concepts'])} primary educational concepts")
            return result
            
        except Exception as e:
            logger.error(f"❌ Educational concept extraction failed: {str(e)}")
            return self._fallback_concept_extraction(transcript_text)
    
    def _preprocess_transcript(self, text: str) -> str:
        """Clean transcript text of noise and filler"""
        try:
            # Remove empty parentheses and extra whitespace
            clean_text = re.sub(r'\(\s*\)', '', text)
            clean_text = ' '.join(clean_text.split())
            
            # Remove very short segments (likely noise)
            sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 10]
            
            # Filter out sentences that are mostly noise words
            filtered_sentences = []
            for sentence in sentences:
                words = sentence.lower().split()
                meaningful_words = [w for w in words if w not in self.all_noise_words and len(w) > 2]
                
                # Keep sentence if it has enough meaningful words
                if len(meaningful_words) >= 3:
                    filtered_sentences.append(sentence)
            
            result = '. '.join(filtered_sentences)
            logger.debug(f"Preprocessed transcript: {len(text)} -> {len(result)} chars")
            
            return result
            
        except Exception as e:
            logger.error(f"Error preprocessing transcript: {str(e)}")
            return text
    
    def _llm_concept_extraction(self, text: str, visual_context: str) -> Dict:
        """Use LLM to extract educational concepts"""
        try:
            if len(text) < 20:
                return {'concepts': [], 'topics': []}
            
            prompt = f"""
Analyze this educational content and extract meaningful concepts:

TRANSCRIPT: "{text}"
VISUAL_CONTEXT: "{visual_context}"

Extract:
1. PRIMARY_CONCEPTS: List 3-5 main educational concepts, theories, or principles discussed
2. SUPPORTING_CONCEPTS: List 3-5 supporting terms, examples, or related ideas
3. MAIN_TOPIC: What is the overall subject being taught?
4. KEY_TERMS: Important terminology that students should know

Focus ONLY on educational content. Ignore:
- Filler words (um, uh, yeah, okay)
- Conversational phrases
- Common words without educational meaning
- Pronouns and articles

Be specific and educational. If content is unclear, extract general academic concepts.

Format response as:
PRIMARY_CONCEPTS: [concept1, concept2, concept3]
SUPPORTING_CONCEPTS: [term1, term2, term3]
MAIN_TOPIC: [topic]
KEY_TERMS: [term1, term2, term3]
"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_k": 20,
                        "top_p": 0.8,
                        "num_predict": 300
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                return self._parse_llm_concept_response(analysis_text)
            else:
                logger.warning(f"LLM concept extraction failed: {response.status_code}")
                return self._fallback_concept_extraction(text)
                
        except Exception as e:
            logger.error(f"LLM concept extraction error: {str(e)}")
            return self._fallback_concept_extraction(text)
    
    def _parse_llm_concept_response(self, response_text: str) -> Dict:
        """Parse LLM response into structured concepts"""
        try:
            concepts = {
                'primary_concepts': [],
                'supporting_concepts': [],
                'main_topic': '',
                'key_terms': []
            }
            
            # Extract sections using regex
            patterns = {
                'primary_concepts': r'PRIMARY_CONCEPTS:\s*\[(.*?)\]',
                'supporting_concepts': r'SUPPORTING_CONCEPTS:\s*\[(.*?)\]',
                'main_topic': r'MAIN_TOPIC:\s*\[(.*?)\]',
                'key_terms': r'KEY_TERMS:\s*\[(.*?)\]'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1)
                    if key == 'main_topic':
                        concepts[key] = content.strip()
                    else:
                        # Parse list items
                        items = [item.strip().strip('"\'') for item in content.split(',')]
                        concepts[key] = [item for item in items if item and len(item) > 2]
            
            return concepts
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {'primary_concepts': [], 'supporting_concepts': [], 'main_topic': '', 'key_terms': []}
    
    def _validate_educational_concepts(self, concepts: Dict) -> Dict:
        """Validate that extracted concepts are actually educational"""
        try:
            validated = {
                'primary_concepts': [],
                'supporting_concepts': []
            }
            
            # Validate primary concepts
            for concept in concepts.get('primary_concepts', []):
                if self._is_educational_concept(concept):
                    validated['primary_concepts'].append(concept)
            
            # Validate supporting concepts
            for concept in concepts.get('supporting_concepts', []):
                if self._is_educational_concept(concept):
                    validated['supporting_concepts'].append(concept)
            
            # Add key terms if primary concepts are low
            if len(validated['primary_concepts']) < 2:
                for term in concepts.get('key_terms', []):
                    if self._is_educational_concept(term) and len(validated['primary_concepts']) < 3:
                        validated['primary_concepts'].append(term)
            
            # Add main topic if still low
            if len(validated['primary_concepts']) < 1 and concepts.get('main_topic'):
                main_topic = concepts['main_topic']
                if self._is_educational_concept(main_topic):
                    validated['primary_concepts'].append(main_topic)
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating concepts: {str(e)}")
            return {'primary_concepts': ['educational content'], 'supporting_concepts': []}
    
    def _is_educational_concept(self, concept: str) -> bool:
        """Check if a concept is educational and meaningful"""
        try:
            if not concept or len(concept.strip()) < 3:
                return False
            
            concept_lower = concept.lower().strip()
            
            # Reject noise words
            if concept_lower in self.all_noise_words:
                return False
            
            # Reject single letters or very short meaningless words
            if len(concept_lower) < 3 or concept_lower.isdigit():
                return False
            
            # Reject common non-educational words
            non_educational = {'thing', 'stuff', 'something', 'anything', 'everything', 'nothing'}
            if concept_lower in non_educational:
                return False
            
            # Check for educational domain indicators
            for domain, keywords in self.educational_domains.items():
                if any(keyword in concept_lower for keyword in keywords):
                    return True
            
            # Accept multi-word educational phrases
            words = concept_lower.split()
            if len(words) > 1:
                # Multi-word phrases are more likely to be educational
                meaningful_words = [w for w in words if w not in self.all_noise_words]
                return len(meaningful_words) >= 2
            
            # Single words: check if they could be educational
            if len(concept_lower) >= 5:  # Longer words more likely educational
                return True
            
            # Check if it contains academic-sounding patterns
            academic_patterns = ['tion', 'ment', 'ness', 'ism', 'ogy', 'ics']
            if any(pattern in concept_lower for pattern in academic_patterns):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking educational concept: {str(e)}")
            return False
    
    def _classify_educational_domain(self, concepts: Dict, text: str) -> Dict:
        """Classify the educational domain of the content"""
        try:
            all_concepts = concepts.get('primary_concepts', []) + concepts.get('supporting_concepts', [])
            all_text = ' '.join(all_concepts) + ' ' + text
            all_text_lower = all_text.lower()
            
            domain_scores = {}
            
            for domain, keywords in self.educational_domains.items():
                score = sum(1 for keyword in keywords if keyword in all_text_lower)
                if score > 0:
                    domain_scores[domain] = score
            
            if domain_scores:
                best_domain = max(domain_scores.keys(), key=lambda d: domain_scores[d])
                confidence = domain_scores[best_domain] / len(self.educational_domains[best_domain])
                return {'domain': best_domain, 'confidence': min(confidence, 1.0)}
            else:
                return {'domain': 'general', 'confidence': 0.5}
                
        except Exception as e:
            logger.error(f"Error classifying domain: {str(e)}")
            return {'domain': 'general', 'confidence': 0.5}
    
    def _generate_learning_objectives(self, concepts: Dict) -> str:
        """Generate learning objectives from concepts"""
        try:
            primary = concepts.get('primary_concepts', [])
            if not primary:
                return "Understand the key educational concepts presented"
            
            objectives = []
            for concept in primary[:3]:
                objectives.append(f"understand {concept}")
            
            return f"Learn to {', '.join(objectives)}"
            
        except:
            return "Understand the key educational concepts presented"
    
    def _assess_content_complexity(self, text: str, concepts: Dict) -> str:
        """Assess the complexity level of the content"""
        try:
            # Count educational indicators
            primary_count = len(concepts.get('primary_concepts', []))
            supporting_count = len(concepts.get('supporting_concepts', []))
            
            # Text complexity indicators
            sentences = text.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            
            # Calculate complexity score
            complexity_score = 0
            complexity_score += min(primary_count * 2, 6)  # Max 6 from primary concepts
            complexity_score += min(supporting_count, 4)   # Max 4 from supporting
            complexity_score += min(avg_sentence_length / 5, 4)  # Max 4 from sentence length
            
            if complexity_score >= 10:
                return 'advanced'
            elif complexity_score >= 6:
                return 'intermediate'
            else:
                return 'beginner'
                
        except:
            return 'intermediate'
    
    def _assess_content_quality(self, concepts: Dict) -> float:
        """Assess the quality of extracted educational content"""
        try:
            score = 0.0
            
            # Primary concepts bonus
            primary_count = len(concepts.get('primary_concepts', []))
            score += min(primary_count * 0.2, 0.6)  # Max 0.6
            
            # Supporting concepts bonus
            supporting_count = len(concepts.get('supporting_concepts', []))
            score += min(supporting_count * 0.1, 0.3)  # Max 0.3
            
            # Base quality if we have any concepts
            if primary_count > 0:
                score += 0.1
            
            return min(score, 1.0)
            
        except:
            return 0.5
    
    def _fallback_concept_extraction(self, text: str) -> Dict:
        """Enhanced fallback concept extraction focused on educational content"""
        try:
            logger.info("🔧 Using enhanced fallback concept extraction...")
            
            # Specific educational keywords to look for
            educational_keywords = {
                'statistics': ['correlation', 'causation', 'data', 'analysis', 'variable', 'hypothesis', 'regression', 'sample', 'population'],
                'research': ['study', 'experiment', 'methodology', 'evidence', 'findings', 'results', 'observation', 'theory'],
                'science': ['principle', 'law', 'phenomenon', 'process', 'mechanism', 'system', 'model', 'structure'],
                'concepts': ['concept', 'definition', 'example', 'principle', 'method', 'approach', 'relationship', 'factor']
            }
            
            # Find educational keywords in text
            found_concepts = []
            text_lower = text.lower()
            
            for domain, keywords in educational_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower and keyword not in found_concepts:
                        found_concepts.append(keyword)
            
            # If no educational keywords found, look for capitalized terms (likely proper nouns)
            if not found_concepts:
                # Find multi-word proper nouns or technical terms
                proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
                meaningful_nouns = []
                
                for noun in proper_nouns:
                    noun_clean = noun.strip()
                    if (len(noun_clean) > 4 and 
                        noun_clean.lower() not in self.all_noise_words and
                        not any(word in noun_clean.lower() for word in ['yeah', 'okay', 'well', 'now'])):
                        meaningful_nouns.append(noun_clean)
                
                found_concepts.extend(meaningful_nouns[:3])
            
            # Look for -tion, -ment, -ness words (likely educational concepts)
            academic_words = re.findall(r'\\b\\w*(?:tion|ment|ness|ism|ology|ics|ity)\\b', text, re.IGNORECASE)
            for word in academic_words:
                if word.lower() not in self.all_noise_words and len(word) > 4:
                    found_concepts.append(word.lower())
            
            # If still no good concepts, create domain-appropriate defaults
            if not found_concepts:
                if 'correlation' in text_lower or 'causation' in text_lower:
                    found_concepts = ['correlation', 'causation', 'statistical relationship']
                elif 'data' in text_lower:
                    found_concepts = ['data analysis', 'research methods', 'statistical inference']
                elif 'study' in text_lower or 'research' in text_lower:
                    found_concepts = ['research methodology', 'empirical evidence', 'scientific method']
                else:
                    found_concepts = ['educational concept', 'learning objective', 'academic principle']
            
            # Clean and deduplicate
            unique_concepts = list(set(found_concepts))[:8]
            
            return {
                'primary_concepts': unique_concepts[:3],
                'supporting_concepts': unique_concepts[3:6],
                'main_topic': unique_concepts[0] if unique_concepts else 'educational content',
                'key_terms': unique_concepts
            }
            
        except Exception as e:
            logger.error(f"Enhanced fallback extraction failed: {str(e)}")
            return {
                'primary_concepts': ['statistical concepts', 'research methods', 'data analysis'],
                'supporting_concepts': ['correlation', 'causation', 'evidence'],
                'main_topic': 'statistical reasoning',
                'key_terms': ['statistics', 'analysis', 'methodology']
            }
