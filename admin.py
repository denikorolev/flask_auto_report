from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
import models
import inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from flask_login import login_user, login_required, logout_user, current_user
from models import *
import re


admin_bp = Blueprint("admin", __name__)


# Function
def get_model_fields(module):
    """
    Returns a list of tuples, where each tuple contains the class name and a list of its field names.
    """
    model_fields = {}
    
    # Перебираем все классы в модуле
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Проверяем, что класс принадлежит модулю models и является моделью SQLAlchemy
        if obj.__module__ == module.__name__ and isinstance(obj, DeclarativeMeta):
            if hasattr(obj, "__table__"):
                fields = [field.name for field in obj.__table__.columns]
                model_fields[name] = fields

    reversed_model_fields = dict(reversed(list(model_fields.items())))
    return reversed_model_fields


# Routs

@admin_bp.route("/admin", methods=["GET"])
@login_required
def admin():
    
    menu = current_app.config["MENU"]
    
        
    all_models_and_fields = get_model_fields(models)
    
    return render_template("admin.html",
                           menu=menu,
                           title="Admin",
                           all_models_and_fields=all_models_and_fields)
    
    

@admin_bp.route("/fetch_data", methods=["POST"])
@login_required
def fetch_data():
    # Получаем данные, отправленные с клиента
    print("маршрут запущен")
    data = request.json
    selected_tables = data.get("tables", [])
    selected_columns = data.get("columns", {})

    # Результат для отправки обратно
    result = {}

    for table_name in selected_tables:
        # Получаем класс таблицы по имени
        table_class = globals().get(table_name)
        if not table_class:
            continue  # Если класс не найден, пропускаем

        # Выбираем только указанные поля
        fields = selected_columns.get(table_name, [])
        if "id" not in fields:
            fields.append("id")
        try:
            # Выполняем запрос к базе данных
            query = db.session.query(*[getattr(table_class, field) for field in fields])
            records = query.all()
            
            # Сохраняем результаты в виде списка словарей
            result[table_name] = [dict(zip(fields, record)) for record in records]
        except Exception as e:
            print(f"Ошибка при запросе к таблице {table_name}: {e}")

    print(result)
    # Возвращаем результаты в формате JSON
    return jsonify(result)


@admin_bp.route("/delete/<table_name>/<int:record_id>", methods=["DELETE"])
@login_required
def delete_record(table_name, record_id):
    # Получаем класс таблицы из словаря
    table_class = current_app.config["TABLE_MODELS"].get(table_name)
    print(table_class)
    if not table_class:
        return jsonify({"error": "Таблица не найдена в настройках config.py"}), 404

    # Выполняем запрос для удаления записи
    try:
        record = db.session.query(table_class).get(record_id)
        if record is None:
            return jsonify({"error": "Запись не найдена"}), 404

        db.session.delete(record)
        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении записи: {e}")
        return jsonify({"error": "Ошибка при удалении записи"}), 500
    
    
@admin_bp.route("/update/<table_name>/<int:record_id>", methods=["PUT"])
@login_required
def update_record(table_name, record_id):
    # Получаем класс таблицы из конфигурации
    table_class = current_app.config["TABLE_MODELS"].get(table_name)
    if not table_class:
        return jsonify({"status": "error", "message": "Таблица не найдена в настройках config.py"}), 404

    # Получаем данные из запроса
    data = request.json
    ignored_fields = ["password"]
    id_pattern = re.compile(r"(^|_)id(_|$)", re.IGNORECASE)

    try:
        # Ищем запись по ID
        record = db.session.query(table_class).get(record_id)
        if record is None:
            return jsonify({"status": "error", "message": "Запись не найдена"}), 404

        fields_was_ignored = []
        
        # Обновляем поля в записи
        for key, value in data.items():
            # Пропускаем поля с названием password или содержащие id
            if key in ignored_fields or id_pattern.search(key):
                fields_was_ignored.append(key)
                continue

            # Проверяем, существует ли колонка в модели
            column_attr = getattr(table_class, key, None)
            if column_attr is None:
                continue

            # Получаем тип колонки
            column_type = str(column_attr.property.columns[0].type)

            # Преобразуем строковые значения "True" и "False" в булевые
            if column_type == "BOOLEAN":
                value = value.lower() == "true"

            # Проверяем тип данных для Binary полей
            elif "BINARY" in column_type.upper() and isinstance(value, str):
                fields_was_ignored.append(key)  # Пропускаем строковые данные для бинарных полей
                continue

            # Обновляем поле, если оно существует в записи
            setattr(record, key, value)

        db.session.commit()
        
        # Формируем сообщение для notification
        notification_message = [
            "Эти поля не были обновлены: " + ", ".join(fields_was_ignored) if fields_was_ignored else "Все поля обновлены"
        ]
        print(notification_message)
        return jsonify({
            "status": "success",
            "notifications": notification_message,
            "message": "Fields in the table were updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при обновлении записи: {e}")
        return jsonify({"status": "error", "message": "Ошибка при обновлении записи"}), 500

    
    
    