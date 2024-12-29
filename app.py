# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g, jsonify
from flask_login import current_user
import logging
from config import get_config, Config
from flask_migrate import Migrate
from models import db, User, UserProfile, Role
import os
import logging
if os.getenv("FLASK_ENV") == "local":
    from flask_debugtoolbar import DebugToolbarExtension
    



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

version = "0.7.4"

app = Flask(__name__)
app.config.from_object(get_config()) # Load configuration from file config.py

# Initialize default menu
app.config['MENU'] = []

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# uuid_butt = str(uuid.uuid4())

#Initialize LoginManager turn off for Flask-Security
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "security.login"


# Инициализирую Flask-security-too
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

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

#Load user callback turn off for Flask-Security
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))


# Обработка ошибок
# @app.errorhandler(Exception)
# def handle_exception(e):
#     app.logger.error(f"My errorhandler Exception occurred: {str(e)}")
#     return "Internal Server Error", 500

# @app.errorhandler(400)
# def handle_bad_request(e):
#     app.logger.error(f"My errorhandler CSRF error: {str(e)}")
#     return "CSRF token missing or invalid", 400


csrf = CSRFProtect(app)
csrf.init_app(app) # Инициализация CSRF-защиты

# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        print("Database connection successful", "success")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}", "error")
        return False


# Фильтруем запросы к статическим ресурсам
class StaticFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith("GET /static")


class RemoveHeadersFilter(logging.Filter):
    """Фильтр для исключения заголовков запросов из логов."""
    def filter(self, record):
        return not record.getMessage().startswith("Headers:")
    
    
# Добавляем фильтр в логгер
app.logger.addFilter(RemoveHeadersFilter())
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.addFilter(StaticFilter())
werkzeug_logger.addFilter(RemoveHeadersFilter())

# Routs
@app.before_request
def log_request_info():
    app.logger.debug(f"Headers: {request.headers}")
    app.logger.debug(f"Body: {request.get_data()}")




# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    # Исключения для маршрутов, которые не требуют авторизации
    
    if request.path.startswith('/static/') or request.path.startswith('/_debug_toolbar/'):
        return None
    
    if request.endpoint in [
        "security.login", "security.logout", "security.register", 
        "security.forgot_password", "security.reset_password", "security.change_password"
    ]:
        return None
        
    # Проверяем, установлена ли сессия пользователя и находится ли он на странице, требующей профиля
    if current_user.is_authenticated:  # Убедимся, что пользователь вошел в систему
        user_profiles = UserProfile.get_user_profiles(current_user.id)
        if user_profiles:
            if 'profile_id' in session:
                g.current_profile = UserProfile.find_by_id(session['profile_id'])
                
                # Если профиль не найден или не принадлежит текущему пользователю, удаляем его из сессии
                if not g.current_profile or g.current_profile.user_id != current_user.id:
                    session.pop('profile_id', None)
                    g.current_profile = None
            else:
                # Проверяем, если у пользователя только один профиль
                if user_profiles[0] == "Default":
                    render_template("welcome_page.html",
                                    title="Welcome",
                                    menu=[])
                    
                if len(user_profiles) == 1:
                    g.current_profile = user_profiles[0]
                    session['profile_id'] = g.current_profile.id
                    return redirect(url_for("working_with_reports.choosing_report"))
                elif len(user_profiles) > 1:
                    g.current_profile = user_profiles[0]
                else:
                    g.current_profile = None
        else:
            # Если у юзера нет профиля то создаю ему дефолтный профиль загружаю 
            # этот профиль в сессию и перекидываю его на главную страницу в противном 
            # случае отправляю его на страницу ошибки
            user_first_profile = UserProfile.create(current_user.id, profile_name="Default") 
            session["profile_id"] = user_first_profile.id
            if not "profile_id" in session:
                return redirect(url_for("error"))
            
            return redirect(url_for("index"))
        # Меню обновляется на основе текущего профиля
        app.config['MENU'] = Config.get_menu()

    else:
        print("Все давай до свидания")
        return None


@app.route("/", methods=['POST', 'GET'])
@auth_required()
def index():
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    menu = app.config["MENU"]
    
    
    
    # Если у пользователя нет профиля в сессии, проверим количество профилей
    if 'profile_id' not in session:
        if user_profiles[0].profile_name == "Default":
                session['profile_id'] = user_profiles[0].id
                print("Зашел в блок default на главной странице")
                return redirect(url_for("welcome_page"))
        if len(user_profiles) == 1:
            session['profile_id'] = user_profiles[0].id
            return redirect(url_for("working_with_reports.choosing_report"))
        elif len(user_profiles) > 1:
            pass
        
    
    return render_template('index.html', 
                           title="Radiologary", 
                           menu=menu,
                           user_profiles=user_profiles,
                           version=version
                           )



@app.route("/welcome_page", methods=["GET"])
def welcome_page():
    print("welcome page started")
    menu = []
    return render_template("welcome_page.html",
                           menu=menu,
                           title="Welcome")


@app.route("/error", methods=["POST", "GET"])
def error():
    message = request.args.get("message") or "no message"
    return render_template("error.html",
                           message=message)


# Это обязательная часть для разрыва сессии базы данных после каждого обращения
@app.teardown_appcontext 
def close_db(error):
    db.session.remove()


if __name__ == "__main__":
    # Если приложение запущено не в режиме продакшена (например, локальная разработка), запускаем Flask встроенным сервером
    if os.getenv("FLASK_ENV") == "local":
        app.debug = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension(app)
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))
        
        

