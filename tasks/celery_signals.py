# tasks/celery_signals.py

from celery.signals import before_task_publish
from datetime import datetime, timezone
from app.utils.redis_client import redis_set

# При каждом добавлении задачи в очередь мы сохраняем время добавления в Redis
@before_task_publish.connect
def store_enqueue_time(sender=None, headers=None, **kwargs):
    task_id = headers.get('id')
    if task_id:
        now = datetime.now(timezone.utc).isoformat()
        redis_set(f"task_enqueue_time:{task_id}", now, ex=600)