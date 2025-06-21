# extensions.py
from celery import Celery
from celery.signals import before_task_publish
from datetime import datetime, timezone
from app.utils.redis_client import redis_set

celery = Celery()
celery.config_from_object('tasks.celeryconfig')

def make_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery



# При каждом добавлении задачи в очередь мы сохраняем время добавления в Redis
@before_task_publish.connect
def store_enqueue_time(sender=None, headers=None, **kwargs):
    task_id = headers.get('id')
    if task_id:
        now = datetime.now(timezone.utc).isoformat()
        redis_set(f"task_enqueue_time:{task_id}", now, ex=600)