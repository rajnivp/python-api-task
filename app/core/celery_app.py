from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app: Celery = Celery(
    'tao_service',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.background_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
)
