# utils.py

from sqlalchemy import func




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



        
  

