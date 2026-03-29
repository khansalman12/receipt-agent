"""Celery application configuration for async receipt processing."""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('expense_ai')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)


@app.task(bind=True)
def debug_task(self):
    """Verify Celery connectivity. Returns request metadata."""
    return f'Celery OK | Task ID: {self.request.id}'
