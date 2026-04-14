"""Node functions for the LangGraph receipt processing pipeline."""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import os

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from .state import ReceiptProcessingState, ExtractedReceiptData, FraudAnalysis

load_dotenv()


def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.1):
    """Create a Groq LLM instance."""
    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Node 1: Load Image
def load_image_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Load and encode the receipt image."""
    print(f"Loading image for receipt: {state['receipt_id']}")
    
    try:
        image_path = state["image_path"]
        
        if not Path(image_path).exists():
            return {
                "processing_status": "failed",
                "error_message": f"Image file not found: {image_path}",
                "audit_notes": ["ERROR: Image file not found"]
            }
        
        image_base64 = encode_image_to_base64(image_path)
        file_size_kb = Path(image_path).stat().st_size / 1024
        
        return {
            "image_base64": image_base64,
            "processing_status": "extracting",
            "audit_notes": [f"Image loaded successfully ({file_size_kb:.1f} KB)"]
        }
        
    except Exception as e:
        return {
            "processing_status": "failed",
            "error_message": str(e),
            "audit_notes": [f"ERROR loading image: {str(e)}"]
        }


EXTRACTION_PROMPT = """You are an expert receipt parser. Analyze this receipt and extract structured data.

Extract: merchant name/address, transaction date/time, items (name, quantity, prices), subtotal, tax, total, payment method, currency.

Return JSON only:
{
    "merchant_name": "string or null",
    "merchant_address": "string or null",
    "transaction_date": "YYYY-MM-DD or null",
    "transaction_time": "HH:MM or null",
    "items": [{"name": "string", "quantity": 1, "unit_price": 0.00, "total_price": 0.00}],
    "subtotal": 0.00,
    "tax_amount": 0.00,
    "total_amount": 0.00,
    "payment_method": "string or null",
    "currency": "USD",
    "confidence_score": 0.85
}"""


# Node 2: Extract Data
def extract_data_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Use LLM vision to extract structured data from receipt image."""
    print(f"Extracting data from receipt: {state['receipt_id']}")

    if not state.get("image_base64"):
        return {
            "processing_status": "failed",
            "error_message": "No image data available for extraction",
            "audit_notes": ["ERROR: Missing image data"]
        }

    try:
        llm = get_llm(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.0)

        messages = [
            SystemMessage(content="You are an expert receipt parser. Return only valid JSON, no markdown, no extra text."),
            HumanMessage(content=[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{state['image_base64']}"
                    }
                },
                {
                    "type": "text",
                    "text": EXTRACTION_PROMPT
                }
            ])
        ]

        response = llm.invoke(messages)

        # Clean response and parse JSON
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        extracted_data: ExtractedReceiptData = json.loads(content)

        return {
            "extracted_data": extracted_data,
            "processing_status": "validating",
            "audit_notes": [
                f"Extraction complete: {extracted_data.get('merchant_name', 'Unknown')}",
                f"Total: {extracted_data.get('currency', 'USD')} {extracted_data.get('total_amount', 0)}",
                f"Confidence: {extracted_data.get('confidence_score', 0):.0%}",
            ]
        }

    except json.JSONDecodeError as e:
        return {
            "processing_status": "failed",
            "error_message": f"Could not parse AI response as JSON: {str(e)}",
            "audit_notes": [f"ERROR: JSON parse failed — {str(e)}"]
        }
    except Exception as e:
        return {
            "processing_status": "failed",
            "error_message": str(e),
            "audit_notes": [f"ERROR during extraction: {str(e)}"]
        }


# Node 3: Validate Data
def validate_data_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Validate the extracted data for consistency."""
    print(f"Validating data for: {state['receipt_id']}")
    
    extracted = state.get("extracted_data")
    
    if not extracted:
        return {
            "validation_passed": False,
            "validation_errors": ["No extracted data to validate"],
            "processing_status": "needs_review"
        }
    
    errors = []
    
    # Required fields
    if not extracted.get("merchant_name"):
        errors.append("Missing merchant name")
    if not extracted.get("total_amount"):
        errors.append("Missing total amount")
    if not extracted.get("transaction_date"):
        errors.append("Missing transaction date")
    
    # Positive numbers
    if extracted.get("total_amount") and extracted["total_amount"] < 0:
        errors.append("Total amount cannot be negative")
    
    # Items should add up to subtotal
    if extracted.get("items") and extracted.get("subtotal"):
        calculated = sum(item.get("total_price", 0) for item in extracted["items"])
        if abs(calculated - extracted["subtotal"]) > 0.01:
            errors.append(f"Items total ({calculated:.2f}) doesn't match subtotal ({extracted['subtotal']:.2f})")
    
    # Date validation
    if extracted.get("transaction_date"):
        try:
            tx_date = datetime.strptime(extracted["transaction_date"], "%Y-%m-%d")
            if tx_date > datetime.now():
                errors.append("Transaction date is in the future")
        except ValueError:
            errors.append("Invalid date format")
    
    # Confidence check
    if extracted.get("confidence_score", 0) < 0.5:
        errors.append("Low extraction confidence")
    
    return {
        "validation_passed": len(errors) == 0,
        "validation_errors": errors,
        "processing_status": "analyzing",
        "audit_notes": [f"Validation: {len(errors)} issues found" if errors else "Validation passed"]
    }


FRAUD_PROMPT = """Analyze this receipt for fraud indicators:

