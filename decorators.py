from functools import wraps
from flask import abort
from flask_login import current_user

def require_role_rank(min_rank):
    """
    Декоратор для проверки, чтобы у текущего пользователя был ранг,
    равный или выше указанного.
    
    Args:
        min_rank (int): Минимальный ранг для доступа (1-user, 4-superadmin).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_max_rank = current_user.get_max_rank()
            if user_max_rank is None or user_max_rank < min_rank:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator
