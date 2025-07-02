from flask import Blueprint, render_template, request, jsonify, current_app, g
from models import *
from logger import logger
import re
from flask_security.decorators import auth_required, roles_required
from sentence_processing import group_keywords, sort_key_words_group
import os




admin_bp = Blueprint("admin", __name__)


# Функция для проверки роли пользователя и сопоствления 
# с позицией superadmin, если пользователь не является суперадмином то выдает ошибку
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
@roles_required("superadmin")  # Доступ только для суперадминов
def admin():
    
    
    all_models, association_tables = get_model_fields()
    
    return render_template("admin.html",
                           title="Admin",
                           all_models=all_models,
                           association_tables=association_tables,
                           )


@admin_bp.route("/fetch_data", methods=["POST"])
@auth_required()
def fetch_data():
    data = request.json
    selected_tables = data.get("tables", [])
    selected_columns = data.get("columns", {})
    result = {}
    logger.info(f"Запрос данных для таблиц: {selected_tables}")

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

    return jsonify({"status": "success",
                    "data": result})


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



# Маршрут для поиска пользоватея и отправки его данных на клиент
@admin_bp.route("/search_user", methods=["POST"])
@auth_required()
@roles_required("superadmin") 
def search_user():
    """Ищет пользователя по имени, email или ID."""
    data = request.get_json()
    search_value = data.get("search", "").strip()

    if not search_value:
        return jsonify({"status": "error", "message": "Не указано значение для поиска."}), 400

    # Попробуем найти пользователя по ID, email или имени
    try:
        # Фильтр по ID, email или имени пользователя
        users = []
        if search_value.isdigit():
            users = User.query.filter(
                (User.id == int(search_value)) |
                (User.username.ilike(f"%{search_value}%"))
            ).all()
        else:
            users = User.query.filter(
                (User.email.ilike(f"%{search_value}%")) |
                (User.username.ilike(f"%{search_value}%"))
            ).all()

        if not users:
            return jsonify({"status": "error", "message": "Пользователь не найден."}), 404

        all_roles = Role.query.all()
        # Формируем список пользователей с их данными
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "all_roles": [role.name for role in all_roles],
                "current_role": user.roles[0].name if user.roles else None
            })

        return jsonify({
            "status": "success",
            "data": users_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Ошибка поиска пользователя: {str(e)}")
        return jsonify({"status": "error", "message": "Ошибка поиска пользователя."}), 500




@admin_bp.route("/update_user/<int:user_id>", methods=["PUT"])
@auth_required()
@roles_required("superadmin")  # Доступ только для суперадминов
def update_user(user_id):
    """Обновляет данные пользователя."""
    data = request.get_json()

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": "error", "message": "Пользователь не найден."}), 404

        # Обновление имени и email
        user.username = data.get("username", user.username).strip()
        user.email = data.get("email", user.email).strip()

        # Обновление роли
        new_role_name = data.get("role")
        if new_role_name:
            new_role = Role.query.filter_by(name=new_role_name).first()
            if not new_role:
                return jsonify({"status": "error", "message": f"Роль '{new_role_name}' не найдена в списке допустимых ролей."}), 400

            # Обновляем роль пользователя (заменяем старую)
            user.roles = [new_role]

        user.save()

        return jsonify({"status": "success", "message": "Данные пользователя успешно обновлены."}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка обновления пользователя: {str(e)}")
        return jsonify({"status": "error", "message": "Ошибка сервера."}), 500

    

    

    
@admin_bp.route("/make_all_public", methods=["POST"])
@auth_required()
@roles_required("superadmin")
def make_all_public():
    profile_id = g.current_profile.id
    user_id = g.current_profile.user_id
    if not profile_id:
        return jsonify({"status": "error", "message": " Не удалось получить profile_id."}), 400

    try:
        reports = Report.find_by_profile(profile_id=profile_id, user_id=user_id)
        count = 0
        for report in reports:
            if not report.public:
                report.public = True
                count += 1
        db.session.commit()
        return jsonify({"status": "success", "message": f"{count} протоколов сделано общедоступными."}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при массовом переводе протоколов в public: {e}")
        return jsonify({"status": "error", "message": f"Ошибка при обновлении протоколов: {e}"}), 500



@admin_bp.route("/share_global_keywords", methods=["POST"])
@auth_required()
@roles_required("superadmin")
def share_global_keywords():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"status": "error", "message": "Email не указан"}), 400

    # Находим пользователя по email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

    # Находим профиль-реципиент (например, первый профиль)
    recipient_profile = UserProfile.get_default_profile(user.id)
    if not recipient_profile:
        return jsonify({"status": "error", "message": "У пользователя нет подходящего профиля"}), 404

    # Получаем глобальные ключевые слова текущего профиля
    global_keywords = KeyWord.find_without_reports(g.current_profile.id)
    if not global_keywords:
        return jsonify({"status": "error", "message": "Нет глобальных ключевых слов для копирования"}), 400


    # Копируем ключевые слова
    new_keywords_count = 0
    for group in group_keywords(global_keywords, with_index=True):
        # Для каждой группы делаем новую группу у получателя
        group_index = group['group_index']
        for i, word_obj in enumerate(group['key_words'], 1):
            KeyWord.create(
                group_index=group_index,
                index=i,
                key_word=word_obj['word'],
                profile_id=recipient_profile.id,
            )
            new_keywords_count += 1

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Скопировано {new_keywords_count} глобальных ключевых слов для пользователя {email}."
    }), 200
    
    
    
    
    