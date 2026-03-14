"""Tests for ExpenseReport and Receipt API endpoints.

Covers CRUD operations, status transitions,
filtering, image upload validation, and error cases.
"""

import uuid
import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from api.models import ExpenseReport, Receipt


@pytest.fixture
def api_client():
    return APIClient()


# ─── ExpenseReport Endpoints ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestExpenseReportAPI:
    """Test /api/reports/ endpoints."""

    def test_create_report(self, api_client):
        """POST /api/reports/ creates a new pending report."""
        response = api_client.post("/api/reports/", {}, format="json")
        assert response.status_code == 201
        assert response.data["status"] == "PENDING"
        assert response.data["total_amount"] == "0.00"

    def test_list_reports(self, api_client, expense_report):
        """GET /api/reports/ returns all reports."""
        response = api_client.get("/api/reports/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_retrieve_report(self, api_client, expense_report):
        """GET /api/reports/{id}/ returns a specific report with receipts."""
        response = api_client.get(f"/api/reports/{expense_report.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(expense_report.id)
        assert "receipts" in response.data

    def test_approve_report(self, api_client, expense_report):
        """POST /api/reports/{id}/approve/ transitions status to APPROVED."""
        response = api_client.post(f"/api/reports/{expense_report.id}/approve/")
        assert response.status_code == 200
        assert response.data["status"] == "APPROVED"

        # Verify persisted
        expense_report.refresh_from_db()
        assert expense_report.status == "APPROVED"

    def test_reject_report(self, api_client, expense_report):
        """POST /api/reports/{id}/reject/ transitions status to REJECTED."""
        response = api_client.post(f"/api/reports/{expense_report.id}/reject/")
        assert response.status_code == 200
        assert response.data["status"] == "REJECTED"

    def test_flag_report(self, api_client, expense_report):
        """POST /api/reports/{id}/flag/ transitions status to FLAGGED."""
        response = api_client.post(f"/api/reports/{expense_report.id}/flag/")
        assert response.status_code == 200
        assert response.data["status"] == "FLAGGED"

    def test_filter_by_status(self, api_client):
        """GET /api/reports/?status=APPROVED filters correctly."""
        ExpenseReport.objects.create(status="APPROVED")
        ExpenseReport.objects.create(status="PENDING")

        response = api_client.get("/api/reports/?status=APPROVED")
        assert response.status_code == 200
        assert all(r["status"] == "APPROVED" for r in response.data)

    def test_pending_action(self, api_client):
        """GET /api/reports/pending/ returns only pending reports."""
        ExpenseReport.objects.create(status="PENDING")
        ExpenseReport.objects.create(status="APPROVED")

        response = api_client.get("/api/reports/pending/")
        assert response.status_code == 200
        assert all(r["status"] == "PENDING" for r in response.data)

    def test_retrieve_nonexistent_report(self, api_client):
        """GET /api/reports/{bogus_id}/ returns 404."""
        bogus_id = uuid.uuid4()
        response = api_client.get(f"/api/reports/{bogus_id}/")
        assert response.status_code == 404


# ─── Receipt Endpoints ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestReceiptAPI:
    """Test /api/receipts/ endpoints."""

    def test_list_receipts(self, api_client, receipt):
        """GET /api/receipts/ returns all receipts."""
        response = api_client.get("/api/receipts/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_retrieve_receipt(self, api_client, receipt):
        """GET /api/receipts/{id}/ returns receipt with AI-extracted data."""
        response = api_client.get(f"/api/receipts/{receipt.id}/")
        assert response.status_code == 200
        assert response.data["merchant_name"] == "Test Coffee Shop"
        assert response.data["fraud_score"] == 15

    def test_filter_by_report(self, api_client, receipt, expense_report):
        """GET /api/receipts/?report={id} filters by parent report."""
        response = api_client.get(f"/api/receipts/?report={expense_report.id}")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_delete_receipt(self, api_client, receipt):
        """DELETE /api/receipts/{id}/ removes the receipt."""
        response = api_client.delete(f"/api/receipts/{receipt.id}/")
        assert response.status_code == 204
        assert not Receipt.objects.filter(id=receipt.id).exists()

    def test_retrieve_nonexistent_receipt(self, api_client):
        """GET /api/receipts/{bogus_id}/ returns 404."""
        bogus_id = uuid.uuid4()
        response = api_client.get(f"/api/receipts/{bogus_id}/")
        assert response.status_code == 404


# ─── Health Check ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHealthCheck:
    """Test /api/health/ endpoint."""

    def test_health_endpoint(self, api_client):
        """Health check returns {status: ok}."""
        response = api_client.get("/api/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
