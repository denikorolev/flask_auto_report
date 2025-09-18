# app/security/signals.py

from flask_security.signals import user_registered
from app.models.models import db

@user_registered.connect_via(None)  
def assign_default_role(sender, user, **extra):
    """Назначаем роль 'user' для новых пользователей"""
    user.add_role("user")