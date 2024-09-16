# app.py
#v0.2.0

from flask import Flask, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_required, user_logged_in
from config import Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User
from werkzeug.utils import secure_filename
from working_with_reports import working_with_reports_bp  
from my_reports import my_reports_bp 
from report_settings import report_settings_bp  
from new_report_creation import new_report_creation_bp
from editing_report import editing_report_bp

app = Flask(__name__)
app.config.from_object(Config) # Load configuration from file config.py

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

# Handle user logged in event
@user_logged_in.connect_via(app)
def on_user_logged_in(sender, user):
    user_config = Config.load_user_config(user.id)
    for key, value in user_config.items():
        if value:
            app.config[key] = value
            

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


# This is only for redirection to the main page
@app.route("/")
def index():
    if not test_db_connection():
        return "Database connection failed", 500
    return redirect(url_for("main"))

# This is the main page

@app.route('/main', methods=['POST', 'GET'])
@login_required
def main():
    test_db_connection()
    return render_template('index.html', title="Main page Radiologary", menu=menu)



@app.teardown_appcontext # I need to figure out how it works
def close_db(error):
    db.session.remove()



# if __name__ == "__main__":
#     app.run(debug=True, port=5001)
