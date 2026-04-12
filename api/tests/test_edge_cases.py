"""Edge-case tests for API behavior, status transitions, and upload validation.

These cover the scenarios a real user would hit — double approvals,
empty reports, oversized uploads, boundary fraud scores — that unit
tests on individual layers tend to miss.
"""

import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from api.models import ExpenseReport, Receipt


@pytest.fixture
def api_client():
    return APIClient()


# --- Status Transition Edge Cases ---


@pytest.mark.django_db
class TestStatusTransitions:
    """Verify that status transitions behave correctly in edge cases."""

    def test_approve_already_approved_report(self, api_client, expense_report):
        """Approving an already-approved report is idempotent."""
        expense_report.status = "APPROVED"
        expense_report.save()

        response = api_client.post(f"/api/reports/{expense_report.id}/approve/")
        assert response.status_code == 200
        assert response.data["status"] == "APPROVED"

    def test_reject_flagged_report(self, api_client, expense_report):
        """A flagged report can still be rejected after review."""
        expense_report.status = "FLAGGED"
        expense_report.save()

        response = api_client.post(f"/api/reports/{expense_report.id}/reject/")
        assert response.status_code == 200
        assert response.data["status"] == "REJECTED"

    def test_flag_approved_report(self, api_client, expense_report):
        """Even approved reports can be flagged if fraud is found later."""
        expense_report.status = "APPROVED"
        expense_report.save()

        response = api_client.post(f"/api/reports/{expense_report.id}/flag/")
        assert response.status_code == 200
        assert response.data["status"] == "FLAGGED"

    def test_approve_nonexistent_report_returns_404(self, api_client):
        """Approving a bogus report ID returns 404, not 500."""
        bogus = uuid.uuid4()
        response = api_client.post(f"/api/reports/{bogus}/approve/")
        assert response.status_code == 404


# --- Upload Edge Cases ---


@pytest.mark.django_db
class TestUploadEdgeCases:
    """Test receipt upload with unusual or invalid input."""

    @patch("api.tasks.process_receipt_task.delay")
    def test_upload_valid_jpeg(self, mock_delay, api_client, expense_report, sample_image):
        """Valid JPEG upload creates receipt and triggers processing."""
        mock_delay.return_value = type("obj", (object,), {"id": "fake-task-id"})()

        response = api_client.post(
            "/api/receipts/",
            {"report": str(expense_report.id), "original_image": sample_image},
            format="multipart",
        )
        assert response.status_code == 201
        mock_delay.assert_called_once()

    def test_upload_without_report_fails(self, api_client, sample_image):
        """Receipt upload without a report ID is rejected."""
        response = api_client.post(
            "/api/receipts/",
            {"original_image": sample_image},
            format="multipart",
        )
        assert response.status_code == 400

    def test_upload_with_invalid_report_id(self, api_client, sample_image):
        """Receipt upload with a non-existent report ID is rejected."""
        bogus = uuid.uuid4()
        response = api_client.post(
            "/api/receipts/",
            {"report": str(bogus), "original_image": sample_image},
            format="multipart",
        )
        assert response.status_code == 400

    def test_upload_gif_is_rejected(self, api_client, expense_report):
        """GIF files are not in the allowed types list."""
        gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        gif = SimpleUploadedFile("receipt.gif", gif_bytes, content_type="image/gif")

        response = api_client.post(
            "/api/receipts/",
            {"report": str(expense_report.id), "original_image": gif},
            format="multipart",
        )
        assert response.status_code == 400


# --- Empty / Boundary State ---


@pytest.mark.django_db
class TestBoundaryStates:
    """Test API behavior at boundary conditions."""

    def test_report_with_no_receipts(self, api_client, expense_report):
        """A report with zero receipts returns an empty receipts array."""
        response = api_client.get(f"/api/reports/{expense_report.id}/")
        assert response.status_code == 200
        assert response.data["receipts"] == []
        assert response.data["total_amount"] == "0.00"

    def test_multiple_receipts_on_one_report(self, api_client, expense_report, sample_image):
        """Report correctly nests multiple receipts."""
        for name in ["Shop A", "Shop B", "Shop C"]:
            Receipt.objects.create(
                report=expense_report,
                original_image=sample_image,
                merchant_name=name,
                total_amount=10.00,
            )

        response = api_client.get(f"/api/reports/{expense_report.id}/")
        assert len(response.data["receipts"]) == 3

    def test_delete_receipt_does_not_delete_report(self, api_client, receipt, expense_report):
        """Deleting a receipt leaves the parent report intact."""
        api_client.delete(f"/api/receipts/{receipt.id}/")

        response = api_client.get(f"/api/reports/{expense_report.id}/")
        assert response.status_code == 200
        assert response.data["receipts"] == []

    def test_filter_by_nonexistent_status(self, api_client):
        """Filtering by a status with no matches returns empty list."""
        response = api_client.get("/api/reports/?status=APPROVED")
        assert response.status_code == 200
        assert response.data == []

    def test_list_receipts_empty_db(self, api_client, db):
        """Listing receipts on an empty database returns []."""
        response = api_client.get("/api/receipts/")
        assert response.status_code == 200
        assert response.data == []
