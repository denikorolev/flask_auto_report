# app/security/signals.py

from flask_security.signals import user_registered
from models import db, Role

@user_registered.connect_via(None)  
def assign_default_role(sender, user, **extra):
    """Назначаем роль 'user' для новых пользователей"""
    default_role = Role.query.filter_by(name="user").first()
    if default_role:
        user.roles.append(default_role)