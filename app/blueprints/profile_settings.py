# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, jsonify
import json
from flask_login import current_user
from app.models.models import User, UserProfile, db, AppConfig, Paragraph, ReportType, ReportShare, ReportCategory
from flask_security.decorators import auth_required
from app.utils.file_processing import sync_profile_files
from app.models.models import Report
from app.utils.logger import logger

profile_settings_bp = Blueprint('profile_settings', __name__)

# Functions

def set_profile_settings(profile_id, settings):
    """
    Сохраняет настройки профиля пользователя.
    """
    for key, value in settings.items():
        if not AppConfig.set_setting(profile_id, key, value):
            return False  # Если ошибка — сразу выход
    return True


def set_profile_as_default(profile_id):
    """
    Устанавливает профиль по умолчанию для пользователя.
    """
    logger.info(f"set_profile_as_default started and profile_id = {profile_id}")
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    if not user_profiles:
        return False
    try:
        for profile in user_profiles:
            if profile.id == int(profile_id):
                profile.default_profile = True
                logger.info(f"set profile {profile.id} as default")
            else:
                logger.info(f"set profile {profile.id} as NOT default")
                profile.default_profile = False
            profile.save()
    except Exception as e:
        logger.error(f"set_profile_as_default error {e}")
        return False
    logger.info(f"set_profile_as_default end work successfull")
    return True
    
# Routes

# Маршрут для загрузки страницы настроек профиля 
@profile_settings_bp.route("/profile_settings", methods=["GET"])
@auth_required()
def profile_settings():
    logger.info(f"(route 'profile_settings') --------------------------------------")
    logger.info(f"(route 'profile_settings') 🚀 Profile settings started")
    profile_id = session.get("profile_id")

    profile = UserProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
    profile_data = profile.get_profile_data()
    logger.debug(f"(route 'profile_settings') Profile data: {profile_data}")
    
    if profile_data:
        logger.info(f"(route 'profile_settings') ✅ Profile settings loaded")
        logger.info(f"(route 'profile_settings') -----------------------------")
        return render_template('profile_settings.html', 
                               title="Настройки профиля", 
                               profile=profile_data)
    else:
        logger.error(f"(route 'profile_settings') ❌ Profile not found")
        return redirect(url_for('main.index'))


# Маршрут для выбора существующего профиля
@profile_settings_bp.route("/choosing_profile", methods=["GET"])
@auth_required()
def choosing_profile():
   
    profile_id = request.args.get("profile_id") or None
    logger.info(f"(Маршрут 'choosing_profile') Получен id профиля из url: {profile_id}")
    if profile_id:
        logger.info(f"(Маршрут 'choosing_profile') Начинаем логику выбора профиля по id из url")
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        print(f"Profile = {profile}")
        if profile:
            session["profile_id"] = profile.id
            session["profile_name"] = profile.profile_name
            session["lang"] = AppConfig.get_setting(profile.id, "APP_LANGUAGE", "default_language")
            user_id = current_user.id
            user_email = current_user.email
            # Синхронизацию файлов пока оставлю здесь, но ее нужно будет перенести
            sync_profile_files(profile.id, user_id, user_email)
            logger.info(f"(Маршрут 'choosing_profile') Профиль {profile.id} выбран")
            logger.info(f"(Маршрут 'choosing_profile') ✅ Параметры профиля загружены")
            return redirect(url_for("working_with_reports.choosing_report"))
        else:
            logger.error(f"(Маршрут 'choosing_profile') ❌ Профиль {profile_id} не найден или у вас нет прав доступа к нему")
            return render_template(url_for("error"),
                           title="Данные о выбранном профиле не получены"
                           )
    

