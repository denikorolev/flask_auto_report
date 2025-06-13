# celeryconfig.py

from celery.schedules import crontab

beat_schedule = {
    'cancel-stuck-tasks-every-minute': {
        'task': 'celery_tasks.celery_cancel_stuck_tasks', 
        'schedule': crontab(minute='*'),
    },
    'cancel-stale-polled-tasks-every-10-seconds': {
        'task': 'celery_tasks.celery_cancel_stale_polled_tasks',
        'schedule': 10.0,
    },
}

timezone = "UTC"
enable_utc = True
