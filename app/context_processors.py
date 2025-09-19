# app/context_processors.py

from flask import request, session
from flask_security import current_user
from app.utils.menu_constructor import build_menu
from app.utils.profile_constructor import ProfileSettingsManager
from app.models.models import UserProfile
from app.utils.logger import logger
import json
from app.utils.redis_client import redis_get, redis_set

# Вспомогательная функция для пропуска контекстного процессора на определённых эндпоинтах
def _skip_ctx(excluded: set) -> bool:
    """Return True when current request should skip this context processor."""
    try:
        # Fast path for static files
        if request.path.startswith("/static/"):
            return True
        ep = request.endpoint or ""
        return ep in excluded
    except Exception:
        # Если нет request-контекста — безопасно пропускаем
        return True

# --- Общая база исключений для гостевых/служебных страниц ---
BASE_EXCLUDE = frozenset({
    "error",
    "main.index",
    "security.login", "security.logout",
    "security.register",
    "security.send_confirmation", "security.confirm_email",
    "security.forgot_password", "security.reset_password",
    "info.success_registered",
})

# Специфика по процессорам
EXCLUDE_USER_SETTINGS = BASE_EXCLUDE
EXCLUDE_USER_RANK     = BASE_EXCLUDE
EXCLUDE_MENU          = BASE_EXCLUDE

# Здесь нужно чуть больше исключений (страница создания профиля без контекста профилей)
EXCLUDE_PROFILES = BASE_EXCLUDE | frozenset({
    "profile_settings.new_profile_creation",
})

def inject_menu():
    if _skip_ctx(EXCLUDE_MENU):
        return {}
    return {"menu": build_menu()}


# Инъекция настроек пользователя
def inject_user_settings():
    if _skip_ctx(EXCLUDE_USER_SETTINGS) or not current_user.is_authenticated:
        return {}
    
    profile_id = session.get("profile_id")
    if not profile_id:
        return {"user_settings": {}}
    # Ключ кэша для настроек пользователя (3 часа TTL)
    cache_key = None
    try:
        if current_user.is_authenticated:
            cache_key = f"user:{current_user.id}:profile:{profile_id}:user_settings:v1"
    except Exception:
        cache_key = None

    # 1) Попытка забрать из Redis
    if cache_key:
        try:
            raw = redis_get(cache_key)
            if raw:
                try:
                    settings = json.loads(raw)
                    return {"user_settings": settings}
                except Exception:
                    pass  # битый кэш — игнорируем
        except Exception:
            pass  # Redis недоступен — игнорируем

    # 2) Фоллбэк в БД/источник
    profile_settings = ProfileSettingsManager.load_profile_settings(profile_id)
    if not profile_settings:
        logger.warning("No profile settings found, returning empty dict")
        return {"user_settings": {}}

    # 3) Кладём в Redis (TTL 3 часа = 10800 сек)
    if cache_key:
        try:
            redis_set(cache_key, json.dumps(profile_settings, ensure_ascii=False), ex=10800)
        except Exception:
            pass

    return {"user_settings": profile_settings}


#  Информация о приложении
def inject_app_info(version):
    def _processor():
        return {"app_info": {"version": version, "author": "radiologary ltd"}}
    return _processor


# Информация о максимальном ранге пользователя
def inject_user_rank():
    if _skip_ctx(EXCLUDE_USER_RANK) or not current_user.is_authenticated:
        return {"user_max_rank": 0}
    
    user_max_rank = session.get("user_max_rank")
    if user_max_rank is not None:
        return {"user_max_rank": user_max_rank}
    user_max_rank = current_user.get_max_rank()
    if not user_max_rank:
        user_max_rank = 0
    session["user_max_rank"] = user_max_rank
    return {"user_max_rank": user_max_rank}


def inject_current_profile_data():
    if _skip_ctx(EXCLUDE_PROFILES) or not current_user.is_authenticated:
        return {"profiles": None}

    cache_key = f"user:{current_user.id}:profiles:v1"

    # 1) Пытаемся взять базовый список профилей из Redis (без is_active)
    try:
        raw = redis_get(cache_key)
        if raw:
            try:
                base_profiles = json.loads(raw)
                active_id = session.get("profile_id")
                profiles = []
                for p in base_profiles:
                    item = dict(p)
                    item["is_active"] = (
                        active_id is not None and item["id"] == int(active_id)
                    )
                    profiles.append(item)
                return {"profiles": profiles}
            except Exception:
                pass
    except Exception:
        pass

    # 2) Фоллбэк: берём из БД
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    if not user_profiles:
        return {"profiles": None}

    base_profiles = []
    for profile in user_profiles:
        base_profiles.append({
            "id": profile.id,
            "profile_name": profile.profile_name,
            "description": profile.description,
            "is_default": profile.default_profile,
        })

    # 3) Пишем базовый список в Redis (TTL 3 часа)
    try:
        redis_set(cache_key, json.dumps(base_profiles, ensure_ascii=False), ex=10800)
    except Exception:
        pass

    # 4) Добавляем is_active на лету
    active_id = session.get("profile_id")
    profiles = []
    for p in base_profiles:
        item = dict(p)
        item["is_active"] = (
            active_id is not None and item["id"] == int(active_id)
        )
        profiles.append(item)

    return {"profiles": profiles}