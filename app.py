# app.py

from flask import Flask, redirect, url_for, flash, render_template, request, session, g
from flask_login import LoginManager, login_required, current_user
from config import get_config
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

version = "0.3.1"

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

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    with db.session() as session:
        return session.get(User, int(user_id))

# Use menu from config
menu = app.config['MENU']

# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        flash("Database connection successful", "success")
        return True
    except Exception as e:
        flash(f"Database connection failed: {e}", "error")
        return False


@app.route("/", methods=['POST', 'GET'])
@login_required
def index():
    # Проверяем подключение к базе данных
    if not test_db_connection():
        return "Database connection failed", 500
    
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
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    
    if not user_profiles:
        flash("You do not have a profile. Please create one.", "warning")
        
    return render_template('index.html', 
                           title="Main page Radiologary", 
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
            flash("Profile created successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Profile name is required.", "danger")

    return render_template('create_profile.html', title="Create Profile")

# Логика для того чтобы установить выбранный профайл
@app.route("/set_profile/<int:profile_id>")
@login_required
def set_profile(profile_id):
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        session['profile_id'] = profile.id
        flash(f"Profile '{profile.profile_name}' set as current.", "success")
    else:
        flash("Profile not found.", "danger")
    return redirect(url_for('index'))


# Логика для того, чтобы сделать данные профиля доступными в любом месте программы
@app.before_request
def load_current_profile():
    # Проверяем, установлен ли профиль в сессии
    if 'profile_id' in session:
        g.current_profile = UserProfile.find_by_id(session['profile_id'])
    else:
        # Профиль не установлен, используем None
        g.current_profile = None
            
            
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
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))  # Включаем отладку и указываем порт

