"""Tests for LangGraph pipeline routing and node logic.

These tests verify the graph's conditional routing without
calling real LLMs — we test the decision logic, not the API.
"""

import pytest
from api.ai.graph import (
    route_after_extraction,
    route_after_validation,
    route_after_fraud_check,
    flag_fraud_node,
    needs_review_node,
)
from api.ai.state import create_initial_state, ProcessingStatus
from api.ai.nodes import validate_data_node


class TestExtractionRouting:
    """Verify routing decisions after the extraction node."""

    def test_routes_to_validate_on_success(self):
        """Successful extraction routes to validation."""
        state = {"processing_status": "extracting", "extracted_data": {"merchant_name": "Test"}}
        assert route_after_extraction(state) == "validate"

    def test_routes_to_error_on_failure(self):
        """Failed extraction routes to error handler."""
        state = {"processing_status": "failed", "extracted_data": None}
        assert route_after_extraction(state) == "error"

    def test_routes_to_error_on_missing_data(self):
        """Missing extracted_data routes to error even if status is OK."""
        state = {"processing_status": "extracting", "extracted_data": None}
        assert route_after_extraction(state) == "error"


class TestValidationRouting:
    """Verify routing decisions after the validation node."""

    def test_routes_to_fraud_check_on_few_errors(self):
        """3 or fewer validation errors proceed to fraud check."""
        state = {"validation_errors": ["err1", "err2"]}
        assert route_after_validation(state) == "fraud_check"

    def test_routes_to_needs_review_on_many_errors(self):
        """More than 3 errors route to manual review."""
        state = {"validation_errors": ["e1", "e2", "e3", "e4"]}
        assert route_after_validation(state) == "needs_review"

    def test_routes_to_fraud_check_on_no_errors(self):
        """No errors is the happy path to fraud check."""
        state = {"validation_errors": []}
        assert route_after_validation(state) == "fraud_check"


class TestFraudCheckRouting:
    """Verify routing decisions after the fraud check node."""

    def test_routes_to_finalize_on_low_score(self):
        """Score below 70 proceeds to finalize."""
        state = {"fraud_score": 30}
        assert route_after_fraud_check(state) == "finalize"

    def test_routes_to_flag_on_high_score(self):
        """Score >= 70 flags for fraud."""
        state = {"fraud_score": 75}
        assert route_after_fraud_check(state) == "flag_fraud"

    def test_boundary_score_70_is_flagged(self):
        """Exactly 70 is the threshold — should flag."""
        state = {"fraud_score": 70}
        assert route_after_fraud_check(state) == "flag_fraud"

    def test_score_69_is_not_flagged(self):
        """69 is just below the threshold — should finalize."""
        state = {"fraud_score": 69}
        assert route_after_fraud_check(state) == "finalize"


class TestValidationNode:
    """Test the validate_data_node logic directly."""

    def test_passes_valid_receipt(self):
        """Complete, well-formed receipt passes validation."""
        state = {
            "receipt_id": "test-123",
            "extracted_data": {
                "merchant_name": "Starbucks",
                "total_amount": 15.50,
                "transaction_date": "2026-01-15",
                "confidence_score": 0.9,
            },
        }
        result = validate_data_node(state)
        assert result["validation_passed"] is True
        assert result["validation_errors"] == []

    def test_catches_missing_merchant(self):
        """Missing merchant_name is a validation error."""
        state = {
            "receipt_id": "test-123",
            "extracted_data": {
                "merchant_name": None,
                "total_amount": 10.00,
                "transaction_date": "2026-01-15",
                "confidence_score": 0.9,
            },
        }
        result = validate_data_node(state)
        assert result["validation_passed"] is False
        assert any("merchant" in e.lower() for e in result["validation_errors"])

    def test_catches_negative_total(self):
        """Negative total_amount is a validation error."""
        state = {
            "receipt_id": "test-123",
            "extracted_data": {
                "merchant_name": "Test",
                "total_amount": -5.00,
                "transaction_date": "2026-01-15",
                "confidence_score": 0.9,
            },
        }
        result = validate_data_node(state)
        assert any("negative" in e.lower() for e in result["validation_errors"])

    def test_catches_future_date(self):
        """Transaction date in the future is flagged."""
        state = {
            "receipt_id": "test-123",
            "extracted_data": {
                "merchant_name": "Test",
                "total_amount": 10.00,
                "transaction_date": "2099-12-31",
                "confidence_score": 0.9,
            },
        }
        result = validate_data_node(state)
        assert any("future" in e.lower() for e in result["validation_errors"])

    def test_catches_low_confidence(self):
        """Confidence below 0.5 triggers a warning."""
        state = {
            "receipt_id": "test-123",
            "extracted_data": {
                "merchant_name": "Test",
                "total_amount": 10.00,
                "transaction_date": "2026-01-15",
                "confidence_score": 0.3,
            },
        }
        result = validate_data_node(state)
        assert any("confidence" in e.lower() for e in result["validation_errors"])

    def test_handles_none_extracted_data(self):
        """None extracted_data is caught gracefully."""
        state = {"receipt_id": "test-123", "extracted_data": None}
        result = validate_data_node(state)
        assert result["validation_passed"] is False


class TestTerminalNodes:
    """Test the flag_fraud and needs_review terminal nodes."""

    def test_flag_fraud_sets_status(self):
        result = flag_fraud_node({
            "fraud_score": 85,
            "fraud_analysis": {"risk_level": "HIGH", "flags": ["suspicious"]},
        })
        assert result["processing_status"] == "flagged_fraud"
        assert "FRAUD ALERT" in result["audit_notes"][0]

    def test_needs_review_sets_status(self):
        result = needs_review_node({
            "validation_errors": ["err1", "err2", "err3", "err4"],
        })
        assert result["processing_status"] == "needs_review"
        assert "MANUAL REVIEW" in result["audit_notes"][0]


class TestInitialState:
    """Test the create_initial_state factory."""

    def test_creates_correct_defaults(self):
        state = create_initial_state("r-1", "/tmp/img.jpg", "rep-1")
        assert state["receipt_id"] == "r-1"
        assert state["processing_status"] == "pending"
        assert state["fraud_score"] == 0
        assert state["validation_errors"] == []
        assert state["audit_notes"] == []
        assert state["processing_started_at"] is not None
