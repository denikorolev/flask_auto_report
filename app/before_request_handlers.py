# app/before_request_handlers.py

from flask import g, request, session, redirect, url_for, current_app
from flask_login import current_user
from logger import logger
from models import UserProfile
from profile_constructor import ProfileSettingsManager
from db_processing import sync_all_profiles_settings
from file_processing import prepare_impression_snippets

# Логика для того, чтобы сделать данные профиля доступными 
# в любом месте программы через g.current_profile
def load_current_profile():
    # Исключения для статических файлов и маршрутов, которые не требуют профиля
    if request.path.startswith('/static/') or request.endpoint in [
        "security.login", "security.logout", "security.register", "custom_logout",
        "security.forgot_password", "security.reset_password", 
        "security.change_password","profile_settings.new_profile_creation", 
        "error", "main.index", "profile_settings.create_profile", "profile_settings.set_default_profile", "feedback_form"
    ]:
        return None
    # Если пользователь не авторизован, удаляем профиль из g и сессии    
    if not current_user.is_authenticated:
        g.current_profile = None
        session.pop("profile_id", None)
        logger.info("User is not authenticated")
        return
    
    # Если профиль уже установлен в g, пропускаем
    if hasattr(g, "current_profile") and g.current_profile:
        logger.info("Profile is already set in g")
        return
    
    profile_id = session.get("profile_id")
    
    if profile_id:
        # Пытаемся загрузить профиль из базы тот профиль, который висит 
        # в сессии и установить его в g
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        if profile:
            g.current_profile = profile
            return
        else:
            # Если профиль из сессии не найден в базе или не 
            # соответствует текущему пользователю, удаляем его из 
            # сессии и идем ниже и ищем профиль текущего пользователя
            print("Profile not found in db or doesn't belong to current user")
            session.pop("profile_id", None)
    
    profile = UserProfile.get_default_profile(current_user.id)
    # Если профиля нет ни в сессии ни в g то выясняем если ли вообще 
    # у пользователя профили, сколько их и в зависимости 
    # от этого маршрутизируем
    if not profile:
        logger.info("User has no profiles")
        # Если у пользователя нет профилей отпраляем его создавать профиль
        return redirect(url_for("profile_settings.new_profile_creation"))
    else:
        logger.info(f"User has default profile {profile.profile_name}")
        session["profile_id"] = profile.id
        g.current_profile = profile
        ProfileSettingsManager.load_profile_settings()
        return redirect(url_for("working_with_reports.choosing_report"))
    


# Запускаем различные синхронизаторы при первом запуске сессии
def one_time_sync_tasks():
    """
    Запускает одноразовые фоновые задачи для пользователя при первом входе в сессию:
    - Синхронизация настроек профилей.
    - (В будущем) другие одноразовые задачи, например, обновления данных.
    """
            
    if not current_user.is_authenticated:
        return  # Если пользователь не вошел — ничего не делаем

    if not session.get("synced"):  # Проверяем, была ли уже выполнена синхронизация
        
        logger.info("Синхронизация настроек профилей")
        sync_all_profiles_settings(current_user.id)
        try:
            # Установка настройки языка в зависимости от профиля
            session["lang"] = current_app.config.get("PROFILE_SETTINGS", {}).get("APP_LANGUAGE", "ru")
            print(f"Установлен язык: {session['lang']}")
        except Exception as e: 
            logger.warning(f"⚠️ Ошибка при установке языка: {e}")
        try:
            # Запуск полной подготовки файлов (удаление старых + генерация новых + загрузка в OpenAI)
            prepare_impression_snippets(g.current_profile.id)
            logger.info(f"📂 Impression snippets успешно подготовлены для профиля {g.current_profile.id}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при подготовке impression snippets: {e}")
        logger.debug("Synced profile settings")
        session["synced"] = True  # Помечаем, что синхронизация выполнена

