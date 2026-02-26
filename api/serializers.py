"""Serializers for expense management API."""

from rest_framework import serializers
from .models import ExpenseReport, Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    """Full serializer for Receipt model - used for reading data."""
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'report',
            'original_image',
            'processed_image',
            'merchant_name',
            'transaction_date',
            'total_amount',
            'tax_amount',
            'scanned_items',
            'fraud_score',
            'audit_notes',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'processed_image',
            'merchant_name',
            'transaction_date',
            'total_amount',
            'tax_amount',
            'scanned_items',
            'fraud_score',
            'audit_notes',
            'created_at',
        ]


class ExpenseReportSerializer(serializers.ModelSerializer):
    """Serializer for ExpenseReport with nested receipts."""
    
    receipts = ReceiptSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExpenseReport
        fields = [
            'id',
            'user',
            'status',
            'total_amount',
            'created_at',
            'receipts',
        ]
        read_only_fields = [
            'id',
            'status',
            'total_amount',
            'created_at',
        ]


class ReceiptUploadSerializer(serializers.ModelSerializer):
    """Minimal serializer for uploading new receipts."""
    
    class Meta:
        model = Receipt
        fields = ['id', 'report', 'original_image']
        read_only_fields = ['id']
    
    def validate_original_image(self, value):
        """Validate uploaded image file."""
        max_size = 10 * 1024 * 1024  # 10MB
        
        if value.size > max_size:
            raise serializers.ValidationError(
                "Image file too large. Maximum size is 10MB."
            )
        
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        
        if hasattr(value, 'content_type'):
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Invalid file type: {value.content_type}. "
                    f"Allowed types: {', '.join(allowed_types)}"
                )
        
        return value
