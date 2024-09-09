# utils.py

def ensure_list(value):
    """Преобразует значение в список, если оно не является списком."""
    if not isinstance(value, list):
        return [value]
    return value