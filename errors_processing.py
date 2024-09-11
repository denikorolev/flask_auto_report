# errors_processing.py

def print_object_structure(obj, indent=0):
    """Функция для рекурсивного вывода структуры объекта"""
    indent_str = ' ' * (indent * 4)  # Уровень отступов для форматирования вывода
    if isinstance(obj, dict):
        print(f"{indent_str}{{}}:")  # Выводим, что это словарь
        for key, value in obj.items():
            print(f"{indent_str}    {key}:")
            print_object_structure(value, indent + 1)  # Рекурсивно выводим значения
    elif isinstance(obj, list):
        print(f"{indent_str}[]:")  # Выводим, что это список
        for index, value in enumerate(obj):
            print(f"{indent_str}    [{index}]:")
            print_object_structure(value, indent + 1)  # Рекурсивно выводим элементы списка
    elif hasattr(obj, '__dict__'):  # Если это объект класса с атрибутами
        print(f"{indent_str}{type(obj).__name__}:")  # Выводим имя класса объекта
        for key, value in obj.__dict__.items():
            print(f"{indent_str}    {key}:")
            print_object_structure(value, indent + 1)  # Рекурсивно выводим атрибуты объекта
    else:
        print(f"{indent_str}{repr(obj)}")  # Выводим простое значение (строка, число и т.д.)

