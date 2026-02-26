"""LangGraph workflow for receipt processing."""

from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from .state import ReceiptProcessingState, create_initial_state
from .nodes import (
    load_image_node,
    extract_data_node,
    validate_data_node,
    fraud_check_node,
    finalize_node,
    error_handler_node,
)


def route_after_extraction(state: ReceiptProcessingState) -> Literal["validate", "error"]:
    """Route after extraction based on success/failure."""
    if state.get("processing_status") == "failed":
        return "error"
    if state.get("extracted_data") is None:
        return "error"
    return "validate"


def route_after_validation(state: ReceiptProcessingState) -> Literal["fraud_check", "needs_review"]:
    """Route after validation based on error count."""
    errors = state.get("validation_errors", [])
    if len(errors) > 3:
        return "needs_review"
    return "fraud_check"


def route_after_fraud_check(state: ReceiptProcessingState) -> Literal["finalize", "flag_fraud"]:
    """Route after fraud check based on score."""
    fraud_score = state.get("fraud_score", 0)
    if fraud_score >= 70:
        return "flag_fraud"
    return "finalize"


def flag_fraud_node(state: ReceiptProcessingState):
    """Handle high-fraud-score receipts."""
    from datetime import datetime
    
    fraud_analysis = state.get("fraud_analysis", {})
    
    return {
        "processing_status": "flagged_fraud",
        "processing_completed_at": datetime.now().isoformat(),
        "audit_notes": [
            f"FRAUD ALERT: Score {state.get('fraud_score', 0)}/100",
            f"Risk level: {fraud_analysis.get('risk_level', 'UNKNOWN')}",
            f"Flags: {', '.join(fraud_analysis.get('flags', []))}",
        ]
    }


def needs_review_node(state: ReceiptProcessingState):
    """Handle receipts that need manual review."""
    from datetime import datetime
    
    validation_errors = state.get("validation_errors", [])
    
    return {
        "processing_status": "needs_review",
        "processing_completed_at": datetime.now().isoformat(),
        "audit_notes": [
            f"MANUAL REVIEW REQUIRED: {len(validation_errors)} validation errors",
            *[f"  - {error}" for error in validation_errors],
        ]
    }


def build_receipt_processing_graph():
    """Construct the complete LangGraph workflow."""
    
    graph_builder = StateGraph(ReceiptProcessingState)
    
    # Add nodes
    graph_builder.add_node("load_image", load_image_node)
    graph_builder.add_node("extract_data", extract_data_node)
    graph_builder.add_node("validate", validate_data_node)
    graph_builder.add_node("fraud_check", fraud_check_node)
    graph_builder.add_node("finalize", finalize_node)
    graph_builder.add_node("flag_fraud", flag_fraud_node)
    graph_builder.add_node("needs_review", needs_review_node)
    graph_builder.add_node("error", error_handler_node)
    
    # Add edges
    graph_builder.add_edge(START, "load_image")
    graph_builder.add_edge("load_image", "extract_data")
    
    # Conditional edges
    graph_builder.add_conditional_edges(
        "extract_data",
        route_after_extraction,
        {"validate": "validate", "error": "error"}
    )
    
    graph_builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {"fraud_check": "fraud_check", "needs_review": "needs_review"}
    )
    
    graph_builder.add_conditional_edges(
        "fraud_check",
        route_after_fraud_check,
        {"finalize": "finalize", "flag_fraud": "flag_fraud"}
    )
    
    # Terminal edges
    graph_builder.add_edge("finalize", END)
    graph_builder.add_edge("flag_fraud", END)
    graph_builder.add_edge("needs_review", END)
    graph_builder.add_edge("error", END)
    
    # Compile
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)


# Create graph instance
receipt_processing_graph = build_receipt_processing_graph()


def process_receipt(receipt_id: str, image_path: str, report_id: str) -> ReceiptProcessingState:
    """Process a receipt through the AI pipeline."""
    initial_state = create_initial_state(
        receipt_id=receipt_id,
        image_path=image_path,
        report_id=report_id
    )
    
    config = {"configurable": {"thread_id": receipt_id}}
    
    return receipt_processing_graph.invoke(initial_state, config)


def get_graph_visualization():
    """Get Mermaid diagram of the graph."""
    try:
        return receipt_processing_graph.get_graph().draw_mermaid()
    except Exception:
        return """
        graph TD
            START --> load_image
            load_image --> extract_data
            extract_data --> validate
            extract_data --> error
            validate --> fraud_check
            validate --> needs_review
            fraud_check --> finalize
            fraud_check --> flag_fraud
            finalize --> END
            flag_fraud --> END
            needs_review --> END
            error --> END
        """
