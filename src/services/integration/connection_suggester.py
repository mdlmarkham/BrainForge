"""Connection suggestion service for recommending relationships between content sources."""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.content_source import ContentSource
from ...services.integration.semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)


class ConnectionSuggester:
    """Suggests connections and relationships between content sources for integration."""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
    
    async def suggest_connections(self, db: AsyncSession, content_source: ContentSource, 
                                max_suggestions: int = 10) -> List[Dict[str, Any]]:
        """Suggest connections between the content source and existing knowledge."""
        
        try:
            # Get semantic neighbors
            neighbors = await self.semantic_analyzer.get_semantic_neighbors(db, content_source, max_suggestions)
            
            # Generate connection suggestions
            connections = []
            for neighbor in neighbors:
                connection = self._generate_connection_suggestion(content_source, neighbor)
                if connection:
                    connections.append(connection)
            
            # Sort by connection strength
            connections.sort(key=lambda x: x.get('strength', 0), reverse=True)
            
            # Limit to max suggestions
            connections = connections[:max_suggestions]
            
            logger.info(f"Generated {len(connections)} connection suggestions for content source {content_source.id}")
            return connections
            
        except Exception as e:
            logger.error(f"Failed to suggest connections for content source {content_source.id}: {e}")
            return []
    
    def _generate_connection_suggestion(self, source: ContentSource, neighbor: Dict) -> Dict[str, Any]:
        """Generate a connection suggestion between two content sources."""
        
        similarity_score = neighbor.get('similarity_score', 0.0)
        
        # Determine connection type based on similarity and content characteristics
        connection_type = self._determine_connection_type(source, neighbor, similarity_score)
        
        # Calculate connection strength
        strength = self._calculate_connection_strength(similarity_score, connection_type)
        
        # Generate connection rationale
        rationale = self._generate_connection_rationale(source, neighbor, connection_type, similarity_score)
        
        return {
            "target_content_id": neighbor.get('content_source_id'),
            "target_title": neighbor.get('title', 'Unknown'),
            "connection_type": connection_type,
            "strength": round(strength, 3),
            "similarity_score": round(similarity_score, 3),
            "rationale": rationale,
            "suggested_action": self._get_suggested_action(connection_type, strength)
        }
    
    def _determine_connection_type(self, source: ContentSource, neighbor: Dict, similarity: float) -> str:
        """Determine the type of connection between content sources."""
        
        # Base connection type on similarity score
        if similarity >= 0.8:
            return "direct_related"
        elif similarity >= 0.6:
            return "thematically_related"
        elif similarity >= 0.4:
            return "contextually_related"
        else:
            return "loosely_related"
    
    def _calculate_connection_strength(self, similarity: float, connection_type: str) -> float:
        """Calculate the strength of a connection suggestion."""
        
        base_strength = similarity
        
        # Adjust strength based on connection type
        type_multipliers = {
            "direct_related": 1.2,
            "thematically_related": 1.0,
            "contextually_related": 0.8,
            "loosely_related": 0.6
        }
        
        multiplier = type_multipliers.get(connection_type, 1.0)
        strength = base_strength * multiplier
        
        return min(1.0, strength)
    
    def _generate_connection_rationale(self, source: ContentSource, neighbor: Dict, 
                                     connection_type: str, similarity: float) -> str:
        """Generate a rationale for the connection suggestion."""
        
        source_title = source.title or "the source content"
        neighbor_title = neighbor.get('title', 'the target content')
        
        rationales = {
            "direct_related": f"High semantic similarity ({similarity:.2f}) suggests {source_title} is directly related to {neighbor_title}",
            "thematically_related": f"Strong thematic alignment ({similarity:.2f}) indicates {source_title} shares core themes with {neighbor_title}",
            "contextually_related": f"Moderate similarity ({similarity:.2f}) suggests {source_title} provides relevant context for {neighbor_title}",
            "loosely_related": f"Basic similarity ({similarity:.2f}) indicates potential loose connection between {source_title} and {neighbor_title}"
        }
        
        return rationales.get(connection_type, f"Content shows {similarity:.2f} similarity with existing knowledge")
    
    def _get_suggested_action(self, connection_type: str, strength: float) -> str:
        """Get suggested action for the connection."""
        
        if strength >= 0.8:
            return "create_bidirectional_link"
        elif strength >= 0.6:
            return "create_primary_link"
        elif strength >= 0.4:
            return "add_as_reference"
        else:
            return "note_possible_connection"
    
    async def suggest_hierarchical_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Suggest hierarchical connections (parent-child relationships)."""
        
        try:
            # This would typically use more sophisticated analysis
            # For now, use basic semantic similarity with content type analysis
            
            hierarchical_connections = []
            
            # Suggest parent connections (broader topics)
            parent_suggestions = await self._suggest_parent_connections(db, content_source)
            hierarchical_connections.extend(parent_suggestions)
            
            # Suggest child connections (more specific topics)
            child_suggestions = await self._suggest_child_connections(db, content_source)
            hierarchical_connections.extend(child_suggestions)
            
            return hierarchical_connections
            
        except Exception as e:
            logger.error(f"Failed to suggest hierarchical connections for content source {content_source.id}: {e}")
            return []
    
    async def _suggest_parent_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict]:
        """Suggest parent (broader) connections."""
        
        # This would typically analyze content to find broader categories
        # For now, return empty list as placeholder
        return []
    
    async def _suggest_child_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict]:
        """Suggest child (more specific) connections."""
        
        # This would typically analyze content to find more specific related topics
        # For now, return empty list as placeholder
        return []
    
    async def suggest_temporal_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Suggest temporal connections (chronological relationships)."""
        
        try:
            temporal_connections = []
            
            # Suggest predecessor connections (earlier related content)
            predecessor_suggestions = await self._suggest_predecessor_connections(db, content_source)
            temporal_connections.extend(predecessor_suggestions)
            
            # Suggest successor connections (later related content)
            successor_suggestions = await self._suggest_successor_connections(db, content_source)
            temporal_connections.extend(successor_suggestions)
            
            return temporal_connections
            
        except Exception as e:
            logger.error(f"Failed to suggest temporal connections for content source {content_source.id}: {e}")
            return []
    
    async def _suggest_predecessor_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict]:
        """Suggest predecessor (earlier) connections."""
        
        # This would typically analyze publication dates and content evolution
        # For now, return empty list as placeholder
        return []
    
    async def _suggest_successor_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict]:
        """Suggest successor (later) connections."""
        
        # This would typically analyze publication dates and content evolution
        # For now, return empty list as placeholder
        return []
    
    async def suggest_cross_domain_connections(self, db: AsyncSession, content_source: ContentSource) -> List[Dict[str, Any]]:
        """Suggest cross-domain connections (interdisciplinary relationships)."""
        
        try:
            cross_domain_connections = []
            
            # Analyze content for interdisciplinary potential
            domain_analysis = self._analyze_domain_potential(content_source)
            
            # Generate cross-domain suggestions
            for domain in domain_analysis.get('potential_domains', []):
                connection = {
                    "domain": domain,
                    "connection_type": "cross_domain",
                    "strength": domain_analysis.get('strength', 0.5),
                    "rationale": f"Content shows potential relevance to {domain} domain",
                    "suggested_action": "explore_interdisciplinary_links"
                }
                cross_domain_connections.append(connection)
            
            return cross_domain_connections
            
        except Exception as e:
            logger.error(f"Failed to suggest cross-domain connections for content source {content_source.id}: {e}")
            return []
    
    def _analyze_domain_potential(self, content_source: ContentSource) -> Dict[str, Any]:
        """Analyze potential cross-domain relevance."""
        
        # Simple keyword-based domain analysis
        domain_keywords = {
            "technology": ["algorithm", "software", "system", "digital", "comput"],
            "science": ["research", "study", "experiment", "data", "analysis"],
            "business": ["market", "strategy", "management", "economic", "finance"],
            "education": ["learning", "teaching", "curriculum", "pedagogy", "student"],
            "health": ["medical", "health", "treatment", "patient", "clinical"]
        }
        
        content_text = self._get_content_text(content_source)
        potential_domains = []
        
        for domain, keywords in domain_keywords.items():
            keyword_matches = sum(1 for keyword in keywords if keyword in content_text.lower())
            if keyword_matches > 0:
                strength = min(1.0, keyword_matches / len(keywords) * 2)  # Normalize strength
                potential_domains.append({
                    "domain": domain,
                    "strength": strength,
                    "keyword_matches": keyword_matches
                })
        
        # Sort by strength
        potential_domains.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            "potential_domains": [domain['domain'] for domain in potential_domains[:3]],  # Top 3 domains
            "strength": potential_domains[0]['strength'] if potential_domains else 0.0
        }
    
    def _get_content_text(self, content_source: ContentSource) -> str:
        """Extract text content for analysis."""
        
        text_parts = []
        
        if content_source.title:
            text_parts.append(content_source.title)
        
        if content_source.description:
            text_parts.append(content_source.description)
        
        if hasattr(content_source, 'content') and content_source.content:
            text_parts.append(content_source.content)
        
        return " ".join(text_parts).lower()
    
    async def get_connection_analysis_summary(self, db: AsyncSession, content_source: ContentSource) -> Dict[str, Any]:
        """Get comprehensive connection analysis summary."""
        
        try:
            # Get all types of connection suggestions
            semantic_connections = await self.suggest_connections(db, content_source)
            hierarchical_connections = await self.suggest_hierarchical_connections(db, content_source)
            temporal_connections = await self.suggest_temporal_connections(db, content_source)
            cross_domain_connections = await self.suggest_cross_domain_connections(db, content_source)
            
            # Calculate connection density
            total_connections = (len(semantic_connections) + len(hierarchical_connections) + 
                               len(temporal_connections) + len(cross_domain_connections))
            
            # Calculate average connection strength
            all_connections = semantic_connections + hierarchical_connections + temporal_connections + cross_domain_connections
            avg_strength = sum(conn.get('strength', 0) for conn in all_connections) / len(all_connections) if all_connections else 0
            
            return {
                "content_source_id": str(content_source.id),
                "semantic_connections": len(semantic_connections),
                "hierarchical_connections": len(hierarchical_connections),
                "temporal_connections": len(temporal_connections),
                "cross_domain_connections": len(cross_domain_connections),
                "total_connections": total_connections,
                "average_connection_strength": round(avg_strength, 3),
                "connection_density": self._calculate_connection_density(total_connections),
                "primary_connection_type": self._identify_primary_connection_type(
                    semantic_connections, hierarchical_connections, temporal_connections, cross_domain_connections
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to generate connection analysis summary for content source {content_source.id}: {e}")
            return {"error": str(e)}
    
    def _calculate_connection_density(self, total_connections: int) -> str:
        """Calculate connection density category."""
        
        if total_connections >= 10:
            return "high"
        elif total_connections >= 5:
            return "medium"
        elif total_connections >= 1:
            return "low"
        else:
            return "very_low"
    
    def _identify_primary_connection_type(self, semantic: List, hierarchical: List, 
                                        temporal: List, cross_domain: List) -> str:
        """Identify the primary type of connections suggested."""
        
        connection_counts = {
            "semantic": len(semantic),
            "hierarchical": len(hierarchical),
            "temporal": len(temporal),
            "cross_domain": len(cross_domain)
        }
        
        primary_type = max(connection_counts, key=connection_counts.get)
        return primary_type if connection_counts[primary_type] > 0 else "none"