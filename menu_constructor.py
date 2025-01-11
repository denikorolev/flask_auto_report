# menu_constructor.py

from flask import url_for, g

def build_menu():
    """
    Формирует меню на основе текущего профиля.
    """
    menu = [
        {"name": "Главная", "url": url_for("index")},
        {"name": "Протокол", "url": url_for("working_with_reports.choosing_report")},
        {"name": "Список протоколов", "url": url_for("my_reports.reports_list")},
        {"name": "Новый протокол", "url": url_for("new_report_creation.create_report")},
        {"name": "Настройки", "url": url_for("report_settings.report_settings")},
        {"name": "API", "url": url_for("openai_api.start_openai_api")},
        {"name": "Ключевые слова", "url": url_for("key_words.key_words")},
        {"name": "admin", "url": url_for("admin.admin")},
    ]

    # Добавляем настройки профиля, если профиль выбран
    if g.get("current_profile"):
        menu.append({
            "name": "Настройки профиля",
            "url": url_for("profile_settings.profile_settings", profile_id=g.current_profile.id)
        })

    return menu
