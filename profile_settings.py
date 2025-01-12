# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, g, jsonify
from flask_login import current_user
from models import UserProfile, db, AppConfig
from profile_constructor import ProfileSettingsManager
from flask_security.decorators import auth_required
from file_processing import sync_profile_files
import json

profile_settings_bp = Blueprint('profile_settings', __name__)


# Маршрут для страницы настроек профиля
@profile_settings_bp.route('/profile_settings/<int:profile_id>', methods=['GET'])
@auth_required()
def profile_settings(profile_id):
    # menu = current_app.config['MENU']
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        return render_template('profile_settings.html', 
                               title="Profile Settings", 
                            #    menu=menu,
                               profile=profile)
    else:
        print('Profile not found.', 'danger')
        return redirect(url_for('index'))


# Логика для того чтобы установить выбранный профайл
@profile_settings_bp.route("/set_profile/<int:profile_id>")
@auth_required()
def set_profile(profile_id):
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        session['profile_id'] = profile.id
        ProfileSettingsManager.load_profile_settings(g.current_profile.id)
        sync_profile_files(g.current_profile.id)
    else:
        print("Profile not found.", "danger")
    return redirect(url_for("working_with_reports.choosing_report"))


# Новый маршрут для создания профиля
@profile_settings_bp.route("/create_profile", methods=['POST',"GET"])
@auth_required()
def create_profile():
    print("started route 'create profile'")
    if request.method == 'POST':
        profile_name = request.form.get('profile_name')
        description = request.form.get('description')
        default_profile = False
        if profile_name:
            # Создаем профиль пользователя
            UserProfile.create(
                current_user.id, 
                profile_name, 
                description,
                default_profile=default_profile
                )
            print("Profile created successfully!", "success")
            return redirect(url_for('index'))
        else:
            print("Profile name is required.", "danger")

    return render_template('create_profile.html', title="Create Profile")


# Маршрут для обновления имени и дескриптора профиля
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@auth_required()
def update_profile_settings():
    data = request.get_json()
    profile_id = data.get("profile_id")
    new_name = data.get("profile_name")
    new_description = data.get("description")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    
    if profile:
        profile.profile_name = new_name
        profile.description = new_description
        profile.save()
        return jsonify({"status": "success", "message": "Profile updated successfully!"}), 200
    else:
        return jsonify({"status": "error", "message": "Profile not found or you do not have permission to update it."}), 400



# Маршрут для удаления профиля
@profile_settings_bp.route('/delete_profile/<int:profile_id>', methods=["DELETE"])
@auth_required()
def delete_profile(profile_id):
    print("you are deleting profile")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        profile.delete()
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
    data = request.json  # Получаем данные из запроса
    profile_id = session.get("profile_id")

    if not profile_id:
        return jsonify({"status": "error", "message": "Profile not selected"}), 400

    # Сохраняем каждую настройку в AppConfig
    for key, value in data.items():
        # Определяем тип данных для сохранения
        if isinstance(value, bool):
            config_type = "boolean"
            value = str(value).lower()  # Преобразуем True/False в "true"/"false"
        elif isinstance(value, int):
            config_type = "integer"
        elif isinstance(value, float):
            config_type = "float"
        elif isinstance(value, (dict, list)):
            config_type = "json"
            value = json.dumps(value)  # Преобразуем в JSON-строку
        else:
            config_type = "string"
            value = str(value)  # Преобразуем в строку для универсальности

        try: # Сохраняем настройку в AppConfig
            AppConfig.set_config(profile_id, key, value, config_type=config_type)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    ProfileSettingsManager.load_profile_settings(g.current_profile.id)
    return jsonify({"status": "success", "message": "Settings saved successfully!"})
