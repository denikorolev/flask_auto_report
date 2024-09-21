# new_report_creation.py
#v0.1.1
# Includes create_report route

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import current_user, login_required
from models import db, User, Report, ReportType, ReportSubtype, ReportParagraph, Sentence  
from file_processing import extract_paragraphs_and_sentences
from werkzeug.utils import secure_filename
import os
import shutil 

new_report_creation_bp = Blueprint('new_report_creation', __name__)

# Check the file extensions for being in allowed list
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

# Routes

@new_report_creation_bp.route('/create_report', methods=['GET', 'POST'])
@login_required
def create_report():
    page_title = "List of the reports"
    menu = current_app.config['MENU']
    # Geting report types and subtypes 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype, "subtype_type_name": rst.report_type_rel.type}
        for rst in report_subtypes
    ]
    
    # IF part
    if request.method == 'POST':
        # Button 'create' report had been pressed
        action = request.form.get('action')
        report_name = request.form.get('report_name')
        report_type = request.form.get('report_type')
        report_subtype = request.form.get('report_subtype')
        comment = request.form.get('comment')
        report_side = request.form.get('report_side') == 'true'
        
        if action == 'manual':
            # If user press button "create new report we created new report and redirect to page for editing new report"
            new_report = Report.create(
                userid=current_user.id,
                report_name=report_name,
                report_type=report_type,
                report_subtype=report_subtype,
                comment=comment,
                report_side=report_side
            )
            flash("Report created successfully", "success")
            return redirect(url_for("editing_report.edit_report", report_id=new_report.id))
        
        elif action == 'existing':
            # Save data from form to the session
            session['report_name'] = report_name
            session['report_type'] = report_type
            session['report_subtype'] = report_subtype
            session['comment'] = comment
            session['report_side'] = report_side
            # Geting all user's reports which have the same type with form
            user_reports = Report.query.filter_by(userid=current_user.id, report_type=report_type).all()
            return render_template("create_report.html",
                           title=page_title,
                           menu=menu,
                           report_types=report_types,
                           report_subtypes=report_subtypes_dict,
                           user_reports_list=user_reports)
            
        elif action == 'file':
            user_temp_folder = f"{current_user.id}_temp"
            if 'report_file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            file = request.files['report_file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(user_temp_folder, filename)
                if not os.path.exists(user_temp_folder):
                    os.makedirs(user_temp_folder)
                file.save(filepath)
                
                try:
                    # Extract content from the file
                    paragraphs_from_file = extract_paragraphs_and_sentences(filepath)

                    # Create new report
                    new_report = Report.create(
                        userid=current_user.id,
                        report_name=report_name,  
                        report_type=report_type,  
                        report_subtype=report_subtype,  
                        comment=comment,  
                        report_side=report_side  
                    )

                    # Add paragraphs and sentences to the report
                    for idx, paragraph in enumerate(paragraphs_from_file, start=1):
                        new_paragraph = ReportParagraph.create(
                            paragraph_index=idx,
                            report_id=new_report.id,
                            paragraph=paragraph['title'],
                            paragraph_visible=True
                        )
                        for sidx, sentence in enumerate(paragraph['sentences'], start=1):
                            Sentence.create(
                                paragraph_id=new_paragraph.id,
                                index=sidx,
                                weight=1,
                                comment='',
                                sentence=sentence
                            )
                            
                    # После успешной обработки удаляем временную папку и её содержимое
                    if os.path.exists(user_temp_folder):
                        shutil.rmtree(user_temp_folder)  # Удаляет папку и все файлы в ней

                    flash("Report created from file successfully", "success")
                    return redirect(url_for("editing_report.edit_report", report_id=new_report.id))
                
                except Exception as e:
                    # Если произошла ошибка, удаляем временную папку и её содержимое
                    if os.path.exists(user_temp_folder):
                        shutil.rmtree(user_temp_folder)
                    flash(f"Error occurred during file processing: {str(e)}", "error")
                    return redirect(request.url)
    
    return render_template("create_report.html",
                           title=page_title,
                           menu=menu,
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict
                           )
    
@new_report_creation_bp.route('/select_existing_report', methods=['POST'])
@login_required
def select_existing_report():
    existing_report_id = request.form.get('existing_report_id')
    if not existing_report_id:
        flash('No report selected', 'error')
        return redirect(url_for('new_report_creation.create_report'))

    # Get the saved form data from the session
    report_name = session.get('report_name')
    report_type = session.get('report_type')
    report_subtype = session.get('report_subtype')
    comment = session.get('comment')
    report_side = session.get('report_side')

    # Create a new report
    new_report = Report.create(
        userid=current_user.id,
        report_name=report_name,
        report_type=report_type,
        report_subtype=report_subtype,
        comment=comment,
        report_side=report_side
    )
    # Copy paragraphs and sentences from the existing report
    existing_report = Report.query.get(existing_report_id)
    for paragraph in existing_report.report_paragraphs:
        new_paragraph = ReportParagraph.create(
            paragraph_index=paragraph.paragraph_index,
            report_id=new_report.id,
            paragraph=paragraph.paragraph,
            paragraph_visible=paragraph.paragraph_visible
        )
        for sentence in paragraph.sentences:
            Sentence.create(
                paragraph_id=new_paragraph.id,
                index=sentence.index,
                weight=sentence.weight,
                comment=sentence.comment,
                sentence=sentence.sentence
            )

    flash("Report created from existing report successfully", "success")
    return redirect(url_for("editing_report.edit_report", report_id=new_report.id))
