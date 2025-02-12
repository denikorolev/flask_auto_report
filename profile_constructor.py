# profile_constructor.py

from flask import current_app, g, session
import json
from models import AppConfig
from logger import logger


class ProfileSettingsManager:
    """
    Класс для управления настройками профиля.
    """
    @staticmethod
    def load_profile_settings():
        """
        Загружает настройки для указанного профиля из таблицы AppConfig в current_app.config.
        """
        
        try:
            profile = getattr(g, "current_profile", None)
            profile_id = profile.id if profile else session.get("profile_id") or None
            if profile_id:
                settings = AppConfig.query.filter_by(profile_id=profile_id).all()
                profile_settings = {setting.config_key: ProfileSettingsManager._parse_value(setting) for setting in settings}
                # Сохраняем все настройки в app.config под ключом PROFILE_SETTINGS
                current_app.config["PROFILE_SETTINGS"] = profile_settings
                
                if not profile_settings:
                    logger.warning(f"No settings found for profile_id={profile_id}. Using default settings.")
                    profile_settings = current_app.config.get("DEFAULT_PROFILE_SETTINGS", {})
                    current_app.config["PROFILE_SETTINGS"] = profile_settings
                    
                return profile_settings
                
        except Exception as e:
            logger.error(f"Error loading settings for profile_id={profile_id}: {str(e)}")
        logger.warning("No profile settings loaded. Using empty dict.")
        return {}

    @staticmethod
    def _parse_value(setting):
        """
        Конвертирует значение настройки в правильный тип, основываясь на config_type.
        """
        if setting.config_type == "boolean":
            return setting.config_value.lower() == "true"
        elif setting.config_type == "integer":
            return int(setting.config_value)
        elif setting.config_type == "float":
            return float(setting.config_value)
        elif setting.config_type == "json":
            return json.loads(setting.config_value)
        elif setting.config_type == "string" or setting.config_type is None:
            return setting.config_value  # Если тип строки или отсутствует
        else:
            raise ValueError(f"Unknown config_type: {setting.config_type}")

    # Пока нигде не используется
    @staticmethod
    def get_profile_setting(key, default=None):
        """
        Возвращает значение настройки профиля по ключу из app.config["PROFILE_SETTINGS"].
        """
        profile_settings = current_app.config.get("PROFILE_SETTINGS", {})
        return profile_settings.get(key, default)
