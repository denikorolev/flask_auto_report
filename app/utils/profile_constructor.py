# profile_constructor.py

from flask import current_app, session, g
import json
from app.models.models import AppConfig
from app.utils.logger import logger


class ProfileSettingsManager:
    """
    Класс для управления настройками профиля.
    """
    @staticmethod
    def load_profile_settings():
        """
        Загружает настройки для указанного профиля из таблицы AppConfig в current_app.config.
        """
        logger.info("Loading profile settings...")
        try:
            profile_id = session.get("profile_id") or None
            if profile_id:
                settings = AppConfig.query.filter_by(profile_id=profile_id).all()
                profile_settings = {setting.config_key: ProfileSettingsManager._parse_value(setting) for setting in settings}
                logger.info(f"Loaded settings for profile_id={profile_id} ✅ successfull.")
                g.profile_settings = profile_settings

                if not profile_settings:
                    logger.warning(f"No settings found for profile_id={profile_id}. ⚠️ Using default settings.")
                    profile_settings = current_app.config.get("DEFAULT_PROFILE_SETTINGS", {})
                    g.profile_settings = profile_settings

                return g.profile_settings

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

    