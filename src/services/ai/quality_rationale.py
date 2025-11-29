"""AI-powered quality assessment rationale generation service using PydanticAI."""

import logging
from typing import Dict, Any, Optional

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from ...models.content_source import ContentSource

logger = logging.getLogger(__name__)


class QualityRationaleGenerator:
    """AI service for generating detailed rationales for quality assessment scores."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the rationale generator with a specific AI model."""
        
        try:
            self.model = OpenAIModel(model_name)
            self.agent = Agent(
                model=self.model,
                system_prompt=self._get_system_prompt(),
                retries=2
            )
            logger.info(f"QualityRationaleGenerator initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize QualityRationaleGenerator: {e}")
            # Fallback to a basic implementation
            self.agent = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for quality rationale generation."""
        
        return """
        You are an expert quality assessor. Your task is to generate detailed, objective rationales 
        explaining quality assessment scores for research content.
        
        Your rationales should:
        - Explain why each score was assigned
        - Reference specific aspects of the content
        - Be objective and evidence-based
        - Highlight both strengths and weaknesses
        - Provide actionable insights for improvement
        
        Structure your rationale with:
        1. Overall assessment summary
        2. Breakdown by quality dimension (credibility, relevance, freshness, completeness)
        3. Key strengths identified
        4. Areas for improvement
        5. Final recommendation
        
        Be specific and reference actual content elements (titles, descriptions, metadata) 
        rather than making generic statements.
        
        Maintain a professional, academic tone throughout.
        """
    
    async def generate_rationale(self, content_source: ContentSource, 
                               credibility_score: float, relevance_score: float,
                               freshness_score: float, completeness_score: float) -> Optional[str]:
        """Generate a detailed rationale explaining the quality assessment scores."""
        
        try:
            # If AI agent is not available, use fallback method
            if not self.agent:
                return self._fallback_rationale(content_source, credibility_score, relevance_score,
                                              freshness_score, completeness_score)
            
            # Prepare content and scores for rationale generation
            rationale_prompt = self._prepare_rationale_prompt(content_source, credibility_score,
                                                            relevance_score, freshness_score,
                                                            completeness_score)
            
            # Generate rationale using AI
            result = await self.agent.run(rationale_prompt)
            
            rationale = str(result.data).strip()
            
            # Validate rationale quality
            if self._validate_rationale(rationale, content_source):
                logger.info(f"Generated quality rationale for {content_source.url}")
                return rationale
            else:
                logger.warning(f"Rationale validation failed for {content_source.url}, using fallback")
                return self._fallback_rationale(content_source, credibility_score, relevance_score,
                                              freshness_score, completeness_score)
                
        except Exception as e:
            logger.error(f"AI rationale generation failed for {content_source.url}: {e}")
            return self._fallback_rationale(content_source, credibility_score, relevance_score,
                                          freshness_score, completeness_score)
    
    def _prepare_rationale_prompt(self, content_source: ContentSource,
                                credibility_score: float, relevance_score: float,
                                freshness_score: float, completeness_score: float) -> str:
        """Prepare prompt for rationale generation."""
        
        overall_score = self._calculate_overall_score(credibility_score, relevance_score,
                                                    freshness_score, completeness_score)
        
        prompt_parts = [
            f"Content Quality Assessment Rationale Request",
            f"Content Source: {content_source.url}",
            f"Title: {content_source.title}",
            f"Description: {content_source.description}",
            "",
            f"Quality Scores:",
            f"- Credibility: {credibility_score:.2f}/1.0",
            f"- Relevance: {relevance_score:.2f}/1.0", 
            f"- Freshness: {freshness_score:.2f}/1.0",
            f"- Completeness: {completeness_score:.2f}/1.0",
            f"- Overall: {overall_score:.2f}/1.0",
            "",
            "Please generate a detailed rationale explaining these scores. Focus on:",
            "1. Why each dimension received its specific score",
            "2. Specific content elements that influenced the scores",
            "3. Strengths and weaknesses of the content",
            "4. Recommendations for content quality improvement",
            "5. Overall assessment of the content's value for research purposes"
        ]
        
        # Add content excerpt if available
        if hasattr(content_source, 'content') and content_source.content:
            content_excerpt = content_source.content[:1000] + "..." if len(content_source.content) > 1000 else content_source.content
            prompt_parts.extend([
                "",
                "Content Excerpt:",
                content_excerpt
            ])
        
        return "\n".join(prompt_parts)
    
    def _calculate_overall_score(self, credibility: float, relevance: float,
                               freshness: float, completeness: float) -> float:
        """Calculate weighted overall score."""
        
        weights = {
            "credibility": 0.4,
            "relevance": 0.3, 
            "freshness": 0.2,
            "completeness": 0.1
        }
        
        return (credibility * weights["credibility"] +
                relevance * weights["relevance"] +
                freshness * weights["freshness"] +
                completeness * weights["completeness"])
    
    def _validate_rationale(self, rationale: str, content_source: ContentSource) -> bool:
        """Validate that the rationale meets quality standards."""
        
        if not rationale or len(rationale.strip()) < 100:
            logger.warning("Rationale too short")
            return False
        
        if len(rationale) > 5000:
            logger.warning("Rationale too long")
            return False
        
        # Check for common AI failure patterns
        failure_indicators = [
            "I cannot generate", "I don't have enough information",
            "As an AI", "I'm sorry", "Unable to", "Cannot generate"
        ]
        
        for indicator in failure_indicators:
            if indicator.lower() in rationale.lower():
                logger.warning(f"AI failure indicator found: {indicator}")
                return False
        
        # Check that rationale references the content
        if content_source.title and content_source.title.lower() not in rationale.lower():
            logger.warning("Rationale doesn't reference content title")
            return False
        
        # Check for key rationale components
        required_components = [
            "credibility", "relevance", "freshness", "completeness",
            "strength", "weakness", "recommendation"
        ]
        
        found_components = 0
        rationale_lower = rationale.lower()
        for component in required_components:
            if component in rationale_lower:
                found_components += 1
        
        if found_components < 4:  # Require at least 4 key components
            logger.warning("Rationale missing key components")
            return False
        
        return True
    
    def _fallback_rationale(self, content_source: ContentSource,
                          credibility_score: float, relevance_score: float,
                          freshness_score: float, completeness_score: float) -> str:
        """Fallback rationale generation method when AI is unavailable."""
        
        logger.info(f"Using fallback rationale generation for {content_source.url}")
        
        overall_score = self._calculate_overall_score(credibility_score, relevance_score,
                                                    freshness_score, completeness_score)
        
        rationale_parts = [
            f"Quality Assessment Rationale for: {content_source.title or content_source.url}",
            f"Overall Score: {overall_score:.2f}/1.0",
            "",
            "Score Breakdown:",
            f"- Credibility: {credibility_score:.2f}/1.0 - Based on source reputation and content quality indicators",
            f"- Relevance: {relevance_score:.2f}/1.0 - Based on topic alignment and content depth",
            f"- Freshness: {freshness_score:.2f}/1.0 - Based on publication date and temporal relevance", 
            f"- Completeness: {completeness_score:.2f}/1.0 - Based on content depth and structural elements",
            "",
            "Assessment Summary:"
        ]
        
        # Add score-based summary
        if overall_score >= 0.8:
            rationale_parts.append("This content demonstrates high quality across multiple dimensions.")
        elif overall_score >= 0.6:
            rationale_parts.append("This content shows good quality with some areas for improvement.")
        elif overall_score >= 0.4:
            rationale_parts.append("This content has moderate quality with significant improvement opportunities.")
        else:
            rationale_parts.append("This content has low quality and may not be suitable for research purposes.")
        
        # Add specific recommendations based on lowest scores
        scores = {
            "credibility": credibility_score,
            "relevance": relevance_score,
            "freshness": freshness_score,
            "completeness": completeness_score
        }
        
        lowest_dimension = min(scores, key=scores.get)
        lowest_score = scores[lowest_dimension]
        
        if lowest_score < 0.5:
            rationale_parts.append(f"Primary area for improvement: {lowest_dimension.title()} (score: {lowest_score:.2f})")
        
        rationale_parts.extend([
            "",
            "Note: This is an automated assessment. For detailed analysis, please review the original content."
        ])
        
        return "\n".join(rationale_parts)
    
    async def generate_comparative_rationale(self, content_sources: list, 
                                           scores_matrix: Dict[str, Dict[str, float]]) -> Optional[str]:
        """Generate comparative rationale analyzing multiple content sources."""
        
        try:
            if not self.agent:
                return self._fallback_comparative_rationale(content_sources, scores_matrix)
            
            comparative_prompt = self._prepare_comparative_prompt(content_sources, scores_matrix)
            
            result = await self.agent.run(comparative_prompt)
            
            comparative_rationale = str(result.data).strip()
            
            if self._validate_comparative_rationale(comparative_rationale, content_sources):
                logger.info(f"Generated comparative rationale for {len(content_sources)} sources")
                return comparative_rationale
            else:
                return self._fallback_comparative_rationale(content_sources, scores_matrix)
                
        except Exception as e:
            logger.error(f"Comparative rationale generation failed: {e}")
            return self._fallback_comparative_rationale(content_sources, scores_matrix)
    
    def _prepare_comparative_prompt(self, content_sources: list, 
                                  scores_matrix: Dict[str, Dict[str, float]]) -> str:
        """Prepare prompt for comparative rationale generation."""
        
        prompt_parts = [
            "Comparative Quality Assessment Rationale",
            "Please analyze and compare the following content sources:",
            ""
        ]
        
        for i, content_source in enumerate(content_sources, 1):
            source_scores = scores_matrix.get(str(content_source.id), {})
            overall_score = self._calculate_overall_score(
                source_scores.get('credibility', 0.5),
                source_scores.get('relevance', 0.5),
                source_scores.get('freshness', 0.5),
                source_scores.get('completeness', 0.5)
            )
            
            source_info = f"Source {i}: {content_source.title or content_source.url}"
            source_info += f" (Overall: {overall_score:.2f})"
            source_info += f"\n- Credibility: {source_scores.get('credibility', 0.5):.2f}"
            source_info += f"\n- Relevance: {source_scores.get('relevance', 0.5):.2f}"
            source_info += f"\n- Freshness: {source_scores.get('freshness', 0.5):.2f}"
            source_info += f"\n- Completeness: {source_scores.get('completeness', 0.5):.2f}"
            
            prompt_parts.append(source_info)
        
        prompt_parts.extend([
            "",
            "Please provide a comparative analysis that:",
            "1. Identifies the highest and lowest quality sources",
            "2. Explains score differences across sources",
            "3. Highlights patterns in quality dimensions",
            "4. Provides recommendations for source selection",
            "5. Suggests areas for content improvement across the set"
        ])
        
        return "\n".join(prompt_parts)
    
    def _validate_comparative_rationale(self, rationale: str, content_sources: list) -> bool:
        """Validate comparative rationale quality."""
        
        if not rationale or len(rationale.strip()) < 200:
            return False
        
        # Check that rationale references multiple sources
        source_references = 0
        for content_source in content_sources:
            if content_source.title and content_source.title.lower() in rationale.lower():
                source_references += 1
        
        if source_references < min(2, len(content_sources)):
            logger.warning("Comparative rationale doesn't reference enough sources")
            return False
        
        return True
    
    def _fallback_comparative_rationale(self, content_sources: list,
                                      scores_matrix: Dict[str, Dict[str, float]]) -> str:
        """Fallback for comparative rationale generation."""
        
        source_count = len(content_sources)
        
        # Calculate average scores
        avg_scores = {}
        for dimension in ['credibility', 'relevance', 'freshness', 'completeness']:
            dimension_scores = [scores_matrix.get(str(cs.id), {}).get(dimension, 0.5) 
                              for cs in content_sources]
            avg_scores[dimension] = sum(dimension_scores) / len(dimension_scores)
        
        overall_avg = self._calculate_overall_score(avg_scores['credibility'], avg_scores['relevance'],
                                                  avg_scores['freshness'], avg_scores['completeness'])
        
        return f"Comparative analysis of {source_count} content sources. " \
               f"Average quality scores: Credibility: {avg_scores['credibility']:.2f}, " \
               f"Relevance: {avg_scores['relevance']:.2f}, Freshness: {avg_scores['freshness']:.2f}, " \
               f"Completeness: {avg_scores['completeness']:.2f}. Overall average: {overall_avg:.2f}. " \
               f"Please review individual assessments for detailed analysis."