# menu_constructor.py

from flask import url_for, g
from flask_login import current_user

def build_menu():
    """
    Формирует меню на основе текущего профиля.
    """
    print("build_menu started")
    menu = [
        
        {"name": "Протокол", "url": url_for("working_with_reports.choosing_report"), "min_rank": 1},
        {"name": "Список протоколов", "url": url_for("my_reports.reports_list"), "min_rank": 1},
        {"name": "Новый протокол", "url": url_for("new_report_creation.create_report"), "min_rank": 1},
        {"name": "Настройки протоколов", "url": url_for("report_settings.report_settings"), "min_rank": 1},
        {"name": "ИИ", "url": url_for("openai_api.start_openai_api"), "min_rank": 3},
        {"name": "Ключевые слова", "url": url_for("key_words.key_words"), "min_rank": 2},
        {"name": "Админ", "url": url_for("admin.admin"), "min_rank": 4},
        {"name": "Настройки профиля", "url": url_for("profile_settings.profile_settings"), "min_rank": 1}
    ]


    # Получаем ранг текущего пользователя
   
    if not current_user.is_authenticated:
        user_rank = 0
    else:
        user_rank = current_user.get_max_rank()
        if user_rank is None:
            print("user_rank from get_max_rank has returtned as None")
            user_rank = 0
    
    print(f"in build menu, user_rank={user_rank}")

    # Фильтруем пункты меню в зависимости от ранга
    filtered_menu = [item for item in menu if item["min_rank"] <= user_rank]
        
    
    print("build_menu end work")
    print(f"inject_menu get menu ===== {filtered_menu}  ")
    return filtered_menu
