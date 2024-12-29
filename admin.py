from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy.ext.declarative import DeclarativeMeta
from flask_login import login_required
from models import *
import re
from flask_security.decorators import auth_required, roles_required



admin_bp = Blueprint("admin", __name__)

@admin_bp.before_request
@roles_required("superadmin")  
def restrict_to_superadmin():
    pass


# Function
def get_model_fields():
    """
    Returns two dictionaries:
    - models: a dictionary where keys are model names and values are their field names.
    - association_tables: a dictionary where keys are table names and values are their field names.
    """

    models = {}
    association_tables = {}

    # Получаем список моделей и ассоциативных таблиц из конфигурации
    table_models = current_app.config.get("TABLE_MODELS", {})
    associative_tables = current_app.config.get("ASSOCIATIVE_TABLES", [])

    # Обрабатываем модели
    for table_name, model_class in table_models.items():
        if hasattr(model_class, "__table__"):  # Проверяем, является ли это моделью SQLAlchemy
            models[table_name] = [column.name for column in model_class.__table__.columns]

    # Обрабатываем ассоциативные таблицы
    for table_name in associative_tables:
        table = db.metadata.tables.get(table_name)
        if table is not None:
            association_tables[table_name] = [column.name for column in table.columns]

    return models, association_tables



# Routs

@admin_bp.route("/admin", methods=["GET"])
@auth_required()
def admin():
    
    menu = current_app.config["MENU"]
    
    all_models, association_tables = get_model_fields()
    
    return render_template("admin.html",
                           menu=menu,
                           title="Admin",
                           all_models=all_models,
                           association_tables=association_tables)
    
    

@admin_bp.route("/fetch_data", methods=["POST"])
@auth_required()
def fetch_data():
    data = request.json
    selected_tables = data.get("tables", [])
    selected_columns = data.get("columns", {})
    result = {}

    table_models = current_app.config.get("TABLE_MODELS", {})
    associative_tables = current_app.config.get("ASSOCIATIVE_TABLES", [])

    for table_name in selected_tables:
        if table_name in table_models:
            model_class = table_models[table_name]
            fields = selected_columns.get(table_name, [])
            if "id" not in fields:
                fields.append("id")
            try:
                query = db.session.query(*[getattr(model_class, field) for field in fields])
                records = query.all()
                result[table_name] = [dict(zip(fields, record)) for record in records]
            except Exception as e:
                print(f"Ошибка при запросе к модели {table_name}: {e}")
                result[table_name] = {"error": f"Ошибка: {e}"}
        elif table_name in associative_tables:
            table = db.metadata.tables.get(table_name)
            if table is None:
                print(f"Таблица {table_name} не найдена в metadata")
                result[table_name] = {"error": "Таблица не найдена"}
                continue
            try:
                query = db.session.query(table)
                records = query.all()
                columns = [column.name for column in table.columns]
                result[table_name] = [dict(zip(columns, record)) for record in records]
            except Exception as e:
                print(f"Ошибка при запросе к таблице {table_name}: {e}")
                result[table_name] = {"error": f"Ошибка: {e}"}

    return jsonify(result)


@admin_bp.route("/delete/<table_name>/<int:record_id>", methods=["DELETE"])
@auth_required()
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
@auth_required()
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

    
    
    