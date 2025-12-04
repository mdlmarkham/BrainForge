"""Performance metrics collection and analysis for research workflows."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.research_run import ResearchRun, ResearchRunStatus
from ...services.audit.research_audit import research_audit_logger
from ...services.research_run_service import ResearchRunService

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    DURATION = "duration"
    THROUGHPUT = "throughput"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    QUALITY_SCORE = "quality_score"


@dataclass
class MetricDefinition:
    """Definition of a performance metric."""
    name: str
    type: MetricType
    description: str
    unit: str
    aggregation: str  # avg, sum, max, min, count


class ResearchMetricsCollector:
    """Collects and analyzes performance metrics for research workflows."""

    def __init__(self):
        self.research_service = ResearchRunService()
        self.metric_definitions = self._initialize_metric_definitions()

    def _initialize_metric_definitions(self) -> dict[str, MetricDefinition]:
        """Initialize standard metric definitions."""

        return {
            "research_duration": MetricDefinition(
                name="research_duration",
                type=MetricType.DURATION,
                description="Total duration of research run",
                unit="seconds",
                aggregation="avg"
            ),
            "content_discovery_duration": MetricDefinition(
                name="content_discovery_duration",
                type=MetricType.DURATION,
                description="Duration of content discovery phase",
                unit="seconds",
                aggregation="avg"
            ),
            "quality_assessment_duration": MetricDefinition(
                name="quality_assessment_duration",
                type=MetricType.DURATION,
                description="Duration of quality assessment phase",
                unit="seconds",
                aggregation="avg"
            ),
            "integration_proposal_duration": MetricDefinition(
                name="integration_proposal_duration",
                type=MetricType.DURATION,
                description="Duration of integration proposal phase",
                unit="seconds",
                aggregation="avg"
            ),
            "content_sources_discovered": MetricDefinition(
                name="content_sources_discovered",
                type=MetricType.THROUGHPUT,
                description="Number of content sources discovered",
                unit="sources",
                aggregation="avg"
            ),
            "quality_assessments_completed": MetricDefinition(
                name="quality_assessments_completed",
                type=MetricType.THROUGHPUT,
                description="Number of quality assessments completed",
                unit="assessments",
                aggregation="avg"
            ),
            "integration_proposals_generated": MetricDefinition(
                name="integration_proposals_generated",
                type=MetricType.THROUGHPUT,
                description="Number of integration proposals generated",
                unit="proposals",
                aggregation="avg"
            ),
            "research_success_rate": MetricDefinition(
                name="research_success_rate",
                type=MetricType.SUCCESS_RATE,
                description="Percentage of successful research runs",
                unit="percent",
                aggregation="avg"
            ),
            "content_discovery_success_rate": MetricDefinition(
                name="content_discovery_success_rate",
                type=MetricType.SUCCESS_RATE,
                description="Success rate of content discovery",
                unit="percent",
                aggregation="avg"
            ),
            "average_quality_score": MetricDefinition(
                name="average_quality_score",
                type=MetricType.QUALITY_SCORE,
                description="Average quality score of discovered content",
                unit="score",
                aggregation="avg"
            ),
            "error_rate": MetricDefinition(
                name="error_rate",
                type=MetricType.ERROR_RATE,
                description="Error rate across research workflow",
                unit="percent",
                aggregation="avg"
            )
        }

    async def collect_research_run_metrics(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Collect comprehensive metrics for a specific research run."""

        research_run = await self.research_service.get(db, research_run_id)
        if not research_run:
            return {"error": "Research run not found"}

        # Get audit timeline for timing data
        timeline = await research_audit_logger.get_research_timeline(db, research_run_id)

        # Calculate phase durations
        durations = self._calculate_phase_durations(timeline)

        # Get content statistics
        content_stats = await self._get_content_statistics(db, research_run_id)

        # Get quality statistics
        quality_stats = await self._get_quality_statistics(db, research_run_id)

        # Get error statistics
        error_stats = await self._get_error_statistics(db, research_run_id)

        metrics = {
            "research_run_id": str(research_run_id),
            "timestamp": datetime.now().isoformat(),
            "durations": durations,
            "content_statistics": content_stats,
            "quality_statistics": quality_stats,
            "error_statistics": error_stats,
            "overall_success": research_run.status == ResearchRunStatus.COMPLETED
        }

        return metrics

    def _calculate_phase_durations(self, timeline: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate durations for each research phase from audit timeline."""

        phase_start_times = {}
        phase_durations = {}

        for event in timeline:
            event_type = event["event_type"]
            timestamp = datetime.fromisoformat(event["timestamp"])

            # Track phase start times
            if event_type == AuditEventType.RESEARCH_START.value:
                phase_start_times["total"] = timestamp
            elif event_type == AuditEventType.CONTENT_DISCOVERY.value:
                if "content_discovery" not in phase_start_times:
                    phase_start_times["content_discovery"] = timestamp
            elif event_type == AuditEventType.QUALITY_ASSESSMENT.value:
                if "quality_assessment" not in phase_start_times:
                    phase_start_times["quality_assessment"] = timestamp
            elif event_type == AuditEventType.INTEGRATION_PROPOSAL.value:
                if "integration_proposal" not in phase_start_times:
                    phase_start_times["integration_proposal"] = timestamp

            # Calculate durations when phases end
            if event_type == AuditEventType.CONTENT_DISCOVERY.value:
                if "content_discovery" in phase_start_times:
                    phase_durations["content_discovery"] = (
                        timestamp - phase_start_times["content_discovery"]
                    ).total_seconds()
            elif event_type == AuditEventType.QUALITY_ASSESSMENT.value:
                if "quality_assessment" in phase_start_times:
                    phase_durations["quality_assessment"] = (
                        timestamp - phase_start_times["quality_assessment"]
                    ).total_seconds()
            elif event_type == AuditEventType.INTEGRATION_PROPOSAL.value:
                if "integration_proposal" in phase_start_times:
                    phase_durations["integration_proposal"] = (
                        timestamp - phase_start_times["integration_proposal"]
                    ).total_seconds()
            elif event_type == AuditEventType.RESEARCH_COMPLETE.value:
                if "total" in phase_start_times:
                    phase_durations["total"] = (
                        timestamp - phase_start_times["total"]
                    ).total_seconds()

        return phase_durations

    async def _get_content_statistics(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get content-related statistics."""

        content_sources = await self.research_service.get_content_sources_for_run(db, research_run_id)

        sources_by_type = {}
        for source in content_sources:
            source_type = source.source_type or "unknown"
            sources_by_type[source_type] = sources_by_type.get(source_type, 0) + 1

        return {
            "total_sources": len(content_sources),
            "sources_by_type": sources_by_type,
            "average_source_quality": await self._calculate_average_quality(db, content_sources)
        }

    async def _get_quality_statistics(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get quality assessment statistics."""

        from ...services.quality_assessment_service import QualityAssessmentService

        quality_service = QualityAssessmentService()
        content_sources = await self.research_service.get_content_sources_for_run(db, research_run_id)

        assessments = []
        for source in content_sources:
            assessment = await quality_service.get_assessment_by_content_source(db, source.id)
            if assessment:
                assessments.append(assessment)

        if not assessments:
            return {
                "assessments_count": 0,
                "average_score": 0,
                "score_distribution": {}
            }

        scores = [assessment.overall_score for assessment in assessments if assessment.overall_score]
        score_distribution = self._calculate_score_distribution(scores)

        return {
            "assessments_count": len(assessments),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_distribution": score_distribution,
            "high_quality_count": len([s for s in scores if s >= 0.8]),
            "medium_quality_count": len([s for s in scores if 0.5 <= s < 0.8]),
            "low_quality_count": len([s for s in scores if s < 0.5])
        }

    async def _get_error_statistics(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get error statistics from audit trail."""

        audit_stats = await research_audit_logger.audit_service.get_audit_statistics(db, research_run_id)

        error_count = audit_stats["level_counts"].get("error", 0)
        warning_count = audit_stats["level_counts"].get("warning", 0)
        total_events = audit_stats["total_events"]

        return {
            "error_count": error_count,
            "warning_count": warning_count,
            "total_events": total_events,
            "error_rate": (error_count / total_events * 100) if total_events > 0 else 0,
            "warning_rate": (warning_count / total_events * 100) if total_events > 0 else 0
        }

    async def _calculate_average_quality(self, db: AsyncSession, content_sources: list) -> float:
        """Calculate average quality score for content sources."""

        from ...services.quality_assessment_service import QualityAssessmentService

        quality_service = QualityAssessmentService()
        scores = []

        for source in content_sources:
            assessment = await quality_service.get_assessment_by_content_source(db, source.id)
            if assessment and assessment.overall_score:
                scores.append(assessment.overall_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_score_distribution(self, scores: list[float]) -> dict[str, int]:
        """Calculate distribution of quality scores."""

        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }

        for score in scores:
            if score < 0.2:
                distribution["0.0-0.2"] += 1
            elif score < 0.4:
                distribution["0.2-0.4"] += 1
            elif score < 0.6:
                distribution["0.4-0.6"] += 1
            elif score < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1

        return distribution

    async def collect_aggregate_metrics(self, db: AsyncSession,
                                      time_range: timedelta | None = None) -> dict[str, Any]:
        """Collect aggregate metrics across all research runs."""

        # Get research runs within time range
        research_runs = await self._get_research_runs_in_range(db, time_range)

        if not research_runs:
            return {"error": "No research runs found in specified time range"}

        aggregate_metrics = {
            "time_range_start": (datetime.now() - time_range).isoformat() if time_range else "all_time",
            "time_range_end": datetime.now().isoformat(),
            "total_research_runs": len(research_runs),
            "completed_runs": 0,
            "failed_runs": 0,
            "average_durations": {},
            "throughput_metrics": {},
            "success_rates": {},
            "quality_metrics": {},
            "error_metrics": {}
        }

        # Collect metrics for each research run
        all_metrics = []
        for research_run in research_runs:
            metrics = await self.collect_research_run_metrics(db, research_run.id)
            if "error" not in metrics:
                all_metrics.append(metrics)

                # Count status
                if research_run.status == ResearchRunStatus.COMPLETED:
                    aggregate_metrics["completed_runs"] += 1
                elif research_run.status == ResearchRunStatus.FAILED:
                    aggregate_metrics["failed_runs"] += 1

        if not all_metrics:
            return aggregate_metrics

        # Calculate aggregate values
        aggregate_metrics.update(self._calculate_aggregate_values(all_metrics))

        return aggregate_metrics

    async def _get_research_runs_in_range(self, db: AsyncSession,
                                        time_range: timedelta | None) -> list[ResearchRun]:
        """Get research runs within a specified time range."""

        if time_range:
            start_time = datetime.now() - time_range
            return await self.research_service.get_research_runs_since(db, start_time)
        else:
            return await self.research_service.get_all(db)

    def _calculate_aggregate_values(self, metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate aggregate values from multiple metrics collections."""

        # Initialize accumulators
        durations = {
            "total": [], "content_discovery": [],
            "quality_assessment": [], "integration_proposal": []
        }
        throughput = {
            "content_sources": [], "quality_assessments": [], "integration_proposals": []
        }
        success_rates = []
        quality_scores = []
        error_rates = []

        for metrics in metrics_list:
            # Duration metrics
            for phase, duration in metrics.get("durations", {}).items():
                if phase in durations:
                    durations[phase].append(duration)

            # Throughput metrics
            content_stats = metrics.get("content_statistics", {})
            throughput["content_sources"].append(content_stats.get("total_sources", 0))

            quality_stats = metrics.get("quality_statistics", {})
            throughput["quality_assessments"].append(quality_stats.get("assessments_count", 0))
            throughput["integration_proposals"].append(quality_stats.get("assessments_count", 0))  # Approximation

            # Success rates
            success_rates.append(1.0 if metrics.get("overall_success", False) else 0.0)

            # Quality scores
            quality_scores.append(quality_stats.get("average_score", 0))

            # Error rates
            error_stats = metrics.get("error_statistics", {})
            error_rates.append(error_stats.get("error_rate", 0))

        # Calculate averages
        def safe_average(values):
            return sum(values) / len(values) if values else 0

        return {
            "average_durations": {
                phase: safe_average(values) for phase, values in durations.items()
            },
            "throughput_metrics": {
                "average_content_sources": safe_average(throughput["content_sources"]),
                "average_quality_assessments": safe_average(throughput["quality_assessments"]),
                "average_integration_proposals": safe_average(throughput["integration_proposals"])
            },
            "success_rates": {
                "overall_success_rate": safe_average(success_rates) * 100
            },
            "quality_metrics": {
                "average_quality_score": safe_average(quality_scores)
            },
            "error_metrics": {
                "average_error_rate": safe_average(error_rates)
            }
        }

    async def get_performance_trends(self, db: AsyncSession,
                                   period: timedelta = timedelta(days=7)) -> dict[str, Any]:
        """Get performance trends over time."""

        # Group by time periods (e.g., daily)
        period_start = datetime.now() - period
        research_runs = await self.research_service.get_research_runs_since(db, period_start)

        # Group runs by day
        runs_by_day = {}
        for run in research_runs:
            day_key = run.created_at.date().isoformat()
            if day_key not in runs_by_day:
                runs_by_day[day_key] = []
            runs_by_day[day_key].append(run)

        # Calculate daily metrics
        daily_metrics = {}
        for day, runs in runs_by_day.items():
            day_metrics = []
            for run in runs:
                metrics = await self.collect_research_run_metrics(db, run.id)
                if "error" not in metrics:
                    day_metrics.append(metrics)

            if day_metrics:
                daily_metrics[day] = self._calculate_aggregate_values(day_metrics)

        return {
            "period": period.days,
            "trend_start": period_start.isoformat(),
            "trend_end": datetime.now().isoformat(),
            "daily_metrics": daily_metrics,
            "trend_analysis": self._analyze_trends(daily_metrics)
        }

    def _analyze_trends(self, daily_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance trends from daily metrics."""

        if not daily_metrics:
            return {"error": "Insufficient data for trend analysis"}

        days = sorted(daily_metrics.keys())
        recent_days = days[-7:]  # Last 7 days for recent trend

        # Calculate basic trend indicators
        success_rates = [daily_metrics[day]["success_rates"]["overall_success_rate"] for day in days]
        avg_durations = [daily_metrics[day]["average_durations"]["total"] for day in days]

        # Simple linear trend calculation (slope)
        def calculate_slope(values):
            n = len(values)
            if n < 2:
                return 0
            x = list(range(n))
            y = values
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            return numerator / denominator if denominator != 0 else 0

        success_trend = calculate_slope(success_rates)
        duration_trend = calculate_slope(avg_durations)

        return {
            "success_rate_trend": "improving" if success_trend > 0 else "declining" if success_trend < 0 else "stable",
            "duration_trend": "improving" if duration_trend < 0 else "declining" if duration_trend > 0 else "stable",
            "success_trend_slope": success_trend,
            "duration_trend_slope": duration_trend,
            "days_analyzed": len(days),
            "recent_performance": self._analyze_recent_performance(daily_metrics, recent_days)
        }

    def _analyze_recent_performance(self, daily_metrics: dict[str, dict[str, Any]],
                                  recent_days: list[str]) -> dict[str, Any]:
        """Analyze recent performance trends."""

        if not recent_days:
            return {"error": "No recent data"}

        recent_metrics = [daily_metrics[day] for day in recent_days]

        # Calculate averages for recent period
        success_rates = [m["success_rates"]["overall_success_rate"] for m in recent_metrics]
        avg_duration = sum(m["average_durations"]["total"] for m in recent_metrics) / len(recent_metrics)
        avg_quality = sum(m["quality_metrics"]["average_quality_score"] for m in recent_metrics) / len(recent_metrics)

        return {
            "average_success_rate": sum(success_rates) / len(success_rates),
            "average_duration": avg_duration,
            "average_quality_score": avg_quality,
            "period_days": len(recent_days)
        }


# Global metrics collector instance
research_metrics_collector = ResearchMetricsCollector()
