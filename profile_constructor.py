# profile_constructor.py

from flask import current_app, g, session
import json
from models import AppConfig

class ProfileSettingsManager:
    """
    Класс для управления настройками профиля.
    """
    @staticmethod
    def load_profile_settings():
        """
        Загружает настройки для указанного профиля из таблицы AppConfig в current_app.config.
        """
        print("load_profile_settings started")
        try:
            
            profile = getattr(g, "current_profile", None)
            profile_id = profile.id if profile else session.get("profile_id") or None
            print(f"profile_id found ={profile_id}")
            
            if profile_id:
                print(f"Loading settings for profile_id={profile_id}")
                settings = AppConfig.query.filter_by(profile_id=profile_id).all()
                profile_settings = {setting.config_key: ProfileSettingsManager._parse_value(setting) for setting in settings}
                # Сохраняем все настройки в app.config под ключом PROFILE_SETTINGS
                current_app.config["PROFILE_SETTINGS"] = profile_settings
                
                if not profile_settings:
                    print("Loading default settings")
                    profile_settings = current_app.config.get("DEFAULT_PROFILE_SETTINGS", {})
                    current_app.config["PROFILE_SETTINGS"] = profile_settings
                    
                return profile_settings
                
        except Exception as e:
            print(f"Error loading settings for profile_id={profile_id}: {str(e)}")
            current_app.logger.error(f"Error loading settings for profile_id={profile_id}: {str(e)}")
        print("load_profile_settings end work. No settings found")
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
