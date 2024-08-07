# config.py
# Все переменные настроек пользователя сохранены в базе данных в 
# таблице app_config их можно добавлять через AppConfig класс в models.py

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

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads') 
    
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
        upload_folder_path = AppConfig.get_config_value("UPLOAD_FOLDER_PATH", user_id)
        upload_folder_name = AppConfig.get_config_value("UPLOAD_FOLDER_NAME", user_id)
        return {
            "UPLOAD_FOLDER_PATH": upload_folder_path,
            "UPLOAD_FOLDER_NAME": upload_folder_name
        }