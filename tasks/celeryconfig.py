# celeryconfig.py

from celery.schedules import crontab

beat_schedule = {
    'cancel-stuck-tasks-every-minute': {
        'task': 'tasks.celery_tasks.celery_cancel_stuck_tasks', 
        'schedule': crontab(minute='*'),
    },
    'cancel-stale-polled-tasks-every-15-seconds': {
        'task': 'tasks.celery_tasks.celery_cancel_stale_polled_tasks',
        'schedule': 15.0,
    },
}

