"""Views for expense management API."""

import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import ExpenseReport, Receipt
from .serializers import (
    ExpenseReportSerializer,
    ReceiptSerializer,
    ReceiptUploadSerializer,
)


class ExpenseReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expense reports."""
    
    queryset = ExpenseReport.objects.all().order_by('-created_at')
    serializer_class = ExpenseReportSerializer
    
    def get_queryset(self):
        """Filter reports by status if provided."""
        queryset = ExpenseReport.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an expense report."""
        report = self.get_object()
        report.status = 'APPROVED'
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an expense report."""
        report = self.get_object()
        report.status = 'REJECTED'
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='flag')
    def flag_for_review(self, request, pk=None):
        """Flag a report for manual review."""
        report = self.get_object()
        report.status = 'FLAGGED'
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending reports."""
        pending_reports = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(pending_reports, many=True)
        return Response(serializer.data)


class ReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet for managing receipts with file upload support."""
    
    queryset = Receipt.objects.all().order_by('-created_at')
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return ReceiptUploadSerializer
        return ReceiptSerializer
    
    def get_queryset(self):
        """Filter receipts by report ID if provided."""
        queryset = Receipt.objects.all().order_by('-created_at')
        report_id = self.request.query_params.get('report', None)
        
        if report_id:
            queryset = queryset.filter(report_id=report_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create receipt and trigger AI processing."""
        receipt = serializer.save()
        
        # Trigger async AI processing
        from .tasks import process_receipt_task
        task_result = process_receipt_task.delay(str(receipt.id))
        
        logger = logging.getLogger(__name__)
        logger.info(f"Receipt created: {receipt.id}, AI task: {task_result.id}")
        
        return receipt
