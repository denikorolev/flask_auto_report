# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g, jsonify
from flask_login import LoginManager, login_required, current_user, login_manager
import logging
from config import get_config, Config
from flask_migrate import Migrate
# from auth import auth_bp  
from models import db, User, UserProfile, Role
import os
import logging
import uuid
# импорты для flask security

from flask_wtf.csrf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.decorators import auth_required

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

version = "0.7.0"

app = Flask(__name__)
app.config.from_object(get_config()) # Load configuration from file config.py

# Initialize default menu
app.config['MENU'] = []

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# uuid_butt = str(uuid.uuid4())

#Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "security.login"


# Инициализирую Flask-security-too
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

logging.basicConfig(level=logging.DEBUG)  # Установите DEBUG, чтобы видеть все логи

# Register Blueprints
# app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(working_with_reports_bp, url_prefix="/working_with_reports")
app.register_blueprint(my_reports_bp, url_prefix="/my_reports")
app.register_blueprint(report_settings_bp, url_prefix="/report_settings")
app.register_blueprint(editing_report_bp, url_prefix="/editing_report")
app.register_blueprint(new_report_creation_bp, url_prefix="/new_report_creation")
app.register_blueprint(profile_settings_bp, url_prefix="/profile_settings")
app.register_blueprint(openai_api_bp, url_prefix="/openai_api")
app.register_blueprint(key_words_bp, url_prefix="/key_words")
app.register_blueprint(admin_bp, url_prefix="/admin")

#Load user callback 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Настройги логгера
# formatter = logging.Formatter(
#     "[%(asctime)s] %(levelname)s в модуле %(module)s: %(message)s"
# )

# Настраиваем основной логгер
# handler = logging.StreamHandler()  # Логи будут выводиться в консоль
# handler.setFormatter(formatter)
# logging.getLogger().addHandler(handler)
# logging.getLogger().setLevel(logging.INFO)  # Устанавливаем уровень логирования на INFO

# Обработка ошибок
@app.errorhandler(500)
def internal_error(exception):
    app.logger.error(f"500 ошибка: {exception}")
    return "Internal Server Error", 500


csrf = CSRFProtect(app)
# Отключить CSRF для всех маршрутов
# csrf._disable_on_request()
# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        print("Database connection successful", "success")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}", "error")
        return False



# Routs

# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    # Исключения для маршрутов, которые не требуют авторизации
    if request.path.startswith('/static/') or request.endpoint in [
        "security.login", "security.logout", "security.register", 
        "security.forgot_password", "security.reset_password", "security.change_password"
    ]:
        return None
        
    # Проверяем, установлена ли сессия пользователя и находится ли он на странице, требующей профиля
    if current_user.is_authenticated:  # Убедимся, что пользователь вошел в систему
        user_profiles = UserProfile.get_user_profiles(current_user.id)
        if 'profile_id' in session:
            print("Идентификатор профиля есть в сессии")
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
                
        # Меню обновляется на основе текущего профиля
        app.config['MENU'] = Config.get_menu()

    else:
        app.config['MENU'] = []


@app.route("/", methods=['POST', 'GET'])
@auth_required()
def index():
    print("я прорвался на главную страницу")
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

# Новый маршрут для создания профиля
@app.route("/create_profile", methods=['POST', 'GET'])
@login_required
def create_profile():
    print("started route 'create profile'")
    if request.method == 'POST':
        profile_name = request.form.get('profile_name')
        description = request.form.get('description')
        default_profile = False
        if profile_name:
            # Создаем профиль пользователя
            UserProfile.create(
                current_user.id, 
                profile_name, 
                description,
                default_profile=default_profile
                )
            print("Profile created successfully!", "success")
            return redirect(url_for('index'))
        else:
            print("Profile name is required.", "danger")

    return render_template('create_profile.html', title="Create Profile")


# Логика для того чтобы установить выбранный профайл
@app.route("/set_profile/<int:profile_id>")
@login_required
def set_profile(profile_id):
    print("i'm in set_profile route")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        session['profile_id'] = profile.id
        print(f"Profile '{profile.profile_name}' set as current.", "success")
    else:
        print("Profile not found.", "danger")
    return redirect(url_for("working_with_reports.choosing_report"))


# Маршрут для удаления профиля
@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
@login_required
def delete_profile(profile_id):
    print("you are deleting profile")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        db.session.delete(profile)
        db.session.commit()
        print('Profile deleted successfully!', 'success')
    else:
        print('Profile not found or you do not have permission to delete it.', 'danger')

    return redirect(url_for('index'))



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
    # Настройка логирования для вывода в stdout
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.INFO)
    
    # Если приложение запущено не в режиме продакшена (например, локальная разработка), запускаем Flask встроенным сервером
    if os.getenv("FLASK_ENV") == "local":
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))
        

