# radiologary_user_profile.py 

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import User

profile_bp = Blueprint('profile', __name__)

# @profile_bp.route('/settings', methods=['GET', 'POST'])
# @login_required
# def user_settings():
#     if request.method == 'POST':
#         theme = request.form['theme']
#         current_user.theme = theme
#         current_user.save()
#         print("Theme updated successfully", "success")
#         return redirect(url_for('profile.user_settings'))

#     return render_template('user_settings.html', user=current_user)
