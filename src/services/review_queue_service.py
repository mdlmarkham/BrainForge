"""Review queue service for managing human review workflow of content sources."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.research_review_queue import ResearchReviewQueue, ResearchReviewQueueCreate, ReviewStatus
from ..models.content_source import ContentSource
from ..models.quality_assessment import QualityAssessment
from ..services.sqlalchemy_service import SQLAlchemyService

logger = logging.getLogger(__name__)


class ReviewQueueService(SQLAlchemyService[ResearchReviewQueue]):
    """Service for managing the review queue workflow."""
    
    def __init__(self):
        super().__init__(ResearchReviewQueue)
    
    async def add_to_review_queue(self, db: AsyncSession, content_source_id: UUID, 
                                research_run_id: UUID, assigned_to: str = None) -> ResearchReviewQueue:
        """Add a content source to the review queue."""
        
        try:
            # Check if content source already exists in review queue
            existing_review = await self.get_review_by_content_source(db, content_source_id)
            if existing_review:
                logger.info(f"Content source {content_source_id} already in review queue")
                return existing_review
            
            # Create review queue entry
            review_data = ResearchReviewQueueCreate(
                content_source_id=content_source_id,
                research_run_id=research_run_id,
                assigned_to=assigned_to,
                status=ReviewStatus.PENDING,
                priority=self._calculate_priority(content_source_id)  # Would need quality assessment
            )
            
            review_queue = await self.create(db, review_data)
            
            logger.info(f"Added content source {content_source_id} to review queue")
            return review_queue
            
        except Exception as e:
            logger.error(f"Failed to add content source {content_source_id} to review queue: {e}")
            raise
    
    async def get_review_by_content_source(self, db: AsyncSession, content_source_id: UUID) -> Optional[ResearchReviewQueue]:
        """Get review queue entry by content source ID."""
        
        from sqlalchemy import select
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        result = await db.execute(
            select(ResearchReviewQueueORM).where(ResearchReviewQueueORM.content_source_id == content_source_id)
        )
        review_orm = result.scalar_one_or_none()
        
        if review_orm:
            return ResearchReviewQueue.model_validate(review_orm)
        return None
    
    def _calculate_priority(self, content_source_id: UUID) -> int:
        """Calculate review priority based on content quality and other factors."""
        
        # This would typically use quality assessment scores
        # For now, use a default priority
        return 5  # Medium priority
    
    async def assign_review(self, db: AsyncSession, review_id: UUID, assigned_to: str) -> ResearchReviewQueue:
        """Assign a review to a specific reviewer."""
        
        try:
            review = await self.get(db, review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")
            
            # Update review assignment
            update_data = {
                "assigned_to": assigned_to,
                "status": ReviewStatus.ASSIGNED
            }
            
            updated_review = await self.update(db, review_id, update_data)
            
            logger.info(f"Assigned review {review_id} to {assigned_to}")
            return updated_review
            
        except Exception as e:
            logger.error(f"Failed to assign review {review_id}: {e}")
            raise
    
    async def update_review_status(self, db: AsyncSession, review_id: UUID, 
                                 status: ReviewStatus, notes: str = None) -> ResearchReviewQueue:
        """Update the status of a review."""
        
        try:
            review = await self.get(db, review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")
            
            update_data = {"status": status}
            if notes:
                update_data["review_notes"] = notes
            
            updated_review = await self.update(db, review_id, update_data)
            
            logger.info(f"Updated review {review_id} status to {status}")
            return updated_review
            
        except Exception as e:
            logger.error(f"Failed to update review {review_id} status: {e}")
            raise
    
    async def get_pending_reviews(self, db: AsyncSession, limit: int = 10) -> List[ResearchReviewQueue]:
        """Get pending reviews that need assignment."""
        
        from sqlalchemy import select
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        result = await db.execute(
            select(ResearchReviewQueueORM)
            .where(ResearchReviewQueueORM.status == ReviewStatus.PENDING)
            .order_by(ResearchReviewQueueORM.priority.desc(), ResearchReviewQueueORM.created_at)
            .limit(limit)
        )
        reviews_orm = result.scalars().all()
        
        return [ResearchReviewQueue.model_validate(review) for review in reviews_orm]
    
    async def get_assigned_reviews(self, db: AsyncSession, assigned_to: str = None) -> List[ResearchReviewQueue]:
        """Get reviews assigned to a specific reviewer or all assigned reviews."""
        
        from sqlalchemy import select
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        query = select(ResearchReviewQueueORM).where(ResearchReviewQueueORM.status == ReviewStatus.ASSIGNED)
        
        if assigned_to:
            query = query.where(ResearchReviewQueueORM.assigned_to == assigned_to)
        
        query = query.order_by(ResearchReviewQueueORM.priority.desc(), ResearchReviewQueueORM.created_at)
        
        result = await db.execute(query)
        reviews_orm = result.scalars().all()
        
        return [ResearchReviewQueue.model_validate(review) for review in reviews_orm]
    
    async def get_completed_reviews(self, db: AsyncSession, research_run_id: UUID = None) -> List[ResearchReviewQueue]:
        """Get completed reviews, optionally filtered by research run."""
        
        from sqlalchemy import select
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        query = select(ResearchReviewQueueORM).where(
            ResearchReviewQueueORM.status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED])
        )
        
        if research_run_id:
            query = query.where(ResearchReviewQueueORM.research_run_id == research_run_id)
        
        query = query.order_by(ResearchReviewQueueORM.updated_at.desc())
        
        result = await db.execute(query)
        reviews_orm = result.scalars().all()
        
        return [ResearchReviewQueue.model_validate(review) for review in reviews_orm]
    
    async def get_review_queue_count_for_research_run(self, db: AsyncSession, research_run_id: UUID) -> int:
        """Get count of review queue entries for a research run."""
        
        from sqlalchemy import select, func
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        query = select(func.count(ResearchReviewQueueORM.id)).where(
            ResearchReviewQueueORM.research_run_id == research_run_id
        )
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def get_approved_sources_for_research_run(self, db: AsyncSession, research_run_id: UUID) -> List[ContentSource]:
        """Get content sources that were approved through review for a research run."""
        
        from sqlalchemy import select, join
        from ..models.orm.content_source import ContentSource as ContentSourceORM
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        query = (
            select(ContentSourceORM)
            .select_from(
                join(ContentSourceORM, ResearchReviewQueueORM, 
                     ContentSourceORM.id == ResearchReviewQueueORM.content_source_id)
            )
            .where(
                ResearchReviewQueueORM.research_run_id == research_run_id,
                ResearchReviewQueueORM.status == ReviewStatus.APPROVED
            )
        )
        
        result = await db.execute(query)
        sources_orm = result.scalars().all()
        
        return [ContentSource.model_validate(source) for source in sources_orm]
    
    async def get_review_statistics(self, db: AsyncSession, research_run_id: UUID = None) -> Dict[str, Any]:
        """Get review statistics for a research run or overall."""
        
        from sqlalchemy import select, func
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        base_query = select(ResearchReviewQueueORM)
        if research_run_id:
            base_query = base_query.where(ResearchReviewQueueORM.research_run_id == research_run_id)
        
        # Get counts by status
        status_counts_query = (
            select(
                ResearchReviewQueueORM.status,
                func.count(ResearchReviewQueueORM.id).label("count")
            )
            .select_from(base_query)
            .group_by(ResearchReviewQueueORM.status)
        )
        
        result = await db.execute(status_counts_query)
        status_counts = result.mappings().all()
        
        # Get total count
        total_query = select(func.count(ResearchReviewQueueORM.id)).select_from(base_query)
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0
        
        # Get average review time (for completed reviews)
        avg_time_query = (
            select(
                func.avg(
                    func.extract('epoch', ResearchReviewQueueORM.updated_at - ResearchReviewQueueORM.created_at)
                ).label("avg_seconds")
            )
            .where(ResearchReviewQueueORM.status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED]))
        )
        
        if research_run_id:
            avg_time_query = avg_time_query.where(ResearchReviewQueueORM.research_run_id == research_run_id)
        
        avg_time_result = await db.execute(avg_time_query)
        avg_seconds = avg_time_result.scalar() or 0
        
        return {
            "total_reviews": total_count,
            "status_counts": {row["status"]: row["count"] for row in status_counts},
            "average_review_time_seconds": round(avg_seconds, 2),
            "average_review_time_minutes": round(avg_seconds / 60, 2) if avg_seconds > 0 else 0,
            "research_run_id": str(research_run_id) if research_run_id else None
        }
    
    async def batch_assign_reviews(self, db: AsyncSession, review_ids: List[UUID], 
                                 assigned_to: str) -> List[ResearchReviewQueue]:
        """Assign multiple reviews to a reviewer in batch."""
        
        assigned_reviews = []
        
        for review_id in review_ids:
            try:
                review = await self.assign_review(db, review_id, assigned_to)
                assigned_reviews.append(review)
            except Exception as e:
                logger.error(f"Failed to assign review {review_id}: {e}")
                # Continue with next review
        
        logger.info(f"Assigned {len(assigned_reviews)} reviews to {assigned_to}")
        return assigned_reviews
    
    async def get_reviewer_performance(self, db: AsyncSession, reviewer: str) -> Dict[str, Any]:
        """Get performance statistics for a specific reviewer."""
        
        from sqlalchemy import select, func
        from ..models.orm.research_review_queue import ResearchReviewQueue as ResearchReviewQueueORM
        
        # Get counts by status for this reviewer
        status_counts_query = (
            select(
                ResearchReviewQueueORM.status,
                func.count(ResearchReviewQueueORM.id).label("count")
            )
            .where(ResearchReviewQueueORM.assigned_to == reviewer)
            .group_by(ResearchReviewQueueORM.status)
        )
        
        result = await db.execute(status_counts_query)
        status_counts = result.mappings().all()
        
        # Get average review time
        avg_time_query = (
            select(
                func.avg(
                    func.extract('epoch', ResearchReviewQueueORM.updated_at - ResearchReviewQueueORM.created_at)
                ).label("avg_seconds")
            )
            .where(
                ResearchReviewQueueORM.assigned_to == reviewer,
                ResearchReviewQueueORM.status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED])
            )
        )
        
        avg_time_result = await db.execute(avg_time_query)
        avg_seconds = avg_time_result.scalar() or 0
        
        return {
            "reviewer": reviewer,
            "status_counts": {row["status"]: row["count"] for row in status_counts},
            "total_reviews_assigned": sum(row["count"] for row in status_counts),
            "average_review_time_seconds": round(avg_seconds, 2),
            "average_review_time_minutes": round(avg_seconds / 60, 2) if avg_seconds > 0 else 0
        }