# app.py

from flask import Flask, redirect, url_for, render_template, request, session, g
from flask_login import LoginManager, login_required, current_user
from config import get_config, Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User, UserProfile
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

version = "0.5.3"

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


# Routs

# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    # Проверяем, установлена ли сессия пользователя и находится ли он на странице, требующей профиля
    if current_user.is_authenticated:  # Убедимся, что пользователь вошел в систему
        if 'profile_id' in session:
            # Устанавливаем текущий профиль
            g.current_profile = UserProfile.find_by_id(session['profile_id'])
            
            if not g.current_profile or g.current_profile.user_id != current_user.id:
                # Если профиль не найден или не принадлежит текущему пользователю, удаляем его из сессии
                session.pop('profile_id', None)
                g.current_profile = None
        else:
            g.current_profile = None
        
        # Если профиль отсутствует, но пользователь аутентифицирован, и запрос не относится к выбору профиля, перенаправляем
        if not g.current_profile and request.endpoint not in ['create_profile', 'set_profile', 'index', 'auth.logout']:
            print('Please select a profile before proceeding.', 'warning')
            return redirect(url_for('create_profile'))
        app.config['MENU'] = Config.get_menu()
    else:
        # Если пользователь не авторизован, очищаем меню
        app.config['MENU'] = []

@app.route("/", methods=['POST', 'GET'])
@login_required
def index():
    # Проверяем подключение к базе данных
    if not test_db_connection():
        print("db wasn't connected")
        return redirect(url_for("error", message="db wasn't connected"))
    
    if not "profile_id" in session:
        user_profiles = UserProfile.get_user_profiles(current_user.id)
        
        if not user_profiles:
            UserProfile.create(current_user.id, "Default", "Default")
            profile = UserProfile.get_user_profiles(current_user.id)[0]
            if profile:
                session['profile_id'] = profile.id
                return render_template("welcome_page.html",
                                       title="welcome in radiologary",
                                       user=current_user.name,
                                       profile=profile)
            else:
                print("samething goes wrong with profiles of new user")
                return redirect(url_for("error", message="samething goes wrong with profiles of new user"))
        
        if len(user_profiles) == 1:
            print("there is only one profile")
            profile = user_profiles[0]
            if profile:
                session['profile_id'] = profile.id
                return redirect("/")
            else:
                print("samething goes wrong with profiles of seassoned user with only one profile")
                return redirect(url_for("error", message="samething goes wrong with profiles of seassoned user with only one profile"))
        
        if len(user_profiles)>1:
            print("here will be logic for check and choose default profile or show profiles list")
            profile = user_profiles[0]
            if profile:
                session['profile_id'] = profile.id
                return redirect("/")
            else:
                print("samething goes wrong with profiles of seassoned user with only one profile")
                return redirect(url_for("error", message="samething goes wrong with profiles of seassoned user with only one profile"))
    
    menu = app.config['MENU']
    
    if 'profile_id' in session:
        # Проверяем, принадлежит ли профиль текущему пользователю
        profile = UserProfile.query.filter_by(id=session['profile_id'], user_id=current_user.id).first()
        if profile:
            g.current_profile = profile
        else:
            # Если профиль не найден или не принадлежит текущему пользователю, очищаем сессию
            session.pop('profile_id', None)
            g.current_profile = None
    # Проверяем, есть ли у пользователя профиль
    
    
        
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
    if request.method == 'POST':
        profile_name = request.form.get('profile_name')
        description = request.form.get('description')

        if profile_name:
            # Создаем профиль пользователя
            UserProfile.create(current_user.id, profile_name, description)
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


@app.route("/error", methods=["POST", "GET"])
def error():
    message = request.args.get("message")
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
        

