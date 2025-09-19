# redis_client.py

from flask import current_app, session
from flask_security import current_user
import os
import redis
from app.utils.logger import logger

_redis_instance = None

def get_redis():
    """
    Возвращает singleton-экземпляр Redis с настройками из конфига Flask или окружения.
    Можно дергать откуда угодно: из Flask, celery, pure python.
    """
    global _redis_instance
    if _redis_instance:
        return _redis_instance

    # Пробуем взять настройки из Flask, если есть app context
    try:
        host = current_app.config.get("REDIS_HOST")
        port = current_app.config.get("REDIS_PORT")
    except Exception:
        logger.debug("Не удалось получить настройки Redis из Flask app context, используем переменные окружения.")
        host = os.environ.get("REDIS_HOST", "localhost")
        port = os.environ.get("REDIS_PORT", 6379)
    db = int(os.environ.get("REDIS_DB", 0))
    password = os.environ.get("REDIS_PASSWORD", None)

    _redis_instance = redis.StrictRedis(
        host=host,
        port=int(port),
        db=db,
        password=password,
        decode_responses=True
    )
    return _redis_instance

def redis_set(key, value, ex=None):
    """
    Сохраняет значение в Redis по ключу. ex — TTL в секундах.
    """
    r = get_redis()
    return r.set(key, value, ex=ex)

def redis_get(key):
    """
    Получает значение по ключу из Redis.
    """
    r = get_redis()
    return r.get(key)

def redis_delete(key):
    """
    Удаляет ключ из Redis.
    """
    r = get_redis()
    return r.delete(key)


def redis_keys(pattern):
    """
    Возвращает генератор ключей по паттерну через scan_iter.
    """
    r = get_redis()
    return r.scan_iter(pattern)


# Инвалидация кэша настроек пользователя использую этот кэш в context_processors.py
def invalidate_user_settings_cache(user_id: int):
    try:
        cache_key = f"user:{current_user.id}:profile:{session.get('profile_id')}:user_settings:v1"
        redis_delete(cache_key)
    except Exception:
        pass

# Инвалидация кэша профилей пользователя использую этот кэш в context_processors.py
def invalidate_profiles_cache(user_id: int):
    try:
        redis_delete(f"user:{user_id}:profiles:v1")
    except Exception:
        pass