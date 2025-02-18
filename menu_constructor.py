# menu_constructor.py

from flask import url_for
from flask_login import current_user
from logger import logger



def build_menu():
    """
    Формирует меню на основе текущего профиля.
    """
    menu = [
        
        {"name": "Протокол", "url": url_for("working_with_reports.choosing_report"), "min_rank": 1},
        {"name": "Список протоколов", "url": url_for("my_reports.reports_list"), "min_rank": 1},
        {"name": "Новый протокол", "url": url_for("new_report_creation.create_report"), "min_rank": 1},
        {"name": "Настройки протоколов", "url": url_for("report_settings.report_settings"), "min_rank": 1},
        {"name": "ИИ", "url": url_for("openai_api.start_openai_api"), "min_rank": 3},
        {"name": "Ключевые слова", "url": url_for("key_words.key_words"), "min_rank": 2},
        {"name": "Админ", "url": url_for("admin.admin"), "min_rank": 4},
        {"name": "Настройки профиля", "url": url_for("profile_settings.profile_settings"), "min_rank": 1},
        {"name": "Playground", "url": url_for("playground"), "min_rank": 4}
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