# Маршрут для создания нового профиля (это просто маршрут для загрузки страницы создания профиля, 
# ничего не создает) вызывается из before_request_handlers.py и из попапа в header
@profile_settings_bp.route("/new_profile_creation", methods=["GET"])
@auth_required()
def new_profile_creation():
    logger.info(f"(Маршрут 'new_profile_creation') --------------------------------------")
    logger.info(f"(Маршрут 'new_profile_creation') 🚀 Начато создание нового профиля")
    existing_user_profile_id = request.args.get("profile_id") or None
    existing_user_profile = UserProfile.find_by_id_and_user(existing_user_profile_id, current_user.id) if existing_user_profile_id else None
    title = "Создание нового профиля"
    if existing_user_profile:
        title = f"Редактирование профиля {existing_user_profile.profile_name}"
        logger.info(f"(Маршрут 'new_profile_creation') Используем существующий профиль {existing_user_profile.profile_name} для создания нового профиля")
    user_profile_ids = [p.id for p in UserProfile.get_user_profiles(current_user.id)]
    modalities = []

    # Добавляем все глобальные модальности и области исследования (is_global=True)
    modalities += ReportCategory.get_categories_tree(is_global=True)
    # Добавляем все пользовательские  модальности и области исследования (по всем профилям пользователя)
    for pid in user_profile_ids:
        user_modalities = ReportCategory.get_categories_tree(profile_id=pid, is_global=False)
        for user_modality in user_modalities:
            if user_modality.get("name") not in [m.get("name") for m in modalities]:
                logger.info(f"(Маршрут 'new_profile_creation') Добавляем пользовательскую модальность {user_modality.get('name')} из профиля {pid}")
                modalities.append(user_modality)
    print(f"modalities = {modalities}")
    return render_template("new_profile_creation.html",
                           title=title,
                           modalities=modalities,
                           user_profile=existing_user_profile
                           )


