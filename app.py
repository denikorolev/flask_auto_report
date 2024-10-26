# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g, jsonify
from flask_login import LoginManager, login_required, current_user
from config import get_config, Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User, UserProfile, Paragraph
import os
import logging

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

version = "0.6.0"

app = Flask(__name__)
app.config.from_object(get_config()) # Load configuration from file config.py

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(working_with_reports_bp, url_prefix="/working_with_reports")
app.register_blueprint(my_reports_bp, url_prefix="/my_reports")
app.register_blueprint(report_settings_bp, url_prefix="/report_settings")
app.register_blueprint(editing_report_bp, url_prefix="/editing_report")
app.register_blueprint(new_report_creation_bp, url_prefix="/new_report_creation")
app.register_blueprint(profile_settings_bp, url_prefix="/profile_settings")
app.register_blueprint(openai_api_bp, url_prefix="/openai_api")
app.register_blueprint(key_words_bp, url_prefix="/key_words")
app.register_blueprint(admin_bp, url_prefix="/admin")

# Load user callback 
@login_manager.user_loader
def load_user(user_id):
    with db.session() as session:
        return session.get(User, int(user_id))



# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        print("Database connection successful", "success")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}", "error")
        return False

def test_befor_request(message):
    try:
        us = current_user.user_name or "noname"
    except Exception as e:
        us = f"no user: {e}"
    try:
        pr = g.current_profile.profile_name or "noprofile"
    except Exception as e:
        pr = f"error: {e}"
    print(f"{message}:  {us} and {pr}")





# Routs

# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    if request.path.startswith('/static/') or request.path.startswith('/auth/'):
        return None
    print(f"Меня вызвал запрос:   {request.method} {request.url}")
    if request.endpoint not in ["profile_settings.update_profile_settings", "auth.loguot", "auth.login", "auth.signup"]:
        
        # Проверяем, установлена ли сессия пользователя и находится ли он на странице, требующей профиля
        if current_user.is_authenticated:  # Убедимся, что пользователь вошел в систему
            user_profiles = UserProfile.get_user_profiles(current_user.id)
            
            if 'profile_id' in session:
                g.current_profile = UserProfile.find_by_id(session['profile_id'])
                
                test_befor_request("Просто загрузил профиль в g ")
                # Если профиль не найден или не принадлежит текущему пользователю, удаляем его из сессии
                if not g.current_profile or g.current_profile.user_id != current_user.id:
                    session.pop('profile_id', None)
                    g.current_profile = None
                    test_befor_request("ОШИБКА ")
            else:
                # Проверяем, если у пользователя только один профиль
                if user_profiles[0] == "Default":
                    test_befor_request("Загрузился в ветку Default ")
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
            test_befor_request("и доехал до конца функции ")

        else:
            app.config['MENU'] = []


@app.route("/", methods=['POST', 'GET'])
@login_required
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
                           version=version)

# Новый маршрут для создания профиля
@app.route("/create_profile", methods=['POST', 'GET'])
@login_required
def create_profile():
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
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # Если приложение запущено не в режиме продакшена (например, локальная разработка), запускаем Flask встроенным сервером
    if os.getenv("FLASK_ENV") == "local":
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))
        

