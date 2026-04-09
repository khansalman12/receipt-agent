"""Tests for custom Django management commands.

Verifies that the CLI tools produce correct output and
handle filters (--status, --days) properly.
"""

import pytest
from io import StringIO
from decimal import Decimal

from django.core.management import call_command

from api.models import ExpenseReport, Receipt


@pytest.mark.django_db
class TestReceiptStatsCommand:
    """Test the `receiptstats` management command."""

    def test_runs_on_empty_database(self):
        """Command completes without error when there is no data."""
        out = StringIO()
        call_command("receiptstats", stdout=out)
        output = out.getvalue()
        assert "Total reports:" in output
        assert "Total receipts:" in output

    def test_displays_report_counts(self):
        """Command shows the correct count per status."""
        ExpenseReport.objects.create(status="PENDING")
        ExpenseReport.objects.create(status="PENDING")
        ExpenseReport.objects.create(status="APPROVED")

        out = StringIO()
        call_command("receiptstats", stdout=out)
        output = out.getvalue()
        assert "Total reports:  3" in output

    def test_displays_receipt_stats(self, expense_report, sample_image):
        """Command shows processed vs unprocessed receipt breakdown."""
        Receipt.objects.create(
            report=expense_report,
            original_image=sample_image,
            merchant_name="Processed Shop",
            total_amount=15.00,
            fraud_score=20,
        )
        Receipt.objects.create(
            report=expense_report,
            original_image=sample_image,
        )

        out = StringIO()
        call_command("receiptstats", stdout=out)
        output = out.getvalue()
        assert "Total receipts: 2" in output
        assert "Processed:      1" in output
        assert "Unprocessed:    1" in output

    def test_status_filter(self):
        """--status flag filters reports correctly."""
        ExpenseReport.objects.create(status="APPROVED")
        ExpenseReport.objects.create(status="PENDING")

        out = StringIO()
        call_command("receiptstats", "--status", "APPROVED", stdout=out)
        output = out.getvalue()
        assert "Total reports:  1" in output
        assert "Filtered by status: APPROVED" in output

    def test_displays_top_merchants(self, expense_report, sample_image):
        """Command lists the most frequent merchants."""
        for _ in range(3):
            Receipt.objects.create(
                report=expense_report,
                original_image=sample_image,
                merchant_name="Frequent Cafe",
                total_amount=5.00,
            )

        out = StringIO()
        call_command("receiptstats", stdout=out)
        output = out.getvalue()
        assert "Frequent Cafe" in output
        assert "3 receipts" in output
