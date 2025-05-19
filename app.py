# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g
from flask_security import logout_user, current_user
import logging
from datetime import datetime
from config import get_config
from flask_migrate import Migrate
from models import db, User, UserProfile, Role
from menu_constructor import build_menu
from profile_constructor import ProfileSettingsManager
from db_processing import sync_all_profiles_settings
from utils.mail_helpers import send_email_via_zeptomail
from werkzeug.middleware.proxy_fix import ProxyFix
from logger import logger
import os
from file_processing import prepare_impression_snippets
from utils.mail_helpers import CustomMailUtil, ExtendedRegisterForm
from flask_wtf.csrf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.decorators import auth_required, roles_required
from flask_security.signals import user_registered

# Импортирую блюпринты
from working_with_reports import working_with_reports_bp  
from my_reports import my_reports_bp 
from report_settings import report_settings_bp  
from new_report_creation import new_report_creation_bp
from editing_report import editing_report_bp
from profile_settings import profile_settings_bp
from openai_api import openai_api_bp
from key_words import key_words_bp
from admin import admin_bp

version = "0.9.5.9"

app = Flask(__name__)
app.config.from_object(get_config()) # Load configuration from file config.py

# Инициализация базы данных
db.init_app(app)

# Инициализация миграций
migrate = Migrate(app, db)

# Инициализирую Flask-security-too
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, mail_util_cls=CustomMailUtil, register_form=ExtendedRegisterForm)

# Инициализация CSRF-защиты
csrf = CSRFProtect(app)
csrf.init_app(app) # Инициализация CSRF-защиты


# Обработчик сигнала user_registered и автоматическое назначение роли 'user'
@user_registered.connect_via(app)
def assign_default_role(sender, user, **extra):
    """Назначаем роль 'user' для новых пользователей"""
    default_role = Role.query.filter_by(name="user").first()
    if default_role:
        user.roles.append(default_role)  # Добавляем роль
    db.session.commit()  # Сохраняем изменения
    # send_welcome_email(user)
    # Временный вывод подтверждающей ссылки в лог
    # from flask_security.utils import generate_confirmation_token
    # token = generate_confirmation_token(user)
    # confirm_url = url_for('security.confirm_email', token=token, _external=True)
    # logger.warning(f"📬 Подтверждающая ссылка: {confirm_url}")

# Register Blueprints
app.register_blueprint(working_with_reports_bp, url_prefix="/working_with_reports")
app.register_blueprint(my_reports_bp, url_prefix="/my_reports")
app.register_blueprint(report_settings_bp, url_prefix="/report_settings")
app.register_blueprint(editing_report_bp, url_prefix="/editing_report")
app.register_blueprint(new_report_creation_bp, url_prefix="/new_report_creation")
app.register_blueprint(profile_settings_bp, url_prefix="/profile_settings")
app.register_blueprint(openai_api_bp, url_prefix="/openai_api")
app.register_blueprint(key_words_bp, url_prefix="/key_words")
app.register_blueprint(admin_bp, url_prefix="/admin")


# Добавляю контекстные процессоры

# Добавляю контекстный процессор для меню
@app.context_processor
def inject_menu():
    """Добавляет меню в глобальный контекст Jinja."""
    excluded_endpoints = {"error", "security.login", "security.logout", "index"}
    if request.endpoint in excluded_endpoints:
        return {}
    return {"menu": build_menu()}

# Добавляю контекстный процессор для настроек профиля
@app.context_processor
def inject_user_settings():
    """Добавляет все настройки профиля в глобальный контекст Jinja."""
    excluded_endpoints = {"error", "security.login", "security.logout", "custom_logout", "index", "profile_settings.create_profile"}
    if request.endpoint in excluded_endpoints:
        return {}
    
    user_settings = app.config.get("PROFILE_SETTINGS", {})

    if not user_settings:
        user_settings = ProfileSettingsManager.load_profile_settings()
        
    return {"user_settings": user_settings}

# Добавляю контекстный процессор для версии приложения
@app.context_processor
def inject_app_info():
    """Добавляет информацию о приложении в глобальный контекст Jinja."""
    app_info = {"version": version, "author": "radiologary ltd"}
    return {"app_info": app_info}

# Добавляю контекстный процессор для ранга пользователя 
# сейчас не используется, но потом буду так ограничивать 
# доступ к некоторым частям страниц
@app.context_processor
def inject_user_rank():
    if not current_user.is_authenticated:
        return {"user_max_rank": 0}
    user_max_rank = current_user.get_max_rank()
    if not user_max_rank:
        user_max_rank = 0   
    return {"user_max_rank": user_max_rank}



# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    # Исключения для статических файлов и маршрутов, которые не требуют профиля
    if request.path.startswith('/static/') or request.endpoint in [
        "security.login", "security.logout", "security.register", "custom_logout",
        "security.forgot_password", "security.reset_password", 
        "security.change_password","profile_settings.choosing_profile", 
        "error", "index", "profile_settings.create_profile", "profile_settings.set_default_profile"
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
    
    # Если я здесь, значит пользователь авторизован и у него нет профиля в g
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
    
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    # Если профиля нет ни в сессии ни в g то выясняем если ли вообще 
    # у пользователя профили, сколько их и в зависимости 
    # от этого маршрутизируем
    if not user_profiles:
        logger.info("User has no profiles")
        # Если у пользователя нет профилей отпраляем его создавать профиль
        return redirect(url_for("profile_settings.choosing_profile"))
    elif len(user_profiles) == 1:
        logger.info("User has only one profile")
        # Если только один профиль, устанавливаем его и отправляем на выбор отчета
        profile = user_profiles[0]
        session["profile_id"] = profile.id
        g.current_profile = profile
        ProfileSettingsManager.load_profile_settings()
        return redirect(url_for("working_with_reports.choosing_report"))
    elif len(user_profiles) > 1 and UserProfile.get_default_profile(current_user.id):
        logger.info("User has multiple profiles and default profile")
        # Если у пользователя несколько профилей и есть дефолтный, устанавливаем его и отправляем на выбор отчета
        profile = UserProfile.get_default_profile(current_user.id)
        session["profile_id"] = profile.id
        g.current_profile = profile
        ProfileSettingsManager.load_profile_settings()
        return redirect(url_for("working_with_reports.choosing_report"))
    else:
        logger.info("User has multiple profiles and no default profile")
        # Если профилей несколько и дефолтный не выбран, перенаправляем для выбора профиля
        return redirect(url_for("profile_settings.choosing_profile"))
                               
# Запускаем различные синхронизаторы при первом запуске сессии
@app.before_request
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
            session["lang"] = app.config.get("PROFILE_SETTINGS", {}).get("APP_LANGUAGE", "ru")
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


# Маршрут для главной страницы
@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template("index.html", title="Главная страница")
                           

@app.route("/custom_logout", methods=["POST", "GET"])
def custom_logout():
    print("inside logout route")
    session.clear()
    print("session cleared")
    logout_user()
    print("user logged out")
    return redirect(url_for("index"))



@app.route("/error", methods=["POST", "GET"])
def error():
    print("inside error route")
    message = request.args.get("message") or "no message"
    return render_template("error.html",
                           message=message)


# Обработка ошибок
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Errorhandler: {str(e)}")
    er = str(e)
    return f"Internal Server Error {er}", 500


# Это обязательная часть для разрыва сессии базы данных после каждого обращения
@app.teardown_appcontext 
def close_db(error):
    db.session.remove()



# Playgroung

@app.route("/playground", methods=["GET", "POST"])
@auth_required()
@roles_required("superadmin")
def playground():
    logger.info("Playground route accessed")
    if request.method == "POST":
        logger.info("Playground POST request received")
       
    
    return render_template(
        "playground.html",
        title="Playground"
    )
    

    

# Фильтруем логи 


if os.getenv("FLASK_ENV") == "local":
    from flask_debugtoolbar import DebugToolbarExtension
    class StaticFilter(logging.Filter):
        """Фильтр для исключения запросов к /static/."""
        def filter(self, record):
            return not record.getMessage().startswith("GET /static/")

    class DebugToolbarFilter(logging.Filter):
        """Фильтр для исключения запросов к /_debug_toolbar/static/."""
        def filter(self, record):
            return not record.getMessage().startswith("GET /_debug_toolbar/static/")

    class RemoveHeadersFilter(logging.Filter):
        """Фильтр для исключения заголовков запросов из логов."""
        def filter(self, record):
            return not record.getMessage().startswith("Headers:")
    
    class IgnoreFaviconFilter(logging.Filter):
        """Исключает запросы к favicon.ico из логов."""
        def filter(self, record):
            return not record.getMessage().startswith("GET /favicon.ico")
        
    
    
    # Подключаем фильтры к логгеру Flask
    app.logger.addFilter(StaticFilter())
    app.logger.addFilter(DebugToolbarFilter())
    app.logger.addFilter(RemoveHeadersFilter())
    app.logger.addFilter(IgnoreFaviconFilter())
   

    # Подключаем фильтры к логгеру Werkzeug
    werkzeug_logger = logging.getLogger("werkzeug")
    
    werkzeug_logger.addFilter(StaticFilter())
    werkzeug_logger.addFilter(DebugToolbarFilter())
    werkzeug_logger.addFilter(RemoveHeadersFilter())
    werkzeug_logger.addFilter(IgnoreFaviconFilter())





if __name__ == "__main__":
    # Если приложение запущено не в режиме продакшена (например, локальная разработка), запускаем Flask встроенным сервером
    if os.getenv("FLASK_ENV") == "local":
        app.debug = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension(app)
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))
        
        

