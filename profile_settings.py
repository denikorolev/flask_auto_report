# profile_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import UserProfile, db

profile_settings_bp = Blueprint('profile_settings', __name__)



# Маршрут для страницы настроек профиля
@profile_settings_bp.route('/profile_settings/<int:profile_id>', methods=['GET'])
@login_required
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

# Маршрут для обновления настроек профиля
@profile_settings_bp.route('/update_profile_settings', methods=['POST'])
@login_required
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
