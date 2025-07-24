# app/before_request_handlers.py

from flask import request, session, redirect, url_for, current_app
from flask_login import current_user
from .utils.logger import logger
from .models.models import UserProfile, AppConfig, ReportCategory
from .utils.db_processing import sync_all_profiles_settings
from tasks.celery_tasks import async_prepare_impression_snippets
import json

# логика для 100% уверенности что данные профиля пользователя и настройки пользователя загружены
def load_current_profile():
    # Исключения для статических файлов и маршрутов, которые не требуют профиля
    if request.path.startswith('/static/') or request.path.startswith("/_debug_toolbar/") or request.endpoint in [
        "security.login", "security.logout", "security.register", "custom_logout",
        "security.forgot_password", "security.reset_password", 
        "security.change_password","profile_settings.new_profile_creation", 
        "error", "main.index", "profile_settings.create_profile", "profile_settings.set_default_profile", "feedback_form"
    ]:
        return None
    # Если пользователь не авторизован, удаляем профиль из сессии
    if not current_user.is_authenticated:
        session.pop("profile_id", None)
        session.pop("profile_name", None)
        session.pop("lang", None)
        logger.info("User is not authenticated")
        return

    profile_id = session.get("profile_id")

    # Если профиль уже в сессии то ничего не делаем
    if profile_id:
        if not session.get("profile_name"):
            print(f"Profile id from session: {profile_id} has no profile name in session")
            profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
            if profile:
                session["profile_name"] = profile.profile_name
        if not session.get("lang") or session.get("lang") == "default_language":
            print("Profile id from session has no language in session")
            language = AppConfig.get_setting(profile_id, "APP_LANGUAGE", "default_language")
            session["lang"] = language
        logger.info(f"😎 Профиль из сессии: {profile_id} с именем {session['profile_name']} и с языком {session.get('lang')} присутствует в сессии")
        return

    profile = UserProfile.get_default_profile(current_user.id)
    # Если профиля нет в сессии то выясняем есть ли вообще 
    # у пользователя профили, сколько их и в зависимости 
    # от этого маршрутизируем
    if not profile:
        logger.info("У пользователя нет ни одного профиля")
        # Если у пользователя нет профилей отпраляем его создавать профиль
        return redirect(url_for("profile_settings.new_profile_creation"))
    else:
        logger.info(f"У пользователя есть профиль по умолчанию {profile.profile_name}")
        session["profile_id"] = profile.id
        session["profile_name"] = profile.profile_name
        session["lang"] = AppConfig.get_setting(profile.id, "APP_LANGUAGE", "default_language")
        return 
    


# Запускаем различные синхронизаторы при первом запуске сессии
def one_time_sync_tasks():
    """
    Запускает одноразовые фоновые задачи для пользователя при первом входе в сессию:
    - Синхронизация настроек профилей.
    - (В будущем) другие одноразовые задачи, например, обновления данных.
    """
    
    if request.path.startswith('/static/') or request.path.startswith("/_debug_toolbar/") or request.endpoint in [
        "security.login", "security.logout", "security.register", "custom_logout",
        "security.forgot_password", "security.reset_password", 
        "security.change_password","profile_settings.new_profile_creation", 
        "error", "main.index", "profile_settings.create_profile", "profile_settings.set_default_profile", "feedback_form"
    ]:
        return
            
    if not current_user.is_authenticated:
        return  # Если пользователь не вошел — ничего не делаем
    
    profile_id = session.get("profile_id")
    if not profile_id:
        logger.info("Профиль не выбран!!! Пропускаем синхронизацию настроек профилей.")
        return

    if not session.get("user_data_synced"):  # Проверяем, была ли уже выполнена синхронизация
        logger.info("Синхронизация настроек профилей")
        sync_all_profiles_settings(current_user.id)
            
        try:
            except_words = AppConfig.get_setting(profile_id, "EXCEPT_WORDS", [])
            user_id = current_user.id
            user_email = current_user.email
            # Запуск полной подготовки файлов (удаление старых + генерация новых + загрузка в OpenAI)
            task = async_prepare_impression_snippets.delay(profile_id, user_id, user_email, except_words)
            logger.info(f"📂 Начата подготовка Impression snippets для профиля {profile_id}")
            session["impression_snippets_task_id"] = task.id # не использую, просто бросаю задачу, автоматически редис 
            # вычистится от нее через 24 часа. Сохраняю в сессию, возможно потом сделаю обратную связь с пользователем, 
            # чтобы он видел прогресс задачи
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при подготовке impression snippets: {e}")
        logger.debug("Synced profile settings")
        session["user_data_synced"] = True  # Помечаем, что синхронизация выполнена
        
    # ---- Проверка категорий пользователя ----
    # 1. Проверка в session
    if not session.get("categories_setup"):
        logger.info("Категории не настроены в сессии. Начинаем настройку...")
        # Здесь можно добавить логику для настройки категорий

        # 2. Пробуем взять из AppConfig (только если в session нет)
        categories_json = AppConfig.get_setting(profile_id, "CATEGORIES_SETUP")
        if categories_json and categories_json in ('None', ''):
            categories_json = "[]"
        if categories_json:
            try:
                categories_data = json.loads(categories_json)
                print(f"Категории из AppConfig: {categories_data}")
                # Если не пустой и не [] — используем
                if isinstance(categories_data, list) and categories_data:
                    session["categories_setup"] = True
                    print("удалось загрузить категории из AppConfig")
                    return
            except Exception as e:
                logger.error(f"Ошибка разбора JSON категорий из AppConfig: {e}")
        print(f"Категории из AppConfig пустые или невалидные: {categories_json} будем искать в базе")
        # 3. Если нет — пробуем собрать из базы (это может быть первый вход или reset)
        categories = ReportCategory.get_categories_tree(profile_id=profile_id)
        print(f"Категории из базы: {categories}")
        if categories:
            try:
                print(f"будем грузить категории из базы тогда")
                categories_json = json.dumps(categories, ensure_ascii=False)
                AppConfig.set_setting(profile_id, "CATEGORIES_SETUP", categories_json)
                session["categories_setup"] = True
                # вот тут нужно будет сделать редирект на страницу настройки категорий
                return
            except Exception as e:
                logger.error(f"Ошибка при сохранении категорий в AppConfig: {e}")

        # 4. Если ни в базе, ни в AppConfig ничего нет — редиректим на настройку
        logger.info("Категории не найдены ни в базе, ни в AppConfig. Редирект на страницу создания профиля.")
        return redirect(url_for("profile_settings.new_profile_creation", profile_id=profile_id))

