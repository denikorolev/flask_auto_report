from flask import current_app
import spacy

class SpacyModel:
    """Singleton-класс для управления загрузкой и настройкой модели SpaCy."""
    
    _instance = None
    _language = None

    @classmethod
    def get_instance(cls, language=None):
        """
        Возвращает инстанс SpaCy модели для заданного языка.
        Если модель уже загружена и язык совпадает, возвращает существующую модель.
        """
        if cls._instance is None or language != cls._language:
            if not language:
                # Получаем язык из конфигурации приложения
                language = current_app.config.get("APP_LANGUAGE", "ru")
            
            # Загрузка соответствующей модели
            if language == "ru":
                cls._instance = spacy.load("ru_core_news_sm")
            elif language == "eng":
                cls._instance = spacy.load("en_core_web_sm")
            else:
                raise ValueError(f"Unsupported language '{language}'. Use 'ru' or 'eng'.")
            
            cls._language = language

        return cls._instance

    @classmethod
    def reset(cls):
        """Сбрасывает текущую модель и язык."""
        cls._instance = None
        cls._language = None