# Маршрут для создания нового профиля (это уже маршрут для создания профиля, который принимает данные из формы)
@profile_settings_bp.route("/create_profile", methods=["POST"])
@auth_required()
def create_profile():
    logger.info(f"(Маршрут 'create_profile') 🚀 Начато создание профиля")
    data = request.get_json()
    print(f"Data from request: {data}")
    if not data:
        logger.error(f"(Маршрут 'create_profile') ❌ Не получены данные для создания профиля")
        return jsonify({"status": "error", "message": "Не получены данные для создания профиля"}), 400

    profile_name = data.get('profile_name')
    description = data.get('description')
    is_default = data.get('is_default')
    modalities = data.get('modalities', [])
    areas = data.get('areas', {})
    existing_profile_id = data.get('existing_profile_id', None)

    print(f"modalities: {modalities}")
    print(f"areas: {areas}")

    if not profile_name:
        logger.error(f"(route 'create_profile') ❌ Profile name is required.")
        return jsonify({"status": "error", "message": "Profile name is required."}), 400

    logger.info(f"(route 'create_profile') Profile name: {profile_name}")
    profile = None
    if existing_profile_id:
        try:
            logger.info(f"(route 'create_profile') Попытка получить профиль из базы по id: {existing_profile_id}")
            profile = UserProfile.find_by_id_and_user(existing_profile_id, current_user.id)
        except Exception as e:
            logger.error(f"(route 'create_profile') ❌ Не удалось получить существующий профиль из базы: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 400
    else:
        logger.info(f"(route 'create_profile') Создаем новый профиль для пользователя {current_user.id}")
        try:
            profile = UserProfile.create(
                current_user.id,
                profile_name,
                description,
                default_profile=is_default
            )
        except Exception as e:
            logger.error(f"(route 'create_profile') ❌ Ошибка при создании нового профиля: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 400

    try:
        # --- Добавляем модальности и области профиля ---
        logger.info(f"(route 'create_profile') Начинаем добавление модальностей и областей исследования в профиль {profile.profile_name}")
        created_categories = {}
        for modality_id in modalities:
            global_modality = ReportCategory.query.get(int(modality_id))
            if not global_modality:
                logger.warning(f"(route 'create_profile') Модальность id={modality_id} не найдена.")
                continue

            # Копируем модальность
            modality_cat = ReportCategory.add_category(
                name=global_modality.name,
                parent_id=None,
                profile_id=profile.id,
                is_global=False,
                level=1,
                global_id=global_modality.global_id if global_modality.global_id else None
            )
            created_categories[str(global_modality.id)] = {
                "modality_id": modality_cat.id,
                "modality_name": global_modality.name,
                "modality_global_id": global_modality.global_id if global_modality.global_id else global_modality.id,
                "modality_global_name": ReportCategory.query.get(int(global_modality.global_id)).name if global_modality.global_id else global_modality.name,
                "areas": {}
            }

            # Добавляем области исследования для этой модальности
            area_ids = areas.get(str(modality_id), [])
            for area_id in area_ids:
                # child-область только среди детей выбранной модальности
                child_area = next((child for child in global_modality.children if str(child.id) == str(area_id)), None)
                if not child_area:
                    logger.warning(f"(route 'create_profile') Область id={area_id} не найдена в модальности id={modality_id}.")
                    continue
                area_cat = ReportCategory.add_category(
                    name=child_area.name,
                    parent_id=modality_cat.id,
                    profile_id=profile.id,
                    is_global=False,
                    level=2,
                    global_id=child_area.global_id if child_area.global_id else None
                )
                # Сохраняем область исследования по её id
                created_categories[str(global_modality.id)]["areas"][str(child_area.id)] = {
                    "area_id": area_cat.id,
                    "area_name": child_area.name,
                    "area_global_id": child_area.global_id if child_area.global_id else child_area.id,
                    "area_global_name": ReportCategory.query.get(int(child_area.global_id)).name if child_area.global_id else child_area.name
                }

        logger.info(f"(route 'create_profile') Profile {profile.id} created")
        
        default_settings = dict(current_app.config.get("DEFAULT_PROFILE_SETTINGS", {}))
        default_settings["CATEGORIES_SETUP"] = created_categories  # <-- Сохраняем созданную структуру модальностей и областей
        save_settings = set_profile_settings(profile.id, default_settings)
        session["profile_id"] = profile.id  # Сохраняем id нового профиля в сессии
        session["profile_name"] = profile.profile_name  # Сохраняем имя профиля в сессии

        logger.info(f"(route 'create_profile') ✅ Профиль {profile.profile_name} успешно создан!")
        if not save_settings:
            logger.error(f"(route 'create_profile') ❌ Не получилось сохранить настройки по умолчанию для нового профиля")
            return jsonify({"status": "error", "message": "Не получилось сохранить настройки по умолчанию для нового профиля"}), 400
        return jsonify({"status": "success", "message": f"Профиль {profile.profile_name} успешно создан!", "data": profile.id}), 200

    except Exception as e:
        logger.error(f"(route 'create_profile') ❌ Ошибка при добавлении модальностей и областей исследования: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
        
    
    
# Маршрут для обновления имени и дескриптора профиля и выбора профиля по умолчанию
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@auth_required()
def update_profile_settings():
    logger.info(f"(route 'update_profile_settings') --------------------------------------")
    logger.info(f"(route 'update_profile_settings') 🚀 Profile settings update started")
    
    data = request.get_json()
    profile_id = data.get("profile_id")
    new_name = data.get("profile_name")
    new_description = data.get("description")
    is_default = data.get("is_default")
    username = data.get("username")
    
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    
    if profile:
        current_user.username = username
        current_user.save()
        profile.profile_name = new_name
        profile.description = new_description
        profile.save()
        if is_default:
            set_default = set_profile_as_default(profile_id)
            if not set_default:
                logger.error(f"(route 'update_profile_settings') ❌ Error setting profile {profile_id} as default")
                notification_message = ["не получилось установить профиль по умолчанию"]
                return jsonify({"status": "succuss","notifications": notification_message, "message": "Изменения сохранены, но"}), 400
        
        return jsonify({"status": "success", "message": "Данные профиля успешно обновлены!"}), 200
    else:
        return jsonify({"status": "error", "message": "Profile not found or you do not have permission to update it."}), 400



# Маршрут для удаления профиля
@profile_settings_bp.route('/delete_profile/<int:profile_id>', methods=["DELETE"])
@auth_required()
def delete_profile(profile_id):
    print("deleting profile started--------")
    print(f"you are deleting profile and profile_id = {profile_id}")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        try:
            profile.delete()
            print(f"profile {profile_id} deleted")
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        
        session.pop("profile_id", None)
        return jsonify({"status": "success", "message": "Profile deleted successfully!"}), 200
    else:
        return jsonify({"status": "error", "message": "Profile not found or you do not have permission to delete it."}), 400


# Маршрут для сохранения настроек профиля
@profile_settings_bp.route("/update_settings", methods=["POST"])
@auth_required()
def save_settings():
    """
    Сохраняет настройки профиля пользователя в таблице AppConfig.
    """
    settings = request.json  # Получаем данные из запроса
    profile_id = session.get("profile_id")

    if not profile_id:
        return jsonify({"status": "error", "message": "Profile not selected"}), 400

    save_settings = set_profile_settings(profile_id, settings)
    if not save_settings:
        return jsonify({"status": "error", "message": "Не получилось сохранить настройки"}), 400

    return jsonify({"status": "success", "message": "Settings saved successfully!"})


# Маршрут для установки профиля по умолчанию
@profile_settings_bp.route("/set_default_profile/<int:profile_id>", methods=["POST"])
@auth_required()
def set_default_profile(profile_id):
    if not profile_id:
        return jsonify({"status": "error", "message": "Профиль не выбран"}), 400
    set_default = set_profile_as_default(profile_id)
    if not set_default:
        return jsonify({"status": "error", "message": "Не получилось установить профиль по умолчанию"}), 400
    return jsonify({"status": "success", "message": "Профиль установлен как дефолтный"}), 200



# Маршрут чтобы поделиться с конкретным пользователем всеми протоколами данного профиля
@profile_settings_bp.route("/share_profile", methods=["POST"])
@auth_required()
def share_profile():
    """
    Поделиться профилем с другим пользователем.
    """
    logger.info(f"(route 'share_profile') --------------------------------------")
    logger.info(f"(route 'share_profile') 🚀 Sharing all reports of this profile started")
    data = request.get_json()
    
    email = data.get("email")
    logger.info(f"(route 'share_profile') Recipient email: {email}")
    
    recipient = User.find_by_email(email)
    if not recipient:
        logger.error(f"(route 'share_profile') ❌ User with this email not found")
        return jsonify({"status": "error", "message": "Пользователь с данным email не найден"}), 400
    logger.info(f"(route 'share_profile') Recipient found: {recipient.email}")
    
    try:
        user_id = current_user.id
        profile_id = session.get("profile_id")
        all_reports = Report.find_by_profile(profile_id, user_id)
    except Exception as e:
        logger.error(f"(route 'share_profile') ❌ Error getting current user or current profile: {e}")
        return jsonify({"status": "error", "message": "Не получилось загрузить данные текощего пользователя или текущего профиля"}), 400
    
    logger.info(f"(route 'share_profile') ✅ Got all necessary data. Starting sharing...")
    
    try:
        for report in all_reports:
            try:
                ReportShare.create(report.id, user_id, recipient.id)
            except Exception as e:
                logger.error(f"(route 'share_profile') ❌ Error sharing report {report.report_name}: {e}. Skipping...")
                continue
        logger.info(f"(route 'share_profile') ✅ All reports shared successfully")
        return jsonify({"status": "success", "message": "Профиль успешно поделен"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@profile_settings_bp.route("/rebuild_modalities_from_db", methods=["POST"])
@auth_required()
def rebuild_modalities_from_db():
    """
    Пересобирает модальности и области исследования из базы данных.
    """
    logger.info(f"(route 'rebuild_modalities_from_db') 🚀 Начинаем пересборку модальностей из БД")

    profile_id = session.get("profile_id")
    if not profile_id:
        logger.error(f"(route 'rebuild_modalities_from_db') ❌ Профиль не выбран")
        return jsonify({"status": "error", "message": "Профиль не выбран"}), 400
    
    try:
        modalities = ReportCategory.get_categories_tree(profile_id=profile_id, is_global=False)
        if not modalities:
            logger.warning(f"(route 'rebuild_modalities_from_db') ❌ Нет модальностей для профиля {profile_id}")
            return jsonify({"status": "warning", "message": "Нет модальностей для пересборки"}), 200
        
        # Сохраняем модальности в сессию
        logger.info(f"(route 'rebuild_modalities_from_db') ✅ Модальности успешно пересобраны")
        return jsonify({"status": "success", "message": "Модальности успешно пересобраны"}), 200
    except Exception as e:
        logger.error(f"(route 'rebuild_modalities_from_db') ❌ Ошибка при пересборке модальностей: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


