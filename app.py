# app.py
#v0.3.0

from flask import Flask, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_required, user_logged_in
from config import get_config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User
import os

# Импортирую блюпринты
from working_with_reports import working_with_reports_bp  
from my_reports import my_reports_bp 
from report_settings import report_settings_bp  
from new_report_creation import new_report_creation_bp
from editing_report import editing_report_bp


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
    
    # Отображаем главную страницу
    return render_template('index.html', 
                           title="Main page Radiologary", 
                           menu=menu)


@app.teardown_appcontext # I need to figure out how it works
def close_db(error):
    db.session.remove()



import os

if __name__ == "__main__":
    # Если приложение запущено не в режиме продакшена (например, локальная разработка), запускаем Flask встроенным сервером
    if os.getenv("FLASK_ENV") == "local":
        app.run(debug=True, port=int(os.getenv("PORT", 5001)))  # Включаем отладку и указываем порт

