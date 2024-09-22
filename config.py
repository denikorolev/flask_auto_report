# config.py
#v0.2.1
# Все переменные настроек пользователя сохранены в базе данных в 
# таблице app_config их можно добавлять через AppConfig класс в models.py

from flask_login import current_user
import os
from dotenv import load_dotenv
from models import AppConfig

load_dotenv()

class Config:
    """Базовая конфигурация, общая для всех сред"""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Основная папка uploads 
    
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    
    # Menu configuration
    MENU = [
        {"name": "main", "url": "index"},
        {"name": "report", "url": "working_with_reports.choosing_report"},
        {"name": "my reports", "url": "my_reports.reports_list"},
        {"name": "new report", "url": "new_report_creation.create_report"},
        {"name": "settings", "url": "report_settings.report_settings"}
    ]

    @staticmethod
    def load_user_config(user_id):
        """
        Load user-specific configuration from the database.
        """
        return None
    
    @staticmethod
    def get_user_upload_folder():
        """
        Создаёт путь к папке для загрузок пользователя в формате: <первая_часть_email>_<user_id>.
        Если папка не существует, она будет создана.
        """
        user_email = current_user.user_email
        user_id = current_user.id
        # Извлекаем первую часть email (до @)
        email_prefix = user_email.split('@')[0]
        # Путь к папке пользователя
        user_folder = os.path.join(Config.BASE_UPLOAD_FOLDER, f"{email_prefix}_{user_id}")
        # Создание папки, если её нет
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        return user_folder
    
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
    
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
        

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DB_HOST = os.getenv("DB_HOST", "db")  # Используем Docker сервис "db"
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS", "")
    
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)


class TestingConfig(Config):
    """Конфигурация для тестовой среды"""
    DB_HOST = os.getenv("DB_HOST_TEST", "db_test")  # Используем Docker сервис "db_test"
    DB_PORT = os.getenv("DB_PORT_TEST", "5433")
    DB_NAME = os.getenv("DB_NAME_TEST")
    DB_USER = os.getenv("DB_USER_TEST")
    DB_PASS = os.getenv("DB_PASS_TEST", "")
    
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