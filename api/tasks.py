"""Celery async tasks for background AI processing."""

from celery import shared_task
from celery.utils.log import get_task_logger
import traceback
from datetime import datetime

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    soft_time_limit=300,
    time_limit=360,
)
def process_receipt_task(self, receipt_id: str):
    """Process a receipt through the AI pipeline."""
    
    logger.info(f"Starting receipt processing: {receipt_id}")
    
    try:
        self.update_state(
            state='STARTED',
            meta={'receipt_id': receipt_id, 'step': 'loading', 'progress': 10}
        )
        
        # Load receipt from database
        from api.models import Receipt, ExpenseReport
        
        try:
            receipt = Receipt.objects.get(id=receipt_id)
        except Receipt.DoesNotExist:
            logger.error(f"Receipt not found: {receipt_id}")
            return {'status': 'failed', 'error': f'Receipt {receipt_id} not found'}
        
        logger.info(f"Loaded receipt: {receipt.id}, Image: {receipt.original_image.name}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'receipt_id': receipt_id, 'step': 'extracting', 'progress': 30}
        )
        
        # Run the LangGraph pipeline
        from api.ai.graph import process_receipt
        
        result = process_receipt(
            receipt_id=str(receipt.id),
            image_path=receipt.original_image.path,
            report_id=str(receipt.report_id)
        )
        
        logger.info(f"AI pipeline complete, Status: {result.get('processing_status')}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'receipt_id': receipt_id, 'step': 'saving', 'progress': 80}
        )
        
        # Save results to database
        extracted = result.get('extracted_data', {})
        
        if extracted:
            receipt.merchant_name = extracted.get('merchant_name')
            receipt.transaction_date = parse_date(extracted.get('transaction_date'))
            receipt.total_amount = extracted.get('total_amount')
            receipt.tax_amount = extracted.get('tax_amount')
            receipt.scanned_items = extracted.get('items', [])
        
        receipt.fraud_score = result.get('fraud_score', 0)
        receipt.audit_notes = '\n'.join(result.get('audit_notes', []))
        receipt.save()
        
        # Update expense report total
        if extracted and extracted.get('total_amount'):
            update_report_total(receipt.report_id)
        
        # Handle flagged receipts
        processing_status = result.get('processing_status', '')
        
        if processing_status in ['flagged_fraud', 'needs_review']:
            report = ExpenseReport.objects.get(id=receipt.report_id)
            report.status = 'FLAGGED'
            report.save()
            logger.warning(f"Receipt flagged: {processing_status}")
        
        return {
            'status': 'success',
            'receipt_id': receipt_id,
            'processing_status': processing_status,
            'fraud_score': result.get('fraud_score', 0),
            'merchant_name': extracted.get('merchant_name') if extracted else None,
            'total_amount': extracted.get('total_amount') if extracted else None,
        }
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            from api.models import Receipt
            receipt = Receipt.objects.get(id=receipt_id)
            receipt.audit_notes = f"Processing failed: {str(e)}"
            receipt.save()
        except:
            pass
        
        raise


def parse_date(date_string: str):
    """Parse date string to Python date object."""
    if not date_string:
        return None
    
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    return None


def update_report_total(report_id: str):
    """Recalculate the total amount for an expense report."""
    from api.models import ExpenseReport, Receipt
    from django.db.models import Sum
    
    try:
        total = Receipt.objects.filter(
            report_id=report_id,
            total_amount__isnull=False
        ).aggregate(Sum('total_amount'))['total_amount__sum']
        
        report = ExpenseReport.objects.get(id=report_id)
        report.total_amount = total or 0
        report.save()
        
        logger.info(f"Updated report total: ${total or 0:.2f}")
        
    except ExpenseReport.DoesNotExist:
        logger.error(f"Report not found: {report_id}")


@shared_task(bind=True)
def batch_process_receipts_task(self, receipt_ids: list):
    """Process multiple receipts in sequence."""
    logger.info(f"Batch processing {len(receipt_ids)} receipts")
    
    results = []
    
    for i, receipt_id in enumerate(receipt_ids):
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': len(receipt_ids), 'current_receipt': receipt_id}
        )
        
        try:
            result = process_receipt_task.apply(args=[receipt_id])
            results.append({'receipt_id': receipt_id, 'status': 'success', 'result': result.get()})
        except Exception as e:
            results.append({'receipt_id': receipt_id, 'status': 'failed', 'error': str(e)})
    
    return {
        'total_processed': len(receipt_ids),
        'successful': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'failed'),
        'results': results
    }


@shared_task
def rescan_recent_receipts_for_fraud():
    """Periodic task to re-scan recent receipts for fraud."""
    from api.models import Receipt
    from datetime import timedelta
    
    recent = Receipt.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=7),
        fraud_score__lt=50
    ).values_list('id', flat=True)
    
    logger.info(f"Re-scanning {len(recent)} recent receipts")
    
    for receipt_id in recent:
        process_receipt_task.delay(str(receipt_id))
    
    return {'queued': len(recent)}
