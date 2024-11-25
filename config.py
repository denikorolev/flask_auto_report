# config.py
# Все переменные настроек пользователя сохранены в базе данных в 
# таблице app_config их можно добавлять через AppConfig класс в models.py

from flask import url_for, session, g, current_app
from flask_login import current_user
import os
from dotenv import load_dotenv
from models import *

load_dotenv()

class Config:
    """Базовая конфигурация, общая для всех сред"""
    
    # Словарь сопоставления имен таблиц с классами моделей нужна для панели Admin
    TABLE_MODELS = {
        "AppConfig": AppConfig,
        "User": User,
        "UserProfile": UserProfile,
        "ReportType": ReportType,
        "ReportSubtype": ReportSubtype,
        "Report": Report,
        "Paragraph": Paragraph,
        "Sentence": Sentence,
        "KeyWord": KeyWord,
        "ParagraphType": ParagraphType,
        "FileMetadata": FileMetadata,
    }
    
    # Flask-Security Configuration
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "$$1")
    SECURITY_PASSWORD_HASH = "scrypt"  # Алгоритм хэширования паролей
    SECURITY_REGISTERABLE = True       # Разрешить регистрацию
    SECURITY_CONFIRMABLE = True        # Требовать подтверждения email
    SECURITY_RECOVERABLE = True        # Включить восстановление пароля
    SECURITY_TRACKABLE = True          # Включить отслеживание входов
    SECURITY_CHANGEABLE = True         # Включить изменение пароля
    SECURITY_POST_LOGIN_VIEW = "/"  # URL после успешного входа
    SECURITY_POST_LOGOUT_VIEW = "/auth/login"         # URL после выхода
    
    
    
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/uploads")
    
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
    OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")
    OPENAI_ASSISTANT = os.getenv("OPENAI_ASSISTANT")
    
    # Menu configuration
    @staticmethod
    def get_menu():
        """Формирует меню с учетом текущего профиля"""
        menu = [
            {"name": "Главная", "url": url_for("index")},
            {"name": "Протокол", "url": url_for("working_with_reports.choosing_report")},
            {"name": "Список протоколов", "url": url_for("my_reports.reports_list")},
            {"name": "Новый протокол", "url": url_for("new_report_creation.create_report")},
            {"name": "Настройки", "url": url_for("report_settings.report_settings")},
            {"name": "API", "url":url_for("openai_api.start_openai_api")},
            {"name": "Ключевые слова", "url":url_for("key_words.key_words")},
            {"name": "admin", "url":url_for("admin.admin")}
        ]
        
        # Добавляем настройки профиля, если профиль выбран
        if g.current_profile:
            menu.append({
                "name": "Настройки профиля",
                "url": url_for("profile_settings.profile_settings", profile_id=g.current_profile.id)
            })
        
        return menu


    @staticmethod
    def load_user_config(user_id):
        """
        Load user-specific configuration from the database.
        """
        return None
    
    @staticmethod
    def get_user_upload_folder():
        """
        Создаёт путь к папке для загрузок пользователя в формате: <первая_часть_email>_<user_id>/profile_<profile_id>.
        Если папка не существует, она будет создана.
        """
        user_email = current_user.email
        user_id = current_user.id
        # Извлекаем первую часть email (до @)
        email_prefix = user_email.split('@')[0]
        # Путь к папке пользователя
        user_folder = os.path.join(current_app.config['BASE_UPLOAD_FOLDER'], f"{email_prefix}_{user_id}")
        
        # Получаем текущий профиль пользователя
        if not g.current_profile:
            raise Exception("Profile is not selected.")
        
        profile_id = g.current_profile.id
        profile_folder = os.path.join(user_folder, f"profile_{profile_id}")
        
        # Создание папки пользователя, если её нет
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            
        # Создание папки профиля, если её нет
        if not os.path.exists(profile_folder):
            os.makedirs(profile_folder)
        
        return profile_folder
    
    @classmethod
    def init_db_uri(cls, db_user, db_pass, db_host, db_port, db_name):
        """Инициализация строки подключения к базе данных"""
        if db_pass:
            return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
        
        
class DevelopmentConfig(Config):
    """Конфигурация для локальной разработки"""
    DB_HOST = os.getenv("DB_HOST", "localhost")  # По умолчанию подключение к localhost
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS", "")
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER_TEST")
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
        

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DB_HOST = os.getenv("DB_HOST", "db")  # Используем Docker сервис "db"
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS", "")
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)


class TestingConfig(Config):
    """Конфигурация для тестовой среды"""
    DB_HOST = os.getenv("DB_HOST_TEST", "db_test")  # Используем Docker сервис "db_test"
    DB_PORT = os.getenv("DB_PORT_TEST", "5433")
    DB_NAME = os.getenv("DB_NAME_TEST")
    DB_USER = os.getenv("DB_USER_TEST")
    DB_PASS = os.getenv("DB_PASS_TEST", "")
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER_TEST")
    
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)


def get_config():
    """Функция для выбора конфигурации в зависимости от переменной FLASK_ENV"""
    flask_env = os.getenv("FLASK_ENV", "local")
    
    if flask_env == "production":
        return ProductionConfig
    elif flask_env == "testing":
        return TestingConfig
    else:
        return DevelopmentConfig  # По умолчанию DevelopmentConfig для локальной разработки