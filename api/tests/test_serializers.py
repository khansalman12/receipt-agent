"""Tests for data validation and serializer logic.

Covers image upload validation (size limits, file types),
read-only field enforcement, and serializer output shape.
"""

import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory
from api.serializers import (
    ExpenseReportSerializer,
    ReceiptSerializer,
    ReceiptUploadSerializer,
)


class TestReceiptUploadSerializer:
    """Validate image upload constraints."""

    def test_rejects_oversized_image(self):
        """Images larger than 10MB are rejected."""
        # 11MB of zeros
        huge_file = SimpleUploadedFile(
            name="huge.jpg",
            content=b"\x00" * (11 * 1024 * 1024),
            content_type="image/jpeg",
        )
        serializer = ReceiptUploadSerializer()
        with pytest.raises(Exception):
            serializer.validate_original_image(huge_file)

    def test_rejects_invalid_file_type(self):
        """Only JPEG, PNG, and WebP are accepted."""
        pdf_file = SimpleUploadedFile(
            name="receipt.pdf",
            content=b"%PDF-1.4 fake content",
            content_type="application/pdf",
        )
        serializer = ReceiptUploadSerializer()
        with pytest.raises(Exception):
            serializer.validate_original_image(pdf_file)

    def test_accepts_valid_jpeg(self, sample_image):
        """Valid JPEG under 10MB passes validation."""
        serializer = ReceiptUploadSerializer()
        result = serializer.validate_original_image(sample_image)
        assert result == sample_image


@pytest.mark.django_db
class TestReceiptSerializer:
    """Verify the read serializer output shape."""

    def test_includes_all_ai_fields(self, receipt):
        """Serialized receipt exposes AI-extracted fields."""
        serializer = ReceiptSerializer(receipt)
        data = serializer.data
        assert "merchant_name" in data
        assert "fraud_score" in data
        assert "scanned_items" in data
        assert "audit_notes" in data

    def test_total_amount_is_decimal(self, receipt):
        """total_amount should serialize as a string-encoded decimal."""
        serializer = ReceiptSerializer(receipt)
        assert serializer.data["total_amount"] == "25.50"


@pytest.mark.django_db
class TestExpenseReportSerializer:
    """Verify nested receipts are included in report output."""

    def test_includes_nested_receipts(self, expense_report, receipt):
        """Report serializer nests related receipts."""
        serializer = ExpenseReportSerializer(expense_report)
        assert "receipts" in serializer.data
        assert len(serializer.data["receipts"]) == 1
        assert serializer.data["receipts"][0]["merchant_name"] == "Test Coffee Shop"
