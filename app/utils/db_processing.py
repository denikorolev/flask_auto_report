# db_processing.py

from flask import current_app, session
from flask_security import current_user
from app.models.models import KeyWord, db, AppConfig, UserProfile, ReportCategory, User, Report
from app.utils.logger import logger
from app.utils.common import get_max_index
import json


def add_keywords_to_db(key_words, report_ids):
    """
    Добавляет ключевые слова в базу данных, распределяя их по новой группе с максимальным group_index.
    Пользователь определяется автоматически через current_user.id.
    
    Args:
        key_words (list): Список ключевых слов для добавления.
        report_ids (list): Список идентификаторов отчетов, к которым привязываются ключевые слова.
    """
    # Определяем максимальный group_index для новой группы
    profile_id = session.get("profile_id")
    new_group_index = get_max_index(KeyWord, "profile_id", profile_id, KeyWord.group_index)

    # Добавляем ключевые слова с соответствующими индексами
    for i, key_word in enumerate(key_words):
        KeyWord.create(
            group_index=new_group_index,
            index=i,
            key_word=key_word,
            profile_id=profile_id,
            reports=report_ids
        )



def sync_all_profiles_settings(user_id):
    """
    Синхронизирует настройки для всех профилей пользователя:
    - Добавляет недостающие ключи.
    - Удаляет лишние ключи, не входящие в DEFAULT_PROFILE_SETTINGS.
    
    Выполняется 1 раз за сессию.
    """
    logger.info(f"Начало синхронизации настроек для всех профилей пользователя {user_id}")  
    DEFAULT_PROFILE_SETTINGS = current_app.config.get("DEFAULT_PROFILE_SETTINGS")
    if not DEFAULT_PROFILE_SETTINGS:
        logger.error("DEFAULT_PROFILE_SETTINGS not found in current_app.config. Syncing aborted.")
        return
    profiles = UserProfile.get_user_profiles(user_id)  # Получаем все профили пользователя
    
    for profile in profiles:
        existing_settings = {
            setting.config_key: setting.config_value
            for setting in AppConfig.query.filter_by(profile_id=profile.id).all()
        }

        # Добавляем недостающие настройки
        for key, default_value in DEFAULT_PROFILE_SETTINGS.items():
            if key not in existing_settings:
                AppConfig.set_setting(profile.id, key, default_value)

        # Удаляем лишние настройки (если они больше не нужны)
        for key in list(existing_settings.keys()):  # Преобразуем в список, чтобы избежать изменения dict во время итерации
            if key not in DEFAULT_PROFILE_SETTINGS:
                setting_to_delete = AppConfig.query.filter_by(profile_id=profile.id, config_key=key).first()
                if setting_to_delete:
                    AppConfig.query.filter_by(profile_id=profile.id, config_key=key).delete()
        
        # Фиксируем изменения
        db.session.commit()

    logger.info(f"Синхронизация настроек для всех профилей пользователя {user_id} завершена")
    

# Функция для получения всех модальностей и областей исследования для данного профиля из AppConfig
def get_categories_setup_from_appconfig(profile_id):
    categories = AppConfig.get_setting(profile_id, "CATEGORIES_SETUP")
    if categories:
        logger.info(f"Loaded CATEGORIES_SETUP for profile_id={profile_id} from AppConfig.")
        try:
            categories = json.loads(categories)
            logger.info(f"Successfully decoded CATEGORIES_SETUP")
            return categories
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding CATEGORIES_SETUP for profile_id={profile_id}: {str(e)}")
            return []
    return []
    
 

# Функция для пересборки модальностей и областей исследования из базы данных
def sync_modalities_from_db(profile_id):
    """
    Пересобирает модальности и области исследования из базы данных.
    """
    try:
        logger.info(f"sync_modalities_from_db started for profile_id = {profile_id}")
        modalities = ReportCategory.get_categories_tree(profile_id=profile_id, is_global=False)
        if not modalities:
            logger.warning(f"Нет модальностей для профиля {profile_id}")
            return False
        # Сохраняем модальности в AppConfig
        AppConfig.set_setting(profile_id, "CATEGORIES_SETUP", modalities)
        logger.info(f"Модальности успешно пересобраны для профиля {profile_id}")
        return True
    except Exception as e:
        logger.error(f"sync_modalities_from_db error {e}")
        return False


# Функция для удаления всех пользователей, кроме текущего и указанных в keep_ids
def delete_all_User_except(keep_ids=None):
    """
    Удаляет всех пользователей, кроме текущего и кроме id, указанных в keep_ids.
    keep_ids: list[int] — список id, которых НЕ удалять.
    """
    if keep_ids is None:
        keep_ids = []

    ids_to_keep = set(keep_ids)
    # Добавляем текущего пользователя в список сохранения
    if current_user and current_user.is_authenticated:
        ids_to_keep.add(current_user.id)

    # Находим всех пользователей, которых нужно удалить
    users_to_delete = User.query.filter(~User.id.in_(ids_to_keep)).all()
    count = len(users_to_delete)
    for user in users_to_delete:
        db.session.delete(user)
    db.session.commit()
    print(f"Удалено пользователей: {count}")
    return count


