# =============================================================================
# FILE: config/__init__.py
# PURPOSE: Make Celery available when Django starts
# =============================================================================
#
# 🧠 WHY IS THIS FILE IMPORTANT?
# ===============================
# When Django starts, it reads this __init__.py file.
# We import the Celery app here so it's READY when Django needs it.
#
# CONNECTION TO YOUR LEARNING:
# ----------------------------
# Remember Python packages? A folder is a package if it has __init__.py
# This file runs when the 'config' package is imported.
#
# By importing the Celery app here, we ensure:
# 1. Celery is configured before any tasks are registered
# 2. The @shared_task decorator can find the Celery app
# 3. Auto-discovery of tasks works correctly
#
# WITHOUT THIS:
#   from api.tasks import process_receipt_task  # Error! Celery not set up
#
# WITH THIS:
#   from api.tasks import process_receipt_task  # Works! Celery is ready
#
# =============================================================================

# Import Celery app so it's available when Django starts
from .celery import app as celery_app
# ↑ We import the 'app' from celery.py and rename it 'celery_app'
#   This is a Django convention

# Make celery_app available when importing from this package
__all__ = ('celery_app',)
# ↑ __all__ defines what gets exported when someone does:
#   from config import *
#
#   The tuple syntax ('celery_app',) is equivalent to ['celery_app']
#   but is more Pythonic for single-item exports
