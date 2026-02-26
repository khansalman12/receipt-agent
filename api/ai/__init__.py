# =============================================================================
# FILE: api/ai/__init__.py
# PURPOSE: Initialize the AI module and expose main components
# =============================================================================
#
# WHY THIS FILE?
# --------------
# In Python, __init__.py makes a directory a "package"
# This allows imports like: from api.ai import process_receipt
#
# Think of it as the "front door" to your AI module - you decide what's
# accessible from outside.
# =============================================================================

# We'll add imports here as we create the modules
# from .graph import process_receipt_graph
# from .chains import extraction_chain, fraud_chain

__all__ = [
    # List of public exports - these will be available when someone does:
    # from api.ai import *
]
