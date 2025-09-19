# app/security/signals.py

from flask import current_app
from flask_security.signals import user_registered
from app.extensions import db
from app.models.models import Role
from app.utils.logger import logger


def _assign_default_role(sender, user, **extra):
    """
    Назначаем роль 'user' для новых пользователей
    """
    try:
        role = Role.query.filter_by(name="user").first()
        if not role:
            logger.warning("Роль 'user' не найдена, создаю новую.")
            role = Role(name="user", description="Regular user", rank=1)
            db.session.add(role)
            db.session.flush()  # Сохраняем роль, чтобы получить её ID
        
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
            logger.info(f"Назначена роль 'user' для пользователя {user.email}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при назначении роли 'user' для пользователя {user.email}: {e}")


def init_security_signals(app):    
    user_registered.connect(_assign_default_role, app)
    logger.info("[security] user_registered signal connected")   