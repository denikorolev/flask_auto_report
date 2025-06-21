# wsgi.py
# Только для запуска приложения Flask с помощью Gunicorn
from app import create_app
app = create_app()
