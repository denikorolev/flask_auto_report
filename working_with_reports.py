# reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import Report, ReportType, ReportSubtype, ReportParagraph, Sentence
from file_processing import extract_paragraphs_and_sentences

working_with_reports_bp = Blueprint('working_with_reports', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

@working_with_reports_bp.route('/create_report', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        method = request.form.get('method')
        if method == 'manual':
            return redirect(url_for('reports.create_report_manual'))
        elif method == 'file':
            return redirect(url_for('reports.create_report_file'))
        elif method == 'existing':
            return redirect(url_for('reports.create_report_existing'))
    
    return render_template('create_report.html')
