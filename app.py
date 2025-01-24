# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g
from flask_login import current_user
import logging
from config import get_config
from flask_migrate import Migrate
from models import db, User, UserProfile, Role
from menu_constructor import build_menu
from profile_constructor import ProfileSettingsManager

import os
import logging
    

from flask_wtf.csrf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.decorators import auth_required
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

version = "0.8.7"

app = Flask(__name__)
app.config.from_object(get_config()) # Load configuration from file config.py

# Инициализация базы данных
db.init_app(app)

# Инициализация миграций
migrate = Migrate(app, db)

# Инициализирую Flask-security-too
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

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
    print("inject_menu started-------")
    excluded_endpoints = {"error", "security.login", "security.logout", "index"}
    if request.endpoint in excluded_endpoints:
        print("inject_menu end work because of exclusion-------")
        return {}
    
    return {"menu": build_menu()}

# Добавляю контекстный процессор для настроек профиля
@app.context_processor
def inject_user_settings():
    """Добавляет все настройки профиля в глобальный контекст Jinja."""
    print("inject_user_settings started-------")
    excluded_endpoints = {"error", "security.login", "security.logout", "index", "profile_settings.create_profile"}
    if request.endpoint in excluded_endpoints:
        print("inject_user_settings end work because of exclusion-------")
        return {}
    
    user_settings = app.config.get("PROFILE_SETTINGS", {})

    print(f"User settings from app.config: {user_settings}")
    if not user_settings:
        print("User settings not found in app.config, loading from ProfileSettingsManager")
        user_settings = ProfileSettingsManager.load_profile_settings()
        
    print(f"inject_user_settings end work. User settings from context processor: {user_settings}")
    return {"user_settings": user_settings}

# Добавляю контекстный процессор для версии приложения
@app.context_processor
def inject_app_info():
    """Добавляет информацию о приложении в глобальный контекст Jinja."""
    app_info = {"version": version, "author": "dgk"}
    return {"app_info": app_info}

# Добавляю контекстный процессор для ранга пользователя 
# сейчас не используется, но потом буду так ограничивать 
# доступ к некоторым частям страниц
@app.context_processor
def inject_user_rank():
    print("inject_user_rank started-------")
    if not current_user.is_authenticated:
        print("inject_user_rank end work because of user is not authenticated end user's rank is 0 -------")
        return {"user_max_rank": 0}
    user_max_rank = current_user.get_max_rank()
    if not user_max_rank:
        print("user_max_rank from get_max_rank has returtned as None")
        user_max_rank = 0   
    print(f"inject_user_rank end work. User's rank is {user_max_rank} -------")
    return {"user_max_rank": user_max_rank}




# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        print("Database connection successful", "success")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}", "error")
        return False



# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    
    # Исключения для статических файлов и маршрутов, которые не требуют профиля
    if request.path.startswith('/static/') or request.endpoint in [
        "security.login", "security.logout", "security.register", 
        "security.forgot_password", "security.reset_password", 
        "security.change_password","profile_settings.choosing_profile", 
        "error", "index", "profile_settings.create_profile"
    ]:
        return None
    # Если пользователь не авторизован, удаляем профиль из g и сессии    
    if not current_user.is_authenticated:
        g.current_profile = None
        session.pop("profile_id", None)
        return
    
    # Если профиль уже установлен в g, пропускаем
    if hasattr(g, "current_profile") and g.current_profile:
        print("skipping - profile is already set in g")
        return
    
    # Если я здесь, значит пользователь авторизован и у него нет профиля в g
    profile_id = session.get("profile_id")
    
    if profile_id:
        # Пытаемся загрузить профиль из базы тот профиль, который висит 
        # в сессии и установить его в g
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        if profile:
            g.current_profile = profile
            print("Profile loaded to g from session")
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
        print("User has no profiles")
        # Если у пользователя нет профилей отпраляем его создавать профиль
        return redirect(url_for("profile_settings.choosing_profile"))
    elif len(user_profiles) == 1:
        print("User has only one profile")
        # Если только один профиль, устанавливаем его и отправляем на выбор отчета
        profile = user_profiles[0]
        session["profile_id"] = profile.id
        g.current_profile = profile
        ProfileSettingsManager.load_profile_settings()
        return redirect(url_for("working_with_reports.choosing_report"))
    elif len(user_profiles) > 1 and UserProfile.get_default_profile(current_user.id):
        print("User has multiple profiles and has default profile")
        # Если у пользователя несколько профилей и есть дефолтный, устанавливаем его и отправляем на выбор отчета
        profile = UserProfile.get_default_profile(current_user.id)
        session["profile_id"] = profile.id
        g.current_profile = profile
        ProfileSettingsManager.load_profile_settings()
        return redirect(url_for("working_with_reports.choosing_report"))
    else:
        print("User has multiple profiles and no default profile")
        # Если профилей несколько и дефолтный не выбран, перенаправляем для выбора профиля
        return redirect(url_for("profile_settings.choosing_profile"))
                               

# Маршрут для главной страницы
@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template("index.html", title="Главная страница")
                           


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
        
        

