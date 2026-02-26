# =============================================================================
# FILE: config/celery.py
# PURPOSE: Configure Celery for async task processing
# =============================================================================
#  n
# 🧠 WHAT IS CELERY?
# ==================
# Celery is a distributed task queue that runs tasks in the background.
#
# Components:
# 1. BROKER (Redis): Holds the task queue
# 2. WORKER: Picks up tasks and executes them
# 3. BACKEND (Redis): Stores task results
#
# CONNECTION TO YOUR LEARNING:
# ----------------------------
# Remember async/await patterns? Celery is the production solution.
# Instead of await, you use .delay() to run tasks in background.
#
# =============================================================================

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('expense_ai')
# ↑ 'expense_ai' is the name of our project
#   This name appears in logs and the worker process name

# Configure Celery using Django settings
# All Celery config uses the CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')
# ↑ This means:
#   CELERY_BROKER_URL in settings.py → celery reads as broker_url
#   CELERY_RESULT_BACKEND → result_backend
#   etc.

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
# ↑ This finds all tasks.py files in Django apps
#   Our api/tasks.py will be automatically registered!

# =========================================================================
# CELERY CONFIGURATION
# =========================================================================
app.conf.update(
    # -----------------------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------------------
    task_serializer='json',      # Use JSON to serialize tasks
    accept_content=['json'],     # Only accept JSON
    result_serializer='json',    # Use JSON for results
    
    # -----------------------------------------------------------------
    # TIMEZONE
    # -----------------------------------------------------------------
    timezone='UTC',
    enable_utc=True,
    
    # -----------------------------------------------------------------
    # TASK EXECUTION
    # -----------------------------------------------------------------
    task_track_started=True,     # Track when tasks start
    task_time_limit=600,         # Hard limit: 10 minutes
    task_soft_time_limit=540,    # Soft limit: 9 minutes
    
    # -----------------------------------------------------------------
    # WORKER SETTINGS
    # -----------------------------------------------------------------
    worker_prefetch_multiplier=1,  # One task at a time
    # ↑ For AI tasks, we don't want workers grabbing too many
    #   Each task uses lots of memory/GPU
    
    # -----------------------------------------------------------------
    # RESULT BACKEND
    # -----------------------------------------------------------------
    result_expires=3600,  # Results expire after 1 hour
)


# =========================================================================
# DEBUG TASK (for testing)
# =========================================================================
@app.task(bind=True)
def debug_task(self):
    """
    A simple debug task to verify Celery is working
    
    Usage:
        from config.celery import debug_task
        result = debug_task.delay()
        print(result.get())  # Should print the request info
    """
    print(f'Request: {self.request!r}')
    return f'Celery is working! Task ID: {self.request.id}'


# =============================================================================
# HOW TO RUN CELERY
# =============================================================================
#
# 1. Start Redis (the broker):
#        docker-compose up redis -d
#
# 2. Start a Celery worker:
#        celery -A config worker --loglevel=info
#
#    Options:
#        -A config: Use config/celery.py
#        --loglevel=info: Show info logs
#        --concurrency=2: Run 2 worker processes
#        -Q default: Process tasks from 'default' queue
#
# 3. (Optional) Start Celery Beat for periodic tasks:
#        celery -A config beat --loglevel=info
#
# 4. (Optional) Flower for monitoring:
#        celery -A config flower
#        Open http://localhost:5555
#
# =============================================================================


# =============================================================================
# DOCKER COMPOSE CONFIGURATION
# =============================================================================
#
# Add these services to docker-compose.yml:
#
#   celery_worker:
#     build: .
#     command: celery -A config worker --loglevel=info
#     volumes:
#       - .:/app
#     env_file:
#       - .env
#     depends_on:
#       - db
#       - redis
#
#   celery_beat:
#     build: .
#     command: celery -A config beat --loglevel=info
#     volumes:
#       - .:/app
#     env_file:
#       - .env
#     depends_on:
#       - db
#       - redis
#
# =============================================================================
