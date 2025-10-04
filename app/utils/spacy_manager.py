from flask import session
import spacy
from app.utils.logger import logger


class SpacyModel:
    """Singleton-класс для управления загрузкой и настройкой модели SpaCy."""
    
    _instance = None
    _language = None
    _custom_model_path = None

    @classmethod
    def set_custom_model(cls, path):
        """Задаёт путь к пользовательской модели"""
        cls._custom_model_path = path
        
        
        
    @classmethod
    def get_instance(cls, language=None):
        """Возвращает инстанс SpaCy модели с учётом кастомной модели только для русского языка."""
        logger.info(f"Загружаю модель SpaCy для языка: {language}")
        
        if cls._instance is not None:
            logger.info("Модель уже загружена")
            return cls._instance  # Уже загружена

        if not language:
            language = session.get("lang", "default_language")  # По умолчанию русский
        cls._language = language

        if language == "ru":
            import glob
            import os

            # Ищем кастомную модель
            models = sorted(
                glob.glob("spacy_models/custom_sentencizer_v*"),
                key=os.path.getmtime,
                reverse=True
            )

            if models:
                cls._custom_model_path = models[0]
                try:
                    cls._instance = spacy.load(cls._custom_model_path)
                    logger.info(f"Использую кастомную модель: {cls._custom_model_path}")
                    return cls._instance
                except Exception as e:
                    # В логах или на экране можно будет увидеть, если кастомная модель битая
                    logger.error(f"❌ Ошибка загрузки кастомной модели: {e}. Использую стандартную.")
                    pass

            # Если кастомной нет или ошибка — загружаем стандартную
            cls._instance = spacy.load("ru_core_news_sm")
            logger.info("Использую стандартную модель ru_core_news_sm")
            return cls._instance

        elif language == "eng":
            cls._instance = spacy.load("en_core_web_sm")
            return cls._instance

        else:
            raise ValueError(f"Unsupported language '{language}'. Use 'ru' or 'eng'.")




    @classmethod
    def reset(cls):
        """Сбрасывает текущую модель и язык."""
        cls._instance = None
        cls._language = None
        
    
    
    
    
