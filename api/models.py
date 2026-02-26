import uuid
from django.db import models
from django.contrib.auth.models import User

class ExpenseReport(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Audit'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged for Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Expense Report'
        verbose_name_plural = 'Expense Reports'

    def __str__(self):
        return f"Report {self.id} - {self.status}"

class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ExpenseReport, related_name='receipts', on_delete=models.CASCADE)
    
    # Image storage
    original_image = models.ImageField(upload_to='receipts/original/')
    processed_image = models.ImageField(upload_to='receipts/processed/', null=True, blank=True)
    
    # Extracted Data
    merchant_name = models.CharField(max_length=255, null=True, blank=True)
    transaction_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Raw JSON from AI
    scanned_items = models.JSONField(default=dict, blank=True)
    
    # Audit Results
    fraud_score = models.IntegerField(default=0)
    audit_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt {self.id} - {self.merchant_name or 'Unknown'}"
