# config.py
#v0.2.0
# Все переменные настроек пользователя сохранены в базе данных в 
# таблице app_config их можно добавлять через AppConfig класс в models.py

from flask_login import current_user
import os
from dotenv import load_dotenv
from models import AppConfig

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST")
    PORT = os.getenv("PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "my_secret_key")

    # Если пароль не задан, разрешить подключение без пароля для теста
    if DB_PASS:
        SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{PORT}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}@{DB_HOST}:{PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Основная папка uploads 
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    
    # Menu configuration
    MENU = [
        {"name": "main", "url": "main"},
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