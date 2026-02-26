"""State definitions for the receipt processing LangGraph pipeline."""

from typing import TypedDict, List, Optional, Annotated
from operator import add
from langgraph.graph import MessagesState


class ProcessingStatus:
    """Constants for receipt processing status values."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
    FLAGGED_FRAUD = "flagged_fraud"


class ReceiptItem(TypedDict):
    """Represents a single item on a receipt."""
    name: str
    quantity: int
    unit_price: float
    total_price: float


class ExtractedReceiptData(TypedDict):
    """Structured data extracted by the LLM from receipt image."""
    merchant_name: Optional[str]
    merchant_address: Optional[str]
    transaction_date: Optional[str]
    transaction_time: Optional[str]
    items: List[ReceiptItem]
    subtotal: Optional[float]
    tax_amount: Optional[float]
    total_amount: Optional[float]
    payment_method: Optional[str]
    currency: str
    confidence_score: float


class FraudAnalysis(TypedDict):
    """Results from fraud detection analysis."""
    score: int
    risk_level: str
    flags: List[str]
    explanation: str
    requires_manual_review: bool


class ReceiptProcessingState(TypedDict):
    """Complete state for the receipt processing graph."""
    
    # Input fields
    receipt_id: str
    image_path: str
    report_id: str
    
    # Processing fields
    image_base64: Optional[str]
    ocr_text: Optional[str]
    extracted_data: Optional[ExtractedReceiptData]
    validation_passed: Optional[bool]
    validation_errors: Annotated[List[str], add]
    
    # Fraud detection
    fraud_analysis: Optional[FraudAnalysis]
    fraud_score: int
    
    # Output fields
    processing_status: str
    error_message: Optional[str]
    audit_notes: Annotated[List[str], add]
    
    # Metadata
    processing_started_at: Optional[str]
    processing_completed_at: Optional[str]
    total_processing_time_ms: Optional[int]


def create_initial_state(
    receipt_id: str,
    image_path: str,
    report_id: str
) -> ReceiptProcessingState:
    """Create the initial state for processing a receipt."""
    from datetime import datetime
    
    return ReceiptProcessingState(
        receipt_id=receipt_id,
        image_path=image_path,
        report_id=report_id,
        image_base64=None,
        ocr_text=None,
        extracted_data=None,
        validation_passed=None,
        validation_errors=[],
        fraud_analysis=None,
        fraud_score=0,
        processing_status="pending",
        error_message=None,
        audit_notes=[],
        processing_started_at=datetime.now().isoformat(),
        processing_completed_at=None,
        total_processing_time_ms=None,
    )
