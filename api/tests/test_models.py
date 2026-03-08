"""Tests for ExpenseReport and Receipt models.

Covers field defaults, relationships, UUID primary keys,
string representations, and ordering behavior.
"""

import uuid
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from api.models import ExpenseReport, Receipt


@pytest.mark.django_db
class TestExpenseReport:
    """Verify ExpenseReport field defaults and behavior."""

    def test_create_report_with_defaults(self):
        """New reports start with PENDING status and zero total."""
        report = ExpenseReport.objects.create()
        assert report.status == "PENDING"
        assert report.total_amount == Decimal("0.00")
        assert report.user is None

    def test_uuid_primary_key(self):
        """Primary key must be a valid UUID, not a sequential integer."""
        report = ExpenseReport.objects.create()
        assert isinstance(report.id, uuid.UUID)

    def test_str_representation(self):
        report = ExpenseReport.objects.create()
        assert "PENDING" in str(report)
        assert str(report.id) in str(report)

    def test_ordering_by_created_at(self):
        """Reports are returned newest-first by default."""
        r1 = ExpenseReport.objects.create()
        r2 = ExpenseReport.objects.create()
        reports = list(ExpenseReport.objects.all())
        assert reports[0].id == r2.id

    def test_status_choices(self):
        """All four status values are valid."""
        for status_code, _ in ExpenseReport.STATUS_CHOICES:
            report = ExpenseReport.objects.create(status=status_code)
            assert report.status == status_code


@pytest.mark.django_db
class TestReceipt:
    """Verify Receipt field defaults and relationships."""

    def test_receipt_belongs_to_report(self, receipt, expense_report):
        """Receipt must be linked to an ExpenseReport."""
        assert receipt.report_id == expense_report.id

    def test_receipt_uuid_primary_key(self, receipt):
        assert isinstance(receipt.id, uuid.UUID)

    def test_default_fraud_score_is_zero(self, expense_report, sample_image):
        """New receipts default to fraud_score=0 before AI runs."""
        r = Receipt.objects.create(
            report=expense_report,
            original_image=sample_image,
        )
        assert r.fraud_score == 0

    def test_scanned_items_stored_as_json(self, receipt):
        """scanned_items is a list of dicts persisted via JSONField."""
        assert isinstance(receipt.scanned_items, list)
        assert receipt.scanned_items[0]["name"] == "Latte"

    def test_str_representation(self, receipt):
        assert "Test Coffee Shop" in str(receipt)

    def test_cascade_delete(self, expense_report, receipt):
        """Deleting a report cascades to its receipts."""
        receipt_id = receipt.id
        expense_report.delete()
        assert not Receipt.objects.filter(id=receipt_id).exists()
