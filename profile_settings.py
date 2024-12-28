# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
from flask_login import current_user
from models import UserProfile, db
from flask_security.decorators import auth_required


profile_settings_bp = Blueprint('profile_settings', __name__)



# Маршрут для страницы настроек профиля
@profile_settings_bp.route('/profile_settings/<int:profile_id>', methods=['GET'])
@auth_required()
def profile_settings(profile_id):
    menu = current_app.config['MENU']
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        return render_template('profile_settings.html', 
                               title="Profile Settings", 
                               menu=menu,
                               profile=profile)
    else:
        print('Profile not found.', 'danger')
        return redirect(url_for('index'))


# Логика для того чтобы установить выбранный профайл
@profile_settings_bp.route("/set_profile/<int:profile_id>")
@auth_required()
def set_profile(profile_id):
    print("i'm in set_profile route")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        session['profile_id'] = profile.id
        print(f"Profile '{profile.profile_name}' set as current.", "success")
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


# Маршрут для обновления настроек профиля
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@auth_required()
def update_profile_settings():
    print("im in profile settings")
    profile_id = request.form.get('profile_id')
    new_name = request.form.get('profile_name')
    new_description = request.form.get('description')
    print(profile_id)
    print(new_name)
    print(new_description)

    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        profile.profile_name = new_name
        profile.description = new_description
        db.session.commit()
        print('Profile updated successfully!', 'success')
    else:
        print('Profile not found or you do not have permission to edit it.', 'danger')

    return redirect(url_for('index'))

# Маршрут для удаления профиля
@profile_settings_bp.route('/delete_profile/<int:profile_id>', methods=['POST'])
@auth_required()
def delete_profile(profile_id):
    print("you are deleting profile")
    profile = UserProfile.find_by_id_and_user(profile_id, current_user.id)
    if profile:
        db.session.delete(profile)
        db.session.commit()
        print('Profile deleted successfully!', 'success')
    else:
        print('Profile not found or you do not have permission to delete it.', 'danger')

    return redirect(url_for('index'))
