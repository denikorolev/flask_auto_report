# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, g, jsonify
from flask_login import current_user
from models import User, UserProfile, db, AppConfig, Paragraph, ReportType, ReportShare
from profile_constructor import ProfileSettingsManager
from flask_security.decorators import auth_required
from file_processing import sync_profile_files
from models import Report
from logger import logger

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
    
    profile = g.current_profile
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
    logger.info(f"(route 'choosing_profile') Profile id from url: {profile_id}")
    if profile_id:
        logger.info(f"(route 'choosing_profile') Starting profile id from url logic")
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        if profile:
            session["profile_id"] = profile.id
            g.current_profile = profile
            user_id = current_user.id
            user_email = current_user.email
            ProfileSettingsManager.load_profile_settings()
            # Синхронизацию файлов пока оставлю здесь, но ее нужно будет перенести
            sync_profile_files(profile.id, user_id, user_email)
            logger.info(f"(route 'choosing_profile') Profile {profile.id} selected")
            logger.info(f"(route 'choosing_profile') ✅ Profile settings loaded")
            return redirect(url_for("working_with_reports.choosing_report"))
        else:
            logger.error(f"(route 'choosing_profile') ❌ Profile {profile_id} not found or you do not have permission to access it")
            return render_template(url_for("error"),
                           title="Данные о выбранном профиле не получены"
                           )
    

# Маршрут для создания нового профиля
@profile_settings_bp.route("/new_profile_creation", methods=["GET"])
@auth_required()
def new_profile_creation():
    logger.info(f"(route 'new_profile_creation') --------------------------------------")
    logger.info(f"(route 'new_profile_creation') 🚀 New profile creation started")
    return render_template("new_profile_creation.html",
                           title="Создание нового профиля")



# Маршрут для создания профиля
@profile_settings_bp.route("/create_profile", methods=["POST"])
@auth_required()
def create_profile():
    logger.info(f"(route 'create_profile') 🚀 Profile creation started")
    data = request.get_json()
    if not data:
        logger.error(f"(route 'create_profile') ❌ No data received")
        return jsonify({"status": "error", "message": "No data received."}), 400
    
    profile_name = data.get('profile_name')
    description = data.get('description')
    is_default = data.get('is_default')
    
        
    if not profile_name:
        logger.error(f"(route 'create_profile') ❌ Profile name is required.")
        return jsonify({"status": "error", "message": "Profile name is required."}), 400

    logger.info(f"(route 'create_profile') Profile name: {profile_name}")
    try:
        new_profile = UserProfile.create(
            current_user.id,
            profile_name,
            description,
            default_profile=is_default
        )
        
        logger.info(f"(route 'create_profile') Profile {new_profile.id} created")
        default_settings = dict(current_app.config.get("DEFAULT_PROFILE_SETTINGS", {}))
        save_settings = set_profile_settings(new_profile.id, default_settings)
        if not save_settings:
            return jsonify({"status": "error", "message": "Не получилось сохранить настройки по умолчанию для нового профиля"}), 400
        print("creating profile end work SUCCESS --------")
        return jsonify({"status": "success", "message": f"Профиль {new_profile.profile_name} успешно создан!", "data": new_profile.id}), 200

    except Exception as e:
        logger.error(f"(route 'create_profile') ❌ Error creating profile: {str(e)}")
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
        g.current_profile = None
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

    ProfileSettingsManager.load_profile_settings()
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
        profile_id = g.current_profile.id
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




