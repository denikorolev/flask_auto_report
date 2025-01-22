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



