# menu_constructor.py

from flask import url_for
from flask_login import current_user
from app.utils.logger import logger



def build_menu():
    """
    Формирует меню на основе текущего профиля.
    """
    menu = [
        {"name": "Протокол", "url": url_for("working_with_reports.choosing_report"), "min_rank": 3, "title": "Выбор протокола"},
        {"name": "Список протоколов", "url": url_for("my_reports.reports_list"), "min_rank": 3, "title": "Список всех протоколов для данного профиля"},
        {"name": "Новый протокол", "url": url_for("new_report_creation.create_report"), "min_rank": 3, "title": "Создание нового протокола"},
        {"name": "ИИ", "url": url_for("openai_api.start_openai_api"), "min_rank": 3, "title": "Чат с искусственным интеллектом"},
        {"name": "Ключевые слова", "url": url_for("key_words.key_words"), "min_rank": 3, "title": "Настройка ключевых слов"},
        {"name": "Админ", "url": url_for("admin.admin"), "min_rank": 4, "title": "Админка"},
        {"name": "PG", "url": url_for("support.playground"), "min_rank": 4, "title": "Песочница"},
        {"name": "Архив", "url": url_for("working_with_reports.snapshots"), "min_rank": 3, "title": "Здесь можно посмотреть архивы протоколов сортированные по типу протокала и дате"},
    ]


    # Получаем ранг текущего пользователя
   
    if not current_user.is_authenticated:
        user_rank = 0
    else:
        user_rank = current_user.get_max_rank()
        if user_rank is None:
            logger.warning(f"User {current_user.email} has no rank. Using default rank=0.")
            user_rank = 0

    # Фильтруем пункты меню в зависимости от ранга
    filtered_menu = [item for item in menu if item["min_rank"] <= user_rank]
        
    return filtered_menu
