# utils.py

from sqlalchemy import func
from logger import logger
from flask import g
from flask_security.decorators import auth_required




def ensure_list(value):
    """Преобразует значение в список, если оно не является списком."""
    if not isinstance(value, list):
        return [value]
    return value



def get_max_index(model, filter_field, filter_value, column):
    """
    Вычисляет максимальный индекс для указанного столбца модели для текущего пользователя.

    Args:
        model (db.Model): Модель, для которой нужно вычислить максимальный индекс.
        filter_field (str): Поле, по которому фильтруются данные.
        filter_value (Any): Значение для фильтрации.
        column (db.Column): Столбец, по которому вычисляется максимальный индекс.

    Returns:
        int: Максимальный индекс или 0, если данных нет.
    """
    
    # Динамическое создание фильтра через распаковку словаря
    filter_kwargs = {filter_field: filter_value}
    
    max_index = model.query.filter_by(**filter_kwargs).with_entities(func.max(column)).scalar() or 0
    return max_index + 1


# Нормализация индексов параграфов
def normalize_paragraph_indices(report_id):
    from models import db, Report, Paragraph, HeadSentence

    report = Report.get_by_id(report_id)
    if not report:
        logger.error(f"Протокол {report_id} не найден")
        raise ValueError(f"Протокол {report_id} не найден")
        
    try:
        paragraphs = Paragraph.query.filter_by(report_id=report.id).order_by(Paragraph.paragraph_index).all()
        
        # Обновляем индексы параграфов
        for new_index, paragraph in enumerate(paragraphs):
            paragraph.paragraph_index = new_index
        
        db.session.commit()  
        logger.info(f"Индексы успешно исправлены")
        return
    except Exception as e:
        logger.error(f"Ошибка при исправлении индексов: {str(e)}")
        db.session.rollback()
        raise ValueError(f"Ошибка при исправлении индексов: {str(e)}")
    

# Нормализация индексов главных предложений
def normalize_head_sentence_indices(paragraph_id):
    from models import db, Paragraph, HeadSentenceGroup

    paragraph = Paragraph.get_by_id(paragraph_id)
    if not paragraph:
        logger.error(f"Параграф {paragraph_id} не найден")
        raise ValueError(f"Параграф {paragraph_id} не найден")
    head_sentences_group_id = paragraph.head_sentence_group_id
    
    try:
        head_sentences = HeadSentenceGroup.get_group_sentences(paragraph.head_sentences_group_id)
        
        # Обновляем индексы главных предложений
        for new_index, head_sentence in enumerate(head_sentences):
            head_sentence.sentence_index = new_index
        
        db.session.commit()  
        logger.info(f"Индексы успешно исправлены")
        return
    except Exception as e:
        logger.error(f"Ошибка при исправлении индексов: {str(e)}")
        db.session.rollback()
        raise ValueError(f"Ошибка при исправлении индексов: {str(e)}")


# Проверка уникальности индексов у параграфов и главных предложений
def check_unique_indices(paragraphs):
    """
    Проверяет, уникальны ли индексы параграфов и главных предложений.
    Args:
        paragraphs (list): Список параграфов.
    Raises:
        ValueError: Если обнаружены дублирующиеся индексы параграфов или главных предложений.
    """
    paragraph_indices = set()

    for paragraph in paragraphs:
        paragraph_index = paragraph["paragraph_index"]

        # Проверяем дубликаты параграфов
        if paragraph_index in paragraph_indices:
            raise ValueError(f"Дубликат индекса параграфа: {paragraph_index}")
        paragraph_indices.add(paragraph_index)

        # Проверяем дубликаты в head_sentences
        head_sentence_indices = set()
        for sentence in paragraph["head_sentences"]:
            sentence_index = sentence["index"]

            if sentence_index in head_sentence_indices:
                raise ValueError(
                    f"Дубликат индекса главного предложения: {sentence_index} в параграфе {paragraph_index}"
                )
            head_sentence_indices.add(sentence_index)

    return True



        
  