{receipt_data}

Check for: round numbers, weekend transactions, unusual merchants, missing info, unrealistic prices.

Return JSON:
{{
    "score": 0-100,
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
    "flags": ["concerns"],
    "explanation": "reasoning",
    "requires_manual_review": true/false
}}"""


# Node 4: Fraud Check
def fraud_check_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Analyze receipt for fraud patterns."""
    print(f"Running fraud detection for: {state['receipt_id']}")
    
    extracted = state.get("extracted_data")
    
    if not extracted:
        return {
            "fraud_score": 100,
            "fraud_analysis": {
                "score": 100,
                "risk_level": "CRITICAL",
                "flags": ["No extracted data"],
                "explanation": "Cannot analyze without data",
                "requires_manual_review": True
            },
            "processing_status": "needs_review",
            "audit_notes": ["FRAUD CHECK: No data to analyze"]
        }
    
    try:
        llm = get_llm(model="llama-3.3-70b-versatile", temperature=0.0)
        
        prompt = FRAUD_PROMPT.format(
            receipt_data=json.dumps(extracted, indent=2, default=str)
        )
        
        messages = [
            SystemMessage(content="You are a fraud detection AI specialist."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        
        try:
            fraud_analysis: FraudAnalysis = json.loads(response.content)
        except json.JSONDecodeError:
            fraud_analysis = {
                "score": 50,
                "risk_level": "MEDIUM",
                "flags": ["Could not parse AI response"],
                "explanation": "Fraud analysis inconclusive",
                "requires_manual_review": True
            }
        
        return {
            "fraud_analysis": fraud_analysis,
            "fraud_score": fraud_analysis["score"],
            "processing_status": "needs_review" if fraud_analysis["score"] >= 70 else "completed",
            "audit_notes": [
                f"Fraud score: {fraud_analysis['score']}/100",
                f"Risk level: {fraud_analysis['risk_level']}"
            ]
        }
        
    except Exception as e:
        return {
            "fraud_score": 50,
            "fraud_analysis": {
                "score": 50,
                "risk_level": "MEDIUM",
                "flags": [f"Analysis error: {str(e)}"],
                "explanation": "Fraud analysis failed",
                "requires_manual_review": True
            },
            "processing_status": "needs_review",
            "audit_notes": [f"FRAUD CHECK ERROR: {str(e)}"]
        }


# Node 5: Finalize
def finalize_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Wrap up processing and record completion."""
    print(f"Finalizing receipt: {state['receipt_id']}")
    
    started = state.get("processing_started_at")
    elapsed_ms = None
    
    if started:
        try:
            start_time = datetime.fromisoformat(started)
            elapsed = datetime.now() - start_time
            elapsed_ms = int(elapsed.total_seconds() * 1000)
        except (ValueError, TypeError):
            pass
    
    extracted = state.get("extracted_data", {})
    
    return {
        "processing_completed_at": datetime.now().isoformat(),
        "total_processing_time_ms": elapsed_ms,
        "audit_notes": [
            "PROCESSING COMPLETE",
            f"Merchant: {extracted.get('merchant_name', 'Unknown')}",
            f"Total: {extracted.get('currency', 'USD')} {extracted.get('total_amount', 0):.2f}",
        ]
    }


# Node 6: Error Handler
def error_handler_node(state: ReceiptProcessingState) -> Dict[str, Any]:
    """Handle processing errors."""
    print(f"Error handling for receipt: {state['receipt_id']}")
    
    error = state.get("error_message", "Unknown error")
    
    return {
        "processing_status": "failed",
        "processing_completed_at": datetime.now().isoformat(),
        "audit_notes": [
            "PROCESSING FAILED",
            f"Error: {error}",
            "Receipt flagged for manual review"
        ]
    }
