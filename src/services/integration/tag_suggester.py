"""Tag suggestion service for recommending relevant tags for content sources."""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.content_source import ContentSource
from ...services.integration.semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)


class TagSuggester:
    """Suggests relevant tags for content sources based on content analysis and existing knowledge."""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        
        # Predefined tag categories and patterns
        self.tag_categories = {
            "topic": {
                "patterns": ["topic", "subject", "theme", "domain", "field"],
                "weight": 1.0
            },
            "methodology": {
                "patterns": ["method", "approach", "technique", "framework", "model"],
                "weight": 0.8
            },
            "technology": {
                "patterns": ["technology", "tool", "software", "platform", "system"],
                "weight": 0.9
            },
            "concept": {
                "patterns": ["concept", "principle", "theory", "idea", "notion"],
                "weight": 0.7
            },
            "application": {
                "patterns": ["application", "use case", "implementation", "deployment"],
                "weight": 0.6
            }
        }
        
        # Common stop words to filter out
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "as", "is", "are", "was", "were", "be", "been", 
            "have", "has", "had", "do", "does", "did", "will", "would", "could", 
            "should", "may", "might", "can", "this", "that", "these", "those"
        }
    
    async def suggest_tags(self, db: AsyncSession, content_source: ContentSource, 
                          max_tags: int = 15) -> List[Dict[str, Any]]:
        """Suggest relevant tags for a content source."""
        
        try:
            # Extract content for analysis
            content_text = self._extract_content_text(content_source)
            
            # Generate tag suggestions using multiple methods
            keyword_tags = self._extract_keyword_tags(content_text)
            semantic_tags = await self._generate_semantic_tags(db, content_source, content_text)
            contextual_tags = self._generate_contextual_tags(content_source)
            existing_knowledge_tags = await self._suggest_from_existing_knowledge(db, content_source)
            
            # Combine and deduplicate tags
            all_tags = self._combine_and_deduplicate_tags(
                keyword_tags, semantic_tags, contextual_tags, existing_knowledge_tags
            )
            
            # Score and rank tags
            scored_tags = self._score_and_rank_tags(all_tags, content_text, content_source)
            
            # Limit to max tags
            final_tags = scored_tags[:max_tags]
            
            logger.info(f"Generated {len(final_tags)} tag suggestions for content source {content_source.id}")
            return final_tags
            
        except Exception as e:
            logger.error(f"Failed to suggest tags for content source {content_source.id}: {e}")
            return []
    
    def _extract_content_text(self, content_source: ContentSource) -> str:
        """Extract text content for tag analysis."""
        
        text_parts = []
        
        if content_source.title:
            text_parts.append(content_source.title)
        
        if content_source.description:
            text_parts.append(content_source.description)
        
        if hasattr(content_source, 'content') and content_source.content:
            # Limit content length for efficiency
            content = content_source.content[:5000]  # First 5000 characters
            text_parts.append(content)
        
        return " ".join(text_parts)
    
    def _extract_keyword_tags(self, content_text: str) -> List[Dict[str, Any]]:
        """Extract keyword-based tags from content text."""
        
        # Clean and tokenize text
        words = self._tokenize_text(content_text)
        
        # Filter out stop words and short words
        candidate_words = [
            word for word in words 
            if len(word) > 2 and word.lower() not in self.stop_words
        ]
        
        # Calculate word frequencies
        word_freq = {}
        for word in candidate_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Generate keyword tags
        keyword_tags = []
        for word, freq in word_freq.items():
            if freq >= 2:  # Only include words that appear at least twice
                tag = {
                    "tag": word.lower(),
                    "source": "keyword_extraction",
                    "confidence": min(1.0, freq / 10),  # Normalize confidence
                    "category": self._categorize_tag(word),
                    "frequency": freq
                }
                keyword_tags.append(tag)
        
        return keyword_tags
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words, handling various separators."""
        
        # Convert to lowercase and split on word boundaries
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', text.lower())
        return words
    
    def _categorize_tag(self, tag: str) -> str:
        """Categorize a tag based on patterns."""
        
        tag_lower = tag.lower()
        
        for category, config in self.tag_categories.items():
            for pattern in config["patterns"]:
                if pattern in tag_lower:
                    return category
        
        return "general"
    
    async def _generate_semantic_tags(self, db: AsyncSession, content_source: ContentSource, 
                                    content_text: str) -> List[Dict[str, Any]]:
        """Generate semantic tags based on content meaning."""
        
        try:
            # Get semantic neighbors to understand context
            neighbors = await self.semantic_analyzer.get_semantic_neighbors(db, content_source, 5)
            
            semantic_tags = []
            
            for neighbor in neighbors:
                # Extract meaningful terms from neighbor titles/descriptions
                neighbor_text = f"{neighbor.get('title', '')} {neighbor.get('description', '')}"
                neighbor_tags = self._extract_keyword_tags(neighbor_text)
                
                # Adjust confidence based on similarity
                similarity = neighbor.get('similarity_score', 0.0)
                for tag in neighbor_tags:
                    tag["confidence"] *= similarity  # Scale by similarity
                    tag["source"] = "semantic_analysis"
                    semantic_tags.append(tag)
            
            return semantic_tags
            
        except Exception as e:
            logger.error(f"Failed to generate semantic tags: {e}")
            return []
    
    def _generate_contextual_tags(self, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Generate tags based on content source context and metadata."""
        
        contextual_tags = []
        
        # Source-based tags
        if content_source.source_type:
            tag = {
                "tag": f"source:{content_source.source_type.lower()}",
                "source": "contextual_analysis",
                "confidence": 0.9,
                "category": "source_type"
            }
            contextual_tags.append(tag)
        
        # Domain-based tags (if available)
        if hasattr(content_source, 'domain') and content_source.domain:
            tag = {
                "tag": f"domain:{content_source.domain.lower()}",
                "source": "contextual_analysis",
                "confidence": 0.8,
                "category": "domain"
            }
            contextual_tags.append(tag)
        
        # Content type tags
        content_type = self._infer_content_type(content_source)
        if content_type:
            tag = {
                "tag": f"type:{content_type}",
                "source": "contextual_analysis",
                "confidence": 0.7,
                "category": "content_type"
            }
            contextual_tags.append(tag)
        
        return contextual_tags
    
    def _infer_content_type(self, content_source: ContentSource) -> Optional[str]:
        """Infer content type based on available information."""
        
        if not content_source.title and not content_source.description:
            return None
        
        text = f"{content_source.title or ''} {content_source.description or ''}".lower()
        
        content_type_indicators = {
            "research": ["study", "research", "paper", "article", "journal"],
            "tutorial": ["tutorial", "guide", "how-to", "step-by-step", "walkthrough"],
            "news": ["news", "update", "announcement", "release", "report"],
            "opinion": ["opinion", "view", "perspective", "analysis", "commentary"],
            "technical": ["technical", "specification", "documentation", "api", "sdk"]
        }
        
        for content_type, indicators in content_type_indicators.items():
            if any(indicator in text for indicator in indicators):
                return content_type
        
        return "general"
    
    async def _suggest_from_existing_knowledge(self, db: AsyncSession, 
                                             content_source: ContentSource) -> List[Dict[str, Any]]:
        """Suggest tags based on existing knowledge base patterns."""
        
        try:
            # This would typically query existing tags from the knowledge base
            # For now, use a simplified approach with common academic/professional tags
            
            common_tags = [
                {"tag": "ai", "confidence": 0.6, "category": "technology"},
                {"tag": "machine-learning", "confidence": 0.5, "category": "technology"},
                {"tag": "data-science", "confidence": 0.5, "category": "field"},
                {"tag": "research", "confidence": 0.7, "category": "topic"},
                {"tag": "innovation", "confidence": 0.4, "category": "concept"},
                {"tag": "best-practices", "confidence": 0.5, "category": "methodology"}
            ]
            
            # Adjust confidence based on content relevance
            content_text = self._extract_content_text(content_source).lower()
            for tag in common_tags:
                tag_word = tag["tag"].replace("-", " ")
                if tag_word in content_text:
                    tag["confidence"] = min(1.0, tag["confidence"] + 0.3)
                tag["source"] = "existing_knowledge"
            
            return common_tags
            
        except Exception as e:
            logger.error(f"Failed to suggest tags from existing knowledge: {e}")
            return []
    
    def _combine_and_deduplicate_tags(self, *tag_lists: List[List[Dict]]) -> List[Dict[str, Any]]:
        """Combine tag lists and deduplicate by tag name."""
        
        tag_dict = {}
        
        for tag_list in tag_lists:
            for tag in tag_list:
                tag_name = tag["tag"]
                
                if tag_name in tag_dict:
                    # Merge tag information
                    existing_tag = tag_dict[tag_name]
                    existing_tag["confidence"] = max(existing_tag["confidence"], tag["confidence"])
                    # Keep the most specific category
                    if tag["category"] != "general":
                        existing_tag["category"] = tag["category"]
                    # Combine sources
                    if "sources" not in existing_tag:
                        existing_tag["sources"] = {existing_tag["source"]}
                    existing_tag["sources"].add(tag["source"])
                    existing_tag["source"] = "combined"
                else:
                    # Create new tag entry
                    tag_dict[tag_name] = tag.copy()
                    tag_dict[tag_name]["sources"] = {tag["source"]}
        
        # Convert back to list
        combined_tags = list(tag_dict.values())
        
        return combined_tags
    
    def _score_and_rank_tags(self, tags: List[Dict[str, Any]], 
                           content_text: str, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Score and rank tags based on relevance and importance."""
        
        scored_tags = []
        
        for tag in tags:
            # Base score from confidence
            base_score = tag.get("confidence", 0.0)
            
            # Adjust score based on category importance
            category = tag.get("category", "general")
            category_weight = self.tag_categories.get(category, {}).get("weight", 0.5)
            category_adjusted_score = base_score * category_weight
            
            # Adjust score based on tag position (title tags are more important)
            position_score = self._calculate_position_score(tag["tag"], content_source)
            
            # Adjust score based on tag specificity (longer, more specific tags)
            specificity_score = self._calculate_specificity_score(tag["tag"])
            
            # Final score calculation
            final_score = (category_adjusted_score + position_score + specificity_score) / 3
            
            # Add scoring information to tag
            scored_tag = tag.copy()
            scored_tag["final_score"] = round(final_score, 3)
            scored_tag["scoring_breakdown"] = {
                "base_confidence": round(base_score, 3),
                "category_adjustment": round(category_adjusted_score, 3),
                "position_score": round(position_score, 3),
                "specificity_score": round(specificity_score, 3)
            }
            
            scored_tags.append(scored_tag)
        
        # Sort by final score (descending)
        scored_tags.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scored_tags
    
    def _calculate_position_score(self, tag: str, content_source: ContentSource) -> float:
        """Calculate score based on tag position in content."""
        
        position_score = 0.0
        
        # Check if tag appears in title
        if content_source.title and tag.lower() in content_source.title.lower():
            position_score += 0.8
        
        # Check if tag appears in description
        if content_source.description and tag.lower() in content_source.description.lower():
            position_score += 0.5
        
        return min(1.0, position_score)
    
    def _calculate_specificity_score(self, tag: str) -> float:
        """Calculate score based on tag specificity."""
        
        # Longer tags are generally more specific
        word_count = len(tag.split())
        
        if word_count >= 3:
            return 0.9
        elif word_count == 2:
            return 0.7
        else:
            return 0.5
    
    async def suggest_hierarchical_tags(self, db: AsyncSession, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Suggest hierarchical tags (parent-child relationships)."""
        
        try:
            base_tags = await self.suggest_tags(db, content_source, 10)
            hierarchical_tags = []
            
            for base_tag in base_tags:
                # Suggest broader tags (parents)
                parent_tags = self._suggest_parent_tags(base_tag["tag"])
                hierarchical_tags.extend(parent_tags)
                
                # Suggest narrower tags (children)
                child_tags = self._suggest_child_tags(base_tag["tag"])
                hierarchical_tags.extend(child_tags)
            
            return hierarchical_tags
            
        except Exception as e:
            logger.error(f"Failed to suggest hierarchical tags: {e}")
            return []
    
    def _suggest_parent_tags(self, base_tag: str) -> List[Dict[str, Any]]:
        """Suggest broader (parent) tags."""
        
        # Simple parent tag mapping
        parent_mappings = {
            "machine-learning": ["ai", "computer-science"],
            "deep-learning": ["machine-learning", "ai"],
            "neural-networks": ["deep-learning", "machine-learning"],
            "natural-language-processing": ["ai", "linguistics"],
            "computer-vision": ["ai", "image-processing"],
            "data-analysis": ["data-science", "statistics"],
            "python": ["programming", "software-development"]
        }
        
        parent_tags = []
        for child, parents in parent_mappings.items():
            if child in base_tag:
                for parent in parents:
                    parent_tags.append({
                        "tag": parent,
                        "relationship": "parent",
                        "base_tag": base_tag,
                        "confidence": 0.6,
                        "category": "hierarchical"
                    })
        
        return parent_tags
    
    def _suggest_child_tags(self, base_tag: str) -> List[Dict[str, Any]]:
        """Suggest narrower (child) tags."""
        
        # Simple child tag mapping
        child_mappings = {
            "ai": ["machine-learning", "deep-learning", "natural-language-processing"],
            "machine-learning": ["supervised-learning", "unsupervised-learning", "reinforcement-learning"],
            "programming": ["python", "javascript", "java", "c++"],
            "data-science": ["data-analysis", "data-visualization", "statistical-modeling"]
        }
        
        child_tags = []
        for parent, children in child_mappings.items():
            if parent in base_tag:
                for child in children:
                    child_tags.append({
                        "tag": child,
                        "relationship": "child",
                        "base_tag": base_tag,
                        "confidence": 0.6,
                        "category": "hierarchical"
                    })
        
        return child_tags
    
    async def get_tag_analysis_summary(self, db: AsyncSession, content_source: ContentSource) -> Dict[str, Any]:
        """Get comprehensive tag analysis summary."""
        
        try:
            tags = await self.suggest_tags(db, content_source, 20)
            hierarchical_tags = await self.suggest_hierarchical_tags(db, content_source)
            
            # Calculate tag statistics
            tag_categories = {}
            tag_sources = {}
            tag_scores = [tag["final_score"] for tag in tags]
            
            for tag in tags:
                category = tag.get("category", "unknown")
                tag_categories[category] = tag_categories.get(category, 0) + 1
                
                source = tag.get("source", "unknown")
                tag_sources[source] = tag_sources.get(source, 0) + 1
            
            return {
                "content_source_id": str(content_source.id),
                "total_tags": len(tags),
                "hierarchical_tags": len(hierarchical_tags),
                "average_tag_score": round(sum(tag_scores) / len(tag_scores), 3) if tag_scores else 0,
                "tag_categories": tag_categories,
                "tag_sources": tag_sources,
                "primary_category": max(tag_categories, key=tag_categories.get) if tag_categories else "unknown",
                "tag_density": self._calculate_tag_density(len(tags))
            }
            
        except Exception as e:
            logger.error(f"Failed to generate tag analysis summary: {e}")
            return {"error": str(e)}
    
    def _calculate_tag_density(self, tag_count: int) -> str:
        """Calculate tag density category."""
        
        if tag_count >= 15:
            return "high"
        elif tag_count >= 8:
            return "medium"
        elif tag_count >= 3:
            return "low"
        else:
            return "very_low"