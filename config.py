# config.py
# Все переменные настроек пользователя сохранены в базе данных в 
# таблице app_config их можно добавлять через AppConfig класс в models.py

from flask import url_for, session, g, current_app
from flask_login import current_user
import os
from dotenv import load_dotenv
from models import *
import logging

load_dotenv()




class Config:
    """Базовая конфигурация, общая для всех сред"""
    
    # Словарь сопоставления имен таблиц с классами моделей нужна для панели Admin
    TABLE_MODELS = {
        "AppConfig": AppConfig,
        "Role": Role,
        "User": User,
        "UserProfile": UserProfile,
        "ReportType": ReportType,
        "ReportSubtype": ReportSubtype,
        "Report": Report,
        "Paragraph": Paragraph,
        "HeadSentence": HeadSentence,
        "BodySentence": BodySentence,
        "TailSentence": TailSentence,
        "TailSentenceGroup": TailSentenceGroup,
        "BodySentenceGroup": BodySentenceGroup,
        "HeadSentenceGroup": HeadSentenceGroup,
        "KeyWord": KeyWord,
        "FileMetadata": FileMetadata,
        "ReportTextSnapshot": ReportTextSnapshot
    }
    
    ASSOCIATIVE_TABLES = [
        "key_word_report_link",
        "roles_users",
        "head_sentence_group_link",
        "tail_sentence_group_link",
        "body_sentence_group_link"
    ]
    
    # Flask-Security Configuration
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "$$1")
    SECURITY_PASSWORD_HASH = "bcrypt"  # Алгоритм хэширования паролей
    SECURITY_REGISTERABLE = True       # Разрешить регистрацию
    
    SECURITY_CONFIRMABLE = True        # Требовать подтверждения email
    SECURITY_SEND_REGISTER_EMAIL = True
    SECURITY_CONFIRM_EMAIL_WITHIN = '5 days'  # Срок действия ссылки
    
    SECURITY_USERNAME_ENABLE = False  # Разрешить вход по имени пользователя
    SECURITY_USERNAME_REQUIRED = False  # Требовать имя пользователя при регистрации
    SECURITY_PASSWORD_CONFIRM_REQUIRED = False  # Не требовать подтверждение пароля при регистрации
    SECURITY_RECOVERABLE = True        # Включить восстановление пароля
    SECURITY_TRACKABLE = True          # Включить отслеживание входов
    SECURITY_CHANGEABLE = True    
    SECURITY_CHANGE_EMAIL = True  # Разрешить изменение email
    SECURITY_SEND_CONFIRM_EMAIL = True  # Отправлять email для подтверждения
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = True  # Отправлять email при изменении пароля
    SECURITY_SEND_PASSWORD_RESET_EMAIL = True  # Отправлять email при сбросе пароля
    SECURITY_POST_LOGIN_VIEW = "/working_with_reports/choosing_report"  # URL после успешного входа
    SECURITY_POST_LOGOUT_VIEW = "/" # URL после выхода
    SECURITY_POST_REGISTER_VIEW = "/support/success_registered"
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 7  # Продолжительность в секундах (7 дней)
    REMEMBER_COOKIE_HTTPONLY = True          # Безопасность cookie
    SECURITY_REMEMBER_ME = True              # Включить "запомнить меня"# URL после выхода
    SECURITY_CSRF_PROTECT = True           # Отключает проверку CSRF
    WTF_CSRF_ENABLED = True  # Включить CSRF для Flask-WTF
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY")
    WTF_CSRF_TIME_LIMIT = 3600 * 12 # Время жизни токена (опционально)
    SECURITY_LOG_LEVEL = logging.DEBUG   # Включение логирования Flask-Security
    SECURITY_FLASH_MESSAGES = False # Отключает всплывающие сообщения Flask-Security
    SECURITY_RETURN_GENERIC_RESPONSES = False
    SECURITY_AUTO_LOGIN_AFTER_CONFIRM = True  # Автоматический вход после подтверждения email
    SECURITY_EMAIL_SUBJECT_REGISTER = "Добро пожаловать в Radiologary"
    SECURITY_EMAIL_SUBJECT_CONFIRM = "Пожалуйста подтвердите ваш email"
    SECURITY_CHANGE_EMAIL_SUBJECT = "Подтверждение изменения email"
    SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = "Пароль успешно изменён"
    SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = "Сброс пароля Radiologary"
    
    
    
    
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Отключает события SQLAlchemy что бережет память и избавляет от сообщения об ошибках в терминале.
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/uploads")
    SESSION_TYPE = "filesystem"
    ZEPTOMAIL_API_TOKEN = os.getenv("ZEPTOMAIL_API_TOKEN")
    NOREPLY_EMAIL = "noreply@radiologary.com"
    SUPPORT_EMAIL = "support@radiologary.com"
    CEO_EMAIL = "korolev.denis@radiologary.com"


    REPORT_TYPES_DEFAULT_RU = ["МРТ", "КТ", "Рентгенография", "ПЭТ-КТ", "Сцинтиграфия", "УЗИ"]
    REPORT_SUBTYPES_DEFAULT_RU = ["Голова и шея", "Органы грудной клетки", "Органы брюшной полости", "Органы малого таза", "Верхние конечности", "Нижние конечности", "Позвоночник", "Сердечно-сосудистая система", "Опорно-двигательный аппарат", "Мягкие ткани", "Суставы", "Комбинированные протоколы", "Педиатрия", "Прочее" ]
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
    OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")
    OPENAI_ASSISTANT_MRI = os.getenv("OPENAI_ASSISTANT_MRI")
    OPENAI_ASSISTANT_CT = os.getenv("OPENAI_ASSISTANT_CT")
    OPENAI_ASSISTANT_XRAY = os.getenv("OPENAI_ASSISTANT_XRAY")
    OPENAI_ASSISTANT_GENERAL = os.getenv("OPENAI_ASSISTANT_GENERAL")
    OPENAI_ASSISTANT_REDACTOR = os.getenv("OPENAI_ASSISTANT_REDACTOR")
    OPENAI_ASSISTANT_GRAMMA_CORRECTOR_RU = os.getenv("OPENAI_ASSISTANT_GRAMMA_CORRECTOR_RU")
    OPENAI_ASSISTANT_DYNAMIC_STRUCTURER = os.getenv("OPENAI_ASSISTANT_DYNAMIC_STRUCTURER")
    OPENAI_ASSISTANT_TEXT_CLEANER = os.getenv("OPENAI_ASSISTANT_TEXT_CLEANER")
    OPENAI_ASSISTANT_FIRST_LOOK_RADIOLOGIST = os.getenv("OPENAI_ASSISTANT_FIRST_LOOK_RADIOLOGIST")
    OPENAI_ASSISTANT_TEMPLATE_MAKER = os.getenv("OPENAI_ASSISTANT_TEMPLATE_MAKER")  # Новый ассистент для создания шаблонов
    
    # Дефолтные настройки для профиля
    DEFAULT_PROFILE_SETTINGS = {"USE_WORD_REPORTS": False,
                                "USE_SENTENCE_AUTOSAVE": True,
                                "USE_SENTENCE_AUTOSAVE_FOR_DYNAMIC_REPORT": False,
                                "APP_LANGUAGE": "ru",
                                "APP_THEME": "light",
                                "SIMILARITY_THRESHOLD_FUZZ": 95,
                                "EXCEPT_WORDS": ["мм", "см"],
                                "EXCEPTIONS_AFTER_PUNCTUATION": ["МРТ", "КТ", "УЗИ", "РКТ", "ПЭТ", "ПЭТ-КТ", "МСКТ", "РГ", "ЭКГ", "ФГДС"],
                                "USE_SENTENCE_AI_CHECK_DEFAULT": True,
                                "USE_FIRST_GRAMMA_SENTENCE_DEFAULT": True,
                                "USE_DUBLICATE_SEARCH_DEFAULT": True,
                                }
    
    @staticmethod
    def get_user_upload_folder(user_id, profile_id, user_email):
        """
        Создаёт путь к папке для загрузок пользователя в формате: <первая_часть_email>_<user_id>/profile_<profile_id>.
        Если папка не существует, она будет создана.
        """
        # Извлекаем первую часть email (до @)
        email_prefix = user_email.split('@')[0]
        # Путь к папке пользователя
        user_folder = os.path.join(current_app.config['BASE_UPLOAD_FOLDER'], f"{email_prefix}_{user_id}")
        
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
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")  # URL брокера сообщений
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")  # URL для хранения результатов задач
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  
    REDIS_PORT = os.getenv("REDIS_PORT", "6379") 

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DB_HOST = os.getenv("DB_HOST", "db")  
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS", "")
    BASE_UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    
    SQLALCHEMY_DATABASE_URI = Config.init_db_uri(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")  # URL брокера сообщений
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")  # URL для хранения результатов задач
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")  
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")  


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