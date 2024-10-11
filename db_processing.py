# db_processing.py

from flask_login import current_user
from models import KeyWordsGroup
from utils import get_max_index

def add_keywords_to_db(key_words, report_ids):
    """
    Добавляет ключевые слова в базу данных, распределяя их по новой группе с максимальным group_index.
    Пользователь определяется автоматически через current_user.id.
    
    Args:
        key_words (list): Список ключевых слов для добавления.
        report_ids (list): Список идентификаторов отчетов, к которым привязываются ключевые слова.
    """
    # Определяем максимальный group_index для новой группы
    new_group_index = get_max_index(KeyWordsGroup, current_user.id, KeyWordsGroup.group_index)

    # Добавляем ключевые слова с соответствующими индексами
    for i, key_word in enumerate(key_words):
        KeyWordsGroup.create(
            group_index=new_group_index,
            index=i,
            key_word=key_word,
            user_id=current_user.id,  # Используем current_user для определения пользователя
            reports=report_ids
        )
