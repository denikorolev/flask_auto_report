# app.py

from flask import Flask, redirect, url_for, flash, render_template, request, session, g
from flask_login import LoginManager, login_required, current_user
from config import get_config, Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User, UserProfile, ReportParagraph
import os
import logging

# Импортирую блюпринты
from working_with_reports import working_with_reports_bp  
from my_reports import my_reports_bp 
from report_settings import report_settings_bp  
from new_report_creation import new_report_creation_bp
from editing_report import editing_report_bp
from profile_settings import profile_settings_bp

version = "0.3.6"

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

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    with db.session() as session:
        return session.get(User, int(user_id))



# Functions 


def test_db_connection():
    try:
        db.engine.connect()
        flash("Database connection successful", "success")
        return True
    except Exception as e:
        flash(f"Database connection failed: {e}", "error")
        return False


def set_title_paragraph_false_for_all():
    """Обновляет поле title_paragraph на False для всех параграфов, где оно не заполнено или имеет некорректное значение."""
    try:
        # Запрашиваем только те параграфы, у которых title_paragraph равно None или имеет некорректное значение
        paragraphs = ReportParagraph.query.filter(
            (ReportParagraph.title_paragraph.is_(None)) | 
            (ReportParagraph.title_paragraph.notin_([True, False]))
        ).all()

        # Проверяем, есть ли такие параграфы
        if paragraphs:
            # Обновляем поле title_paragraph на False для отфильтрованных параграфов
            for paragraph in paragraphs:
                paragraph.title_paragraph = False

            # Сохраняем изменения в базе данных
            db.session.commit()
            print("Successfully updated title_paragraph for relevant paragraphs.")
        else:
            print("No paragraphs found that require updating.")
            
    except Exception as e:
        db.session.rollback()
        print(f"Failed to update title_paragraph: {e}")


def update_bold_paragraph_flags():
    """Обновляет поле bold_paragraph на False для всех параграфов, где оно не заполнено или имеет некорректное значение."""
    try:
        # Запрашиваем параграфы, у которых поле bold_paragraph равно None или имеет некорректное значение
        paragraphs = ReportParagraph.query.filter(
            (ReportParagraph.bold_paragraph.is_(None)) | 
            (ReportParagraph.bold_paragraph.notin_([True, False]))
        ).all()

        # Проверяем, есть ли такие параграфы
        if paragraphs:
            # Обновляем поле bold_paragraph на False для отфильтрованных параграфов
            for paragraph in paragraphs:
                paragraph.bold_paragraph = False

            # Сохраняем изменения в базе данных
            db.session.commit()
            print("Successfully updated bold_paragraph for relevant paragraphs.")
        else:
            print("No paragraphs found that require updating bold_paragraph.")
            
    except Exception as e:
        db.session.rollback()
        print(f"Failed to update bold_paragraph: {e}")


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
            flash('Please select a profile before proceeding.', 'warning')
            return redirect(url_for('create_profile'))
        app.config['MENU'] = Config.get_menu()
    else:
        # Если пользователь не авторизован, очищаем меню
        app.config['MENU'] = []

@app.route("/", methods=['POST', 'GET'])
@login_required
def index():
    menu = app.config['MENU']
    # Проверяем подключение к базе данных
    if not test_db_connection():
        return "Database connection failed", 500
    
    set_title_paragraph_false_for_all()
    update_bold_paragraph_flags()
    
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
    return redirect(url_for("working_with_reports.choosing_report"))


# Маршрут для удаления профиля
@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
@login_required
def delete_profile(profile_id):
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        db.session.delete(profile)
        db.session.commit()
        flash('Profile deleted successfully!', 'success')
    else:
        flash('Profile not found or you do not have permission to delete it.', 'danger')

    return redirect(url_for('index'))



            


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

