# db_processing.py

from flask import current_app, session
from flask_security import current_user
from app.models.models import KeyWord, db, AppConfig, UserProfile, ReportType, ReportSubtype, ReportCategory, User
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
    
    
    
    
    
# Временная функция для миграции типов и подтипов суперюзера в глобальные категории
def migrate_superuser_types_to_global_categories(super_user_id):
    """
    Создаёт глобальные категории 1 и 2 уровня на основе типов и подтипов суперюзера.
    Если в базе уже есть хотя бы одну глобальную категорию уровня 2, функция не выполняется.
    """
    

    # 1. Все типы (ReportType) суперюзера
    report_types = ReportType.find_by_profile(super_user_id)
    created_categories = {}

    # 1.1. Миграция типов (уровень 1)
    for rtype in report_types:
        # Пропустить если уже есть такая глобальная категория 1 уровня
        global_cat = ReportCategory.query.filter_by(
            name=rtype.type_text, is_global=True, level=1
        ).first()
        if global_cat:
            created_categories[rtype.id] = global_cat
            continue

        # Создаём новую глобальную категорию 1 уровня
        new_cat = ReportCategory.add_category(
            name=rtype.type_text,
            parent_id=None,
            profile_id=None,
            is_global=True,
            level=1,
            global_id=None
        )
        created_categories[rtype.id] = new_cat

    # 1.2. Миграция подтипов (уровень 2)
    for rtype in report_types:
        # Глобальная категория-родитель
        parent_cat = created_categories.get(rtype.id)
        if not parent_cat:
            parent_cat = ReportCategory.query.filter_by(
                name=rtype.type_text, is_global=True, level=1
            ).first()
            if not parent_cat:
                print(f"❌ Не найден или не создан глобальный родитель для типа '{rtype.type_text}', пропуск")
                continue

        subtypes = ReportSubtype.find_by_report_type(rtype.id)
        for subtype in subtypes:
            # Проверить на дубль по name+level+parent_id
            exists = ReportCategory.query.filter_by(
                name=subtype.subtype_text,
                is_global=True,
                level=2,
                parent_id=parent_cat.id
            ).first()
            if exists:
                continue

            # Создать новую глобальную категорию 2 уровня
            ReportCategory.add_category(
                name=subtype.subtype_text,
                parent_id=parent_cat.id,
                profile_id=None,
                is_global=True,
                level=2,
                global_id=None
            )

    print("✅ Миграция глобальных категорий завершена.")
    
    
# Временная функция для миграции пользовательских категорий (типов и подтипов) в ReportCategory
def migrate_user_types_to_profile_categories(user_id):
    """
    Для всех профилей пользователя создает категории 1 и 2 уровня на основе ReportType и ReportSubtype.
    global_id подставляет по совпадению name с глобальными категориями соответствующего уровня и родителя.
    Если не найдено — подставляет 11111.
    """
    GLOBAL_PLACEHOLDER_ID = 11111
    
    # Выполнить один раз, до запуска основной миграции!
    if not ReportCategory.query.get(11111):
        print("⚠️ Создаю глобальную категорию-заглушку для ReportCategory с id=11111")
        cat = ReportCategory(
            id=11111,
            name="UNKNOWN_GLOBAL_CATEGORY",
            parent_id=None,
            global_id=None,
            profile_id=None,
            is_global=True,
            level=0
        )
        db.session.add(cat)
        db.session.commit()

    profiles = UserProfile.query.filter_by(user_id=user_id).all()
    global_types = {cat.name: cat for cat in ReportCategory.query.filter_by(is_global=True, level=1).all()}
    global_subtypes = {}  # (parent_name, name) -> cat

    # Сначала загрузим все глобальные subtypes (2 уровень)
    for cat in ReportCategory.query.filter_by(is_global=True, level=2).all():
        parent = ReportCategory.query.get(cat.parent_id)
        if parent:
            global_subtypes[(parent.name, cat.name)] = cat

    for profile in profiles:
        # Типы (уровень 1)
        for rtype in ReportType.find_by_profile(profile.id):
            global_cat = global_types.get(rtype.type_text)
            global_id = global_cat.id if global_cat else GLOBAL_PLACEHOLDER_ID

            # Проверить дубль
            user_cat = ReportCategory.query.filter_by(
                name=rtype.type_text, profile_id=profile.id, is_global=False, level=1
            ).first()
            if not user_cat:
                user_cat = ReportCategory.add_category(
                    name=rtype.type_text,
                    parent_id=None,
                    profile_id=profile.id,
                    is_global=False,
                    level=1,
                    global_id=global_id
                )

            # Подтипы (уровень 2)
            for subtype in ReportSubtype.find_by_report_type(rtype.id):
                # Найти глобальный subtype по паре (тип, подтип)
                key = (rtype.type_text, subtype.subtype_text)
                global_subcat = global_subtypes.get(key)
                global_subcat_id = global_subcat.id if global_subcat else GLOBAL_PLACEHOLDER_ID

                # Проверить дубль
                user_subcat = ReportCategory.query.filter_by(
                    name=subtype.subtype_text, profile_id=profile.id, is_global=False, level=2, parent_id=user_cat.id
                ).first()
                if not user_subcat:
                    ReportCategory.add_category(
                        name=subtype.subtype_text,
                        parent_id=user_cat.id,
                        profile_id=profile.id,
                        is_global=False,
                        level=2,
                        global_id=global_subcat_id
                    )
    # Затем очищаем CATEGORIES_SETUP в AppConfig для всех профилей пользователя, чтобы программа подтянула новые категории которые есть в базе после миграции
    for profile in profiles:
        AppConfig.set_setting(profile.id, "CATEGORIES_SETUP", "[]")
    logger.info(f"Миграция пользовательских категорий для user_id={user_id} завершена.")
    session["categories_setup"] = False  # Сбрасываем флаг в сессии, чтобы при следующем входе пользователь увидел новые категории
    # Можно добавить уведомление
    session["user_data_synced"] = False  # Сбрасываем флаг синхронизации данных пользователя
    print(f"✅ Миграция пользовательских категорий для user_id={user_id} завершена.")


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
        AppConfig.set_setting(profile_id, "CATEGORIES_SETUP", json.dumps(modalities, ensure_ascii=False))
        logger.info(f"Модальности успешно пересобраны для профиля {profile_id}")
        return True
    except Exception as e:
        logger.error(f"sync_modalities_from_db error {e}")
        return False




# Временная функция для удаления всех пользователей, кроме текущего и указанных в keep_ids
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