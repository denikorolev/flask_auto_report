# report_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required


report_settings_bp = Blueprint('report_settings', __name__)

@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    return render_template('report_settings.html', title = "Report settings")
