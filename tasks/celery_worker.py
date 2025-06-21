# tasks/celery_worker.py

from app import create_app
from tasks.make_celery import make_celery

app = create_app()
celery = make_celery(app)