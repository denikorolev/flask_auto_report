# tasks/make_celery.py
from tasks.extensions import celery

def make_celery(app):
    # Читаем конфиг из файла (tasks/celeryconfig.py)
    celery.config_from_object('tasks.celeryconfig')
    
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        OPENAI_API_KEY=app.config.get("OPENAI_API_KEY", ""),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    
    # Импортируем сигналы в конце, чтобы они были зарегистрированы
    import tasks.celery_signals
    return celery
