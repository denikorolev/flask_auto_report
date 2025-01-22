# profile_constructor.py

from flask import current_app
import json
from models import AppConfig

class ProfileSettingsManager:
    """
    Класс для управления настройками профиля.
    """
    @staticmethod
    def load_profile_settings(profile_id):
        """
        Загружает настройки для указанного профиля из таблицы AppConfig в current_app.config.
        """
        settings = AppConfig.query.filter_by(profile_id=profile_id).all()
        profile_settings = {setting.config_key: ProfileSettingsManager._parse_value(setting) for setting in settings}
        print(f"PROFILE_SETTINGS: {profile_settings}")
        # Сохраняем все настройки в app.config под ключом PROFILE_SETTINGS
        current_app.config["PROFILE_SETTINGS"] = profile_settings

        return profile_settings

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

    @staticmethod
    def get_profile_setting(key, default=None):
        """
        Возвращает значение настройки профиля по ключу из app.config["PROFILE_SETTINGS"].
        """
        profile_settings = current_app.config.get("PROFILE_SETTINGS", {})
        return profile_settings.get(key, default)
