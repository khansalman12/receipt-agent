"""Tests for Celery tasks with mocked LLM calls.

These tests verify the full task lifecycle — from receiving a
receipt ID to saving AI-extracted data back to the database —
without hitting any external API.
"""

import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import ExpenseReport, Receipt
from api.tasks import process_receipt_task, update_report_total, batch_process_receipts_task


FAKE_PIPELINE_RESULT = {
    "processing_status": "completed",
    "extracted_data": {
        "merchant_name": "Corner Bakery",
        "transaction_date": "2026-03-10",
        "total_amount": 18.75,
        "tax_amount": 1.50,
        "items": [
            {"name": "Croissant", "quantity": 2, "unit_price": 4.50, "total_price": 9.00},
            {"name": "Coffee", "quantity": 1, "unit_price": 3.25, "total_price": 3.25},
        ],
    },
    "fraud_score": 15,
    "audit_notes": ["Extraction complete", "Validation passed", "PROCESSING COMPLETE"],
}

FLAGGED_PIPELINE_RESULT = {
    "processing_status": "flagged_fraud",
    "extracted_data": {
        "merchant_name": "Suspicious LLC",
        "transaction_date": "2026-03-10",
        "total_amount": 9999.00,
        "tax_amount": 0.00,
        "items": [],
    },
    "fraud_score": 85,
    "audit_notes": ["FRAUD ALERT: Score 85/100"],
}


@pytest.fixture
def report_with_receipt(db, sample_image):
    """Create a report + receipt ready for processing."""
    report = ExpenseReport.objects.create(status="PENDING")
    receipt = Receipt.objects.create(
        report=report,
        original_image=sample_image,
    )
    return report, receipt


@pytest.mark.django_db
class TestProcessReceiptTask:
    """Test the main receipt processing Celery task."""

    @patch("api.tasks.process_receipt_task.update_state")
    @patch("api.ai.graph.process_receipt")
    def test_successful_processing_saves_extracted_data(
        self, mock_pipeline, mock_update_state, report_with_receipt
    ):
        """Task saves merchant, amount, items, and fraud score to the receipt."""
        report, receipt = report_with_receipt
        mock_pipeline.return_value = FAKE_PIPELINE_RESULT

        result = process_receipt_task.apply(args=[str(receipt.id)]).get()

        receipt.refresh_from_db()
        assert receipt.merchant_name == "Corner Bakery"
        assert receipt.total_amount == Decimal("18.75")
        assert receipt.tax_amount == Decimal("1.50")
        assert receipt.fraud_score == 15
        assert len(receipt.scanned_items) == 2
        assert result["status"] == "success"

    @patch("api.tasks.process_receipt_task.update_state")
    @patch("api.ai.graph.process_receipt")
    def test_high_fraud_score_flags_report(
        self, mock_pipeline, mock_update_state, report_with_receipt
    ):
        """Receipt with fraud_score >= 70 flips report status to FLAGGED."""
        report, receipt = report_with_receipt
        mock_pipeline.return_value = FLAGGED_PIPELINE_RESULT

        process_receipt_task.apply(args=[str(receipt.id)]).get()

        report.refresh_from_db()
        assert report.status == "FLAGGED"

    @patch("api.tasks.process_receipt_task.update_state")
    @patch("api.ai.graph.process_receipt")
    def test_low_fraud_score_keeps_report_pending(
        self, mock_pipeline, mock_update_state, report_with_receipt
    ):
        """Low fraud score does not change report status."""
        report, receipt = report_with_receipt
        mock_pipeline.return_value = FAKE_PIPELINE_RESULT

        process_receipt_task.apply(args=[str(receipt.id)]).get()

        report.refresh_from_db()
        assert report.status == "PENDING"

    @patch("api.tasks.process_receipt_task.update_state")
    def test_missing_receipt_returns_failed(self, mock_update_state, db):
        """Task returns failure dict when receipt ID doesn't exist."""
        bogus_id = str(uuid.uuid4())
        result = process_receipt_task.apply(args=[bogus_id]).get()
        assert result["status"] == "failed"

    @patch("api.tasks.process_receipt_task.update_state")
    @patch("api.ai.graph.process_receipt")
    def test_updates_report_total(
        self, mock_pipeline, mock_update_state, report_with_receipt
    ):
        """After processing, report.total_amount reflects receipt totals."""
        report, receipt = report_with_receipt
        mock_pipeline.return_value = FAKE_PIPELINE_RESULT

        process_receipt_task.apply(args=[str(receipt.id)]).get()

        report.refresh_from_db()
        assert report.total_amount == Decimal("18.75")


@pytest.mark.django_db
class TestUpdateReportTotal:
    """Test the report total recalculation helper."""

    def test_sums_receipt_amounts(self, expense_report, sample_image):
        """Total is the sum of all receipt amounts on the report."""
        Receipt.objects.create(
            report=expense_report, original_image=sample_image, total_amount=10.00
        )
        Receipt.objects.create(
            report=expense_report, original_image=sample_image, total_amount=25.50
        )

        update_report_total(str(expense_report.id))

        expense_report.refresh_from_db()
        assert expense_report.total_amount == Decimal("35.50")

    def test_handles_no_receipts(self, expense_report):
        """Report with no receipts gets total_amount = 0."""
        update_report_total(str(expense_report.id))

        expense_report.refresh_from_db()
        assert expense_report.total_amount == Decimal("0")

    def test_ignores_null_amounts(self, expense_report, sample_image):
        """Receipts without a total_amount are excluded from the sum."""
        Receipt.objects.create(
            report=expense_report, original_image=sample_image, total_amount=10.00
        )
        Receipt.objects.create(
            report=expense_report, original_image=sample_image, total_amount=None
        )

        update_report_total(str(expense_report.id))

        expense_report.refresh_from_db()
        assert expense_report.total_amount == Decimal("10.00")
