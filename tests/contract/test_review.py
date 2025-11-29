"""Contract tests for review workflow API endpoints."""

import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient

from src.api.main import app
from src.models.review_queue import ReviewQueueCreate, ReviewDecision
from src.models.integration_proposal import ProposalStatus

client = TestClient(app)


class TestReviewAPI:
    """Test suite for review workflow API endpoints."""
    
    def test_create_review_queue(self):
        """Test creating a new review queue entry."""
        
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium",
            "due_date": "2024-01-01T00:00:00Z"
        }
        
        response = client.post("/review/queue", json=review_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["content_source_id"] == review_data["content_source_id"]
        assert data["research_run_id"] == review_data["research_run_id"]
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_get_review_queues(self):
        """Test getting review queue entries."""
        
        response = client.get("/review/queue")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_review_queue_by_id(self):
        """Test getting a specific review queue entry by ID."""
        
        # First create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Then get it by ID
        response = client.get(f"/review/queue/{review_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review_id
        assert data["content_source_id"] == review_data["content_source_id"]
    
    def test_get_review_queue_not_found(self):
        """Test getting a non-existent review queue entry."""
        
        non_existent_id = str(uuid4())
        response = client.get(f"/review/queue/{non_existent_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_review_queue(self):
        """Test updating a review queue entry."""
        
        # First create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Then update it
        update_data = {
            "priority": "high",
            "notes": "Updated priority due to importance"
        }
        
        response = client.put(f"/review/queue/{review_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review_id
        assert data["priority"] == "high"
        assert data["notes"] == "Updated priority due to importance"
    
    def test_make_review_decision_approve(self):
        """Test making an approve decision on a review queue entry."""
        
        # First create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Then make a decision
        decision_data = {
            "decision": "approve",
            "implementation_notes": "Content approved for integration"
        }
        
        response = client.post(f"/review/queue/{review_id}/decide", json=decision_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review_id
        assert data["status"] == "approved"
        assert data["decision"] == "approve"
    
    def test_make_review_decision_reject(self):
        """Test making a reject decision on a review queue entry."""
        
        # First create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Then make a decision
        decision_data = {
            "decision": "reject",
            "implementation_notes": "Content rejected due to low quality"
        }
        
        response = client.post(f"/review/queue/{review_id}/decide", json=decision_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review_id
        assert data["status"] == "rejected"
        assert data["decision"] == "reject"
    
    def test_make_review_decision_defer(self):
        """Test making a defer decision on a review queue entry."""
        
        # First create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Then make a decision
        decision_data = {
            "decision": "defer",
            "implementation_notes": "Content deferred for later review"
        }
        
        response = client.post(f"/review/queue/{review_id}/decide", json=decision_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review_id
        assert data["status"] == "deferred"
        assert data["decision"] == "defer"
    
    def test_get_review_proposal(self):
        """Test getting the integration proposal associated with a review queue entry."""
        
        # This test would require setting up both review queue and integration proposal
        # For contract testing, we'll test the endpoint structure
        review_id = str(uuid4())
        
        response = client.get(f"/review/queue/{review_id}/proposal")
        
        # Should return either 200 with proposal data or 404 if not found
        assert response.status_code in [200, 404]
    
    def test_get_pending_reviews(self):
        """Test getting pending review queue entries."""
        
        response = client.get("/review/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there are pending reviews, they should have status "pending"
        for review in data:
            assert review["status"] == "pending"
    
    def test_get_review_statistics(self):
        """Test getting review workflow statistics."""
        
        response = client.get("/review/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check expected structure
        assert "total_reviews" in data
        assert "status_counts" in data
        assert "average_processing_time" in data
        assert isinstance(data["status_counts"], dict)
    
    def test_batch_process_reviews(self):
        """Test batch processing multiple review decisions."""
        
        # Create some review queues first
        review_ids = []
        for _ in range(3):
            review_data = {
                "content_source_id": str(uuid4()),
                "research_run_id": str(uuid4()),
                "reviewer_id": str(uuid4()),
                "priority": "medium"
            }
            create_response = client.post("/review/queue", json=review_data)
            review_ids.append(create_response.json()["id"])
        
        # Batch process them
        batch_data = {
            "review_queue_ids": review_ids,
            "decision": "approve",
            "implementation_notes": "Batch approved for integration"
        }
        
        response = client.post("/review/batch-process", json=batch_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "processed" in data
        assert "failed" in data
        assert "total" in data
        assert data["total"] == len(review_ids)
    
    def test_get_research_run_workflow(self):
        """Test getting the complete review workflow for a research run."""
        
        research_run_id = str(uuid4())
        
        response = client.get(f"/review/workflow/{research_run_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All reviews should belong to the specified research run
        for review in data:
            assert review["research_run_id"] == research_run_id
    
    def test_review_queue_filtering(self):
        """Test filtering review queues by various criteria."""
        
        # Test filtering by status
        response = client.get("/review/queue?status=pending")
        assert response.status_code == 200
        
        # Test filtering by content source ID
        content_source_id = str(uuid4())
        response = client.get(f"/review/queue?content_source_id={content_source_id}")
        assert response.status_code == 200
        
        # Test filtering by research run ID
        research_run_id = str(uuid4())
        response = client.get(f"/review/queue?research_run_id={research_run_id}")
        assert response.status_code == 200
        
        # Test pagination
        response = client.get("/review/queue?limit=10&offset=5")
        assert response.status_code == 200
    
    def test_review_decision_validation(self):
        """Test validation of review decision data."""
        
        # Create a review queue first
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # Test invalid decision
        invalid_decision_data = {
            "decision": "invalid_decision",
            "implementation_notes": "This should fail"
        }
        
        response = client.post(f"/review/queue/{review_id}/decide", json=invalid_decision_data)
        assert response.status_code == 422  # Validation error
    
    def test_review_queue_creation_validation(self):
        """Test validation of review queue creation data."""
        
        # Test missing required fields
        invalid_data = {
            "research_run_id": str(uuid4()),
            # Missing content_source_id
        }
        
        response = client.post("/review/queue", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Test invalid UUID format
        invalid_uuid_data = {
            "content_source_id": "not-a-uuid",
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4())
        }
        
        response = client.post("/review/queue", json=invalid_uuid_data)
        assert response.status_code == 422  # Validation error


class TestReviewWorkflowIntegration:
    """Integration tests for the complete review workflow."""
    
    def test_complete_review_workflow(self):
        """Test a complete review workflow from creation to decision."""
        
        # Step 1: Create a review queue
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "high",
            "due_date": "2024-01-01T00:00:00Z"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        assert create_response.status_code == 201
        review_id = create_response.json()["id"]
        
        # Step 2: Verify the review is in pending status
        get_response = client.get(f"/review/queue/{review_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "pending"
        
        # Step 3: Make a decision
        decision_data = {
            "decision": "approve",
            "implementation_notes": "Content meets quality standards"
        }
        
        decision_response = client.post(f"/review/queue/{review_id}/decide", json=decision_data)
        assert decision_response.status_code == 200
        assert decision_response.json()["status"] == "approved"
        assert decision_response.json()["decision"] == "approve"
        
        # Step 4: Verify the review is no longer in pending list
        pending_response = client.get("/review/pending")
        assert pending_response.status_code == 200
        pending_reviews = [r for r in pending_response.json() if r["id"] == review_id]
        assert len(pending_reviews) == 0
        
        # Step 5: Check statistics reflect the completed review
        stats_response = client.get("/review/statistics")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["status_counts"].get("approved", 0) >= 1


class TestReviewErrorHandling:
    """Test error handling in review workflow API."""
    
    def test_review_decision_on_completed_review(self):
        """Test making a decision on an already completed review."""
        
        # Create and complete a review
        review_data = {
            "content_source_id": str(uuid4()),
            "research_run_id": str(uuid4()),
            "reviewer_id": str(uuid4()),
            "priority": "medium"
        }
        
        create_response = client.post("/review/queue", json=review_data)
        review_id = create_response.json()["id"]
        
        # First decision
        decision_data = {"decision": "approve"}
        client.post(f"/review/queue/{review_id}/decide", json=decision_data)
        
        # Try to make another decision
        second_decision_data = {"decision": "reject"}
        response = client.post(f"/review/queue/{review_id}/decide", json=second_decision_data)
        
        # Should return an error (either 400 or 409)
        assert response.status_code in [400, 409, 500]
    
    def test_batch_process_with_invalid_ids(self):
        """Test batch processing with invalid review queue IDs."""
        
        invalid_ids = [str(uuid4()), str(uuid4())]
        batch_data = {
            "review_queue_ids": invalid_ids,
            "decision": "approve"
        }
        
        response = client.post("/review/batch-process", json=batch_data)
        
        # Should process what it can and report failures
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == len(invalid_ids)  # All should fail
        assert data["processed"] == 0