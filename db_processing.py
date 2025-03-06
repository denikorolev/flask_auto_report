# db_processing.py

from flask import g, current_app
from flask_login import current_user
from models import KeyWord, db, AppConfig, HeadSentence, BodySentence, TailSentence, head_sentence_group_link, body_sentence_group_link, tail_sentence_group_link, UserProfile
from logger import logger
from utils import get_max_index
from sqlalchemy.orm import joinedload

def add_keywords_to_db(key_words, report_ids):
    """
    Добавляет ключевые слова в базу данных, распределяя их по новой группе с максимальным group_index.
    Пользователь определяется автоматически через current_user.id.
    
    Args:
        key_words (list): Список ключевых слов для добавления.
        report_ids (list): Список идентификаторов отчетов, к которым привязываются ключевые слова.
    """
    # Определяем максимальный group_index для новой группы
    new_group_index = get_max_index(KeyWord, "profile_id", g.current_profile.id, KeyWord.group_index)

    # Добавляем ключевые слова с соответствующими индексами
    for i, key_word in enumerate(key_words):
        KeyWord.create(
            group_index=new_group_index,
            index=i,
            key_word=key_word,
            profile_id=g.current_profile.id,
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
    
    

# Использую для миграции данных перед удалением полей индексов и весов из таблиц предложений
def migrate_sentence_data():
    """
    Переносит индексы главных предложений и веса body/tail предложений
    в соответствующие таблицы связей.
    """
    logger.info("🔄 Начало миграции индексов и весов предложений")
    # 1️⃣ Перенос индексов у `HeadSentence`
    head_sentences = db.session.query(HeadSentence).options(joinedload(HeadSentence.groups)).all()
    for sentence in head_sentences:
        logger.info(f"Обработка главного предложения {sentence.id}")
        for group in sentence.groups:
            db.session.execute(
                head_sentence_group_link.update()
                .where(
                    (head_sentence_group_link.c.head_sentence_id == sentence.id) &
                    (head_sentence_group_link.c.group_id == group.id)
                )
                .values(sentence_index=sentence.sentence_index)
            )

    # 2️⃣ Перенос весов у `BodySentence`
    body_sentences = db.session.query(BodySentence).options(joinedload(BodySentence.groups)).all()
    for sentence in body_sentences:
        logger.info(f"Обработка body предложения {sentence.id}")
        for group in sentence.groups:
            db.session.execute(
                body_sentence_group_link.update()
                .where(
                    (body_sentence_group_link.c.body_sentence_id == sentence.id) &
                    (body_sentence_group_link.c.group_id == group.id)
                )
                .values(sentence_weight=sentence.sentence_weight)
            )

    # 3️⃣ Перенос весов у `TailSentence`
    tail_sentences = db.session.query(TailSentence).options(joinedload(TailSentence.groups)).all()
    for sentence in tail_sentences:
        logger.info(f"Обработка tail предложения {sentence.id}")
        for group in sentence.groups:
            db.session.execute(
                tail_sentence_group_link.update()
                .where(
                    (tail_sentence_group_link.c.tail_sentence_id == sentence.id) &
                    (tail_sentence_group_link.c.group_id == group.id)
                )
                .values(sentence_weight=sentence.sentence_weight)
            )

    db.session.commit()
    logger.info("✅ Миграция индексов и весов завершена успешно")
    