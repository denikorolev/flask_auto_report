# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, g, jsonify
from flask_login import current_user
from models import UserProfile, db, AppConfig
from profile_constructor import ProfileSettingsManager
from flask_security.decorators import auth_required
from file_processing import sync_profile_files
import json

profile_settings_bp = Blueprint('profile_settings', __name__)

# Functions
def set_profile_settings(profile_id, settings):
    """
    Сохраняет настройки профиля пользователя в таблице AppConfig.
    """
    for key, value in settings.items():
        # Определяем тип данных для сохранения
        if isinstance(value, bool):
            config_type = "boolean"
            value = str(value).lower() # Преобразуем True/False в "true"/"false"
        elif isinstance(value, int):
            config_type = "integer"
        elif isinstance(value, float):
            config_type = "float"
        elif isinstance(value, (dict, list)):
            config_type = "json"
            value = json.dumps(value) # Преобразуем в JSON-строку
        else:
            config_type = "string"
            value = str(value)
        
        try:
            AppConfig.set_setting(profile_id, key, value, config_type=config_type)
        except Exception as e:
            print(f"Error while saving settings: {e}")
            return False
    return True

def set_profile_as_default(profile_id):
    """
    Устанавливает профиль по умолчанию для пользователя.
    """
    print("set_profile_as_default started----------------")
    print(f"profile_id = {profile_id}")
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    if not user_profiles:
        return False
    try:
        for profile in user_profiles:
            if profile.id == int(profile_id):
                profile.default_profile = True
                print(f"set profile {profile.id} as default")
            else:
                print(f"set profile {profile.id} as NOT default")
                profile.default_profile = False
            profile.save()
    except Exception as e:
        print(f"Error while setting default profile: {e}")
        return False
    print("End of set_profile_as_default----------------")
    return True
    

# Маршрут для загрузки страницы настроек профиля 
@profile_settings_bp.route("/profile_settings", methods=["GET"])
@auth_required()
def profile_settings():
    profile = g.current_profile
    if profile:
        return render_template('profile_settings.html', 
                               title="Настройки профиля", 
                               profile=profile)
    else:
        print('Profile not found.', 'danger')
        return redirect(url_for('index'))

# Маршрут для выбора существующего профиля
@profile_settings_bp.route("/choosing_profile", methods=["GET"])
@auth_required()
def choosing_profile():
    # Вот пользователь авторизован и у него либо нет профиля 
    # либо их несколько и нет дефолтного
    print("profile settings started-------------")
    print(f"profile settings started and profile in g = {getattr(g,'current_profile', None)}")
    print(f"profile settings, looking for profile in session, profile = {session.get('profile_id')}")
    print("not use profile from session")
    user_profiles = UserProfile.get_user_profiles(current_user.id)
    print(f"looking for user_profiles: {user_profiles}")
    if not user_profiles:
        print("profile settings end work with success if it's new user -------------")
        return render_template("choosing_profile.html",
                           title="Создание нового профиля",
                           new_user=True)
    profile_id = request.args.get("profile_id") or None
    print(f"profile_id from url: {profile_id}")
    if profile_id:
        print("inside profile_id from url logic")
        profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
        if profile:
            session["profile_id"] = profile.id
            g.current_profile = profile
            ProfileSettingsManager.load_profile_settings()
            # Синхронизацию файлов пока оставлю здесь, но ее нужно будет перенести
            sync_profile_files(profile.id)
            print("profile settings end work with success -------------")
            return redirect(url_for("working_with_reports.choosing_report"))
        else:
            print("profile settings end work with error -------------")
            return render_template(url_for("error"),
                           title="Данные о выбранном профиле не получены"
                           )
    print("not dive into profile_id from url logic")
    return render_template("choosing_profile.html",
                           title="Выбор профиля",
                           user_profiles=user_profiles)


# Маршрут для создания профиля
@profile_settings_bp.route("/create_profile", methods=["POST"])
@auth_required()
def create_profile():
    print("creating profile started--------")
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received."}), 400
    
    profile_name = data.get('profile_name')
    description = data.get('description')
    is_default = data.get('is_default')
    
        
    if profile_name:
        print("creating profile name found")
        try:
            new_profile = UserProfile.create(
                current_user.id, 
                profile_name, 
                description,
                default_profile=is_default
                )
            
            print("logic of creating profile settings")
            default_settings = dict(current_app.config.get("DEFAULT_PROFILE_SETTINGS", {}))
            print(f"new settings for new profile: {profile_settings}")
            save_settings = set_profile_settings(new_profile.id, default_settings)
    
        except Exception as e:
            print("creating profile end work {e} --------")
            return jsonify({"status": "error", "message": str(e)}), 400
        
    
    
        if not save_settings:
            return jsonify({"status": "error", "message": "Не получилось сохранить настройки по умолчанию для нового профиля"}), 400
        print("creating profile end work SUCCESS --------")
        return jsonify({"status": "success", "message": "Profile created successfully!"}), 200
    
    print("creating profile end work ERROR no profile name --------")
    return jsonify({"status": "error", "message": "Profile name is required."}), 400


# Маршрут для обновления имени и дескриптора профиля и выбора профиля по умолчанию
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@auth_required()
def update_profile_settings():
    data = request.get_json()
    profile_id = data.get("profile_id")
    new_name = data.get("profile_name")
    new_description = data.get("description")
    is_default = data.get("is_default")
    print(f"this profile default = {is_default}")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    
    if profile:
        profile.profile_name = new_name
        profile.description = new_description
        profile.save()
        if is_default:
            set_default = set_profile_as_default(profile_id)
            print(f"Профиль установлен как дефолтный = {set_default}")
            if not set_default:
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