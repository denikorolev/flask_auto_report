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
        print("inside load_profile_settings method")
        try:
            
            profile = getattr(g, "current_profile", None)
            profile_id = profile.id if profile else None #session.get("profile_id")
            print(f"profile_id={profile_id}")
            
            if profile_id:
                print(f"Loading settings for profile_id={profile_id}")
                settings = AppConfig.query.filter_by(profile_id=profile_id).all()
                profile_settings = {setting.config_key: ProfileSettingsManager._parse_value(setting) for setting in settings}
                # Сохраняем все настройки в app.config под ключом PROFILE_SETTINGS
                current_app.config["PROFILE_SETTINGS"] = profile_settings
                print(f"PROFILE_SETTINGS: {profile_settings}")
                return profile_settings
        except Exception as e:
            print(f"Error loading settings for profile_id={profile_id}: {str(e)}")
            current_app.logger.error(f"Error loading settings for profile_id={profile_id}: {str(e)}")
        print("No settings found")
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
        elif setting.config_type == "json":
            return json.loads(setting.config_value)
        return setting.config_value

    # Пока нигде не используется
    @staticmethod
    def get_profile_setting(key, default=None):
        """
        Возвращает значение настройки профиля по ключу из app.config["PROFILE_SETTINGS"].
        """
        profile_settings = current_app.config.get("PROFILE_SETTINGS", {})
        return profile_settings.get(key, default)
