# app.__init__.py

from flask import Flask
import os
import logging

from flask_security import SQLAlchemyUserDatastore
from .extensions import db, migrate, csrf, security as security_ext

# Мои модули
from .handlers.error import register_error_handlers
from .models.models import User, Role
from .utils.mail_helpers import CustomMailUtil, ExtendedRegisterForm
from .before_request_handlers import load_current_profile, one_time_sync_tasks
from .security.signals import init_security_signals


from .context_processors import (
        inject_menu,
        inject_user_settings,
        inject_app_info,
        inject_user_rank,
        inject_current_profile_data,
    )

from tasks.make_celery import make_celery
from config import get_config


from .blueprints.working_with_reports import working_with_reports_bp  
from .blueprints.my_reports import my_reports_bp 
from .blueprints.new_report_creation import new_report_creation_bp
from .blueprints.editing_report import editing_report_bp
from .blueprints.profile_settings import profile_settings_bp
from .blueprints.openai_api import openai_api_bp
from .blueprints.key_words import key_words_bp
from .blueprints.admin import admin_bp
from .blueprints.support import support_bp
from .blueprints.main import main_bp
from .blueprints.tasks_status import tasks_status_bp
from .blueprints.snapshorts import snapshots_bp



def close_db(exception=None):
    db.session.remove()

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())  

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
   
    celery = make_celery(app)
    app.celery = celery  
    
    # Инициализирую Flask-security-too
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security_ext.init_app(app, user_datastore, mail_util_cls=CustomMailUtil, register_form=ExtendedRegisterForm)
    init_security_signals(app)
    
    register_error_handlers(app)
    
    
    app.before_request(load_current_profile)
    app.before_request(one_time_sync_tasks)


    # Регистрация контекстных процессоров
    app.context_processor(inject_menu)
    app.context_processor(inject_user_settings)
    app.context_processor(inject_user_rank)
    app.context_processor(inject_current_profile_data)
    # Для inject_app_info — нужно передать версию
    app.context_processor(inject_app_info("0.10.7.9"))
    
   
    # Register Blueprints
    app.register_blueprint(working_with_reports_bp, url_prefix="/working_with_reports")
    app.register_blueprint(my_reports_bp, url_prefix="/my_reports")
    app.register_blueprint(editing_report_bp, url_prefix="/editing_report")
    app.register_blueprint(new_report_creation_bp, url_prefix="/new_report_creation")
    app.register_blueprint(profile_settings_bp, url_prefix="/profile_settings")
    app.register_blueprint(openai_api_bp, url_prefix="/openai_api")
    app.register_blueprint(key_words_bp, url_prefix="/key_words")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(tasks_status_bp, url_prefix="/tasks_status")
    app.register_blueprint(support_bp, url_prefix="/support")
    app.register_blueprint(main_bp, url_prefix="/")
    app.register_blueprint(snapshots_bp, url_prefix="/snapshots")
    
    
    app.teardown_appcontext(close_db)
    
    
    # DEBUG TOOLBAR (только локально)
    if os.getenv("FLASK_ENV") == "local":
        from flask_debugtoolbar import DebugToolbarExtension
        class StaticFilter(logging.Filter):
            def filter(self, record):
                return not record.getMessage().startswith("GET /static/")
        app.debug = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension(app)
        # Применить фильтр к логгеру если надо
        for handler in logging.getLogger('werkzeug').handlers:
            handler.addFilter(StaticFilter())
    
    return app