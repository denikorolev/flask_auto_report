# my_reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import Report, ReportType, ReportSubtype, ReportParagraph, Sentence
from file_processing import extract_paragraphs_and_sentences

my_reports_bp = Blueprint('my_reports', __name__)

# Access configuration parameters
def init_app(app):
    menu = app.config['MENU']
    upload_folder = app.config['UPLOAD_FOLDER']
    return menu, upload_folder



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

@my_reports_bp.route('/reports_list', methods=['POST', 'GET'])
@login_required
def reports_list(): 
    page_title = "List of the reports"
    new_report_query = request.args.get("new_report_query")   # The line for check if user want to create new report
    type_subtype_editing_query = request.args.get("type_subtype_editing_query") 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    
    # Initialize config variables
    menu, upload_folder = init_app(current_app)
    
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype, "subtype_type_name": rst.report_type_rel.type}
        for rst in report_subtypes
    ]
    # All reports of current user with load of linked records (types and subtypes) by method in class
    user_reports_rel = Report.query.filter_by(userid=current_user.id).all()
    
    # If user want to make new report show them form for report creation
    if request.method == "POST":
        if "report_creation_form_view" in request.form:
            return redirect(url_for("my_reports.reports_list", new_report_query=True))
        
        # Create new report from file
        if "report_creation_from_file" in request.form:
            if 'report_file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            file = request.files['report_file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                # Extract content from the file
                paragraphs_from_file = extract_paragraphs_and_sentences(filepath)

                # Create new report
                new_report = Report.create(
                    userid=current_user.id,
                    report_name=request.form["report_name"],
                    report_type=request.form["report_type"],
                    report_subtype=request.form["report_subtype"],
                    comment=request.form["comment"]
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

                flash("Report created from file successfully", "success")
                return redirect(url_for("my_reports.edit_report", report_id=new_report.id))
        
    # If user press button "create new report we created new report and redirect to page for editing new report"
        if "report_creation" in request.form:
            # New string in the tab reports
            new_report = Report.create(
                userid=current_user.id,
                report_name=request.form["report_name"],
                report_type=request.form["report_type"],
                report_subtype=request.form["report_subtype"],
                comment=request.form["comment"]
            )
            flash("Report created successfully", "success")
            return redirect(url_for("my_reports.edit_report", report_id=new_report.id))
        
        # If user press button "add new type or subtype we show them form for editing types and subtypes"
        if "type_subtype_edit_form_view" in request.form:
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        
        # Processing type
        if "add_new_type_button" in request.form:
            ReportType.create(type=request.form["new_type"])
            flash("New type was created successfully")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        if "delete_type_button" in request.form:
            try:
                ReportType.delete_by_id(request.form["type_id"])
                flash("Type was deleted successfully")
            except:
                flash("It's impossible to delele the type because of existing of the reports with this type")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        if "edit_type_button" in request.form:
            type_for_editing = ReportType.query.get(request.form["type_id"])
            type_for_editing.type = request.form["type_type"]
            type_for_editing.save()
            flash("Type edited successfully")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        
        # Processing subtype
        if "add_new_subtype_button" in request.form:
            ReportSubtype.create(type=request.form["report_subtype_type"], subtype=request.form["new_subtype"])
            flash("New subtype was created successfully")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        if "delete_subtype_button" in request.form:
            try:
                ReportSubtype.delete_by_id(request.form["subtype_id"])
                flash("Subtype was deleted successfully")
            except:
                flash("It's impossible to delele the subtype because of existing of the reports with this type")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        if "edit_subtype_button" in request.form:
            subtype_for_editing = ReportSubtype.query.get(request.form["subtype_id"])
            subtype_for_editing.subtype = request.form["subtype_subtype"]
            subtype_for_editing.save()
            flash("Subtype edited successfully")
            return redirect(url_for("my_reports.reports_list", type_subtype_editing_query=True))
        
        if "report_delete" in request.form:
            try:
                Report.delete_by_id(request.form["report_id"])
                flash("Report deleted successfully", "success")
            except Exception as e:
                flash(f"Report not found. error code: {e}", "error")
            return redirect(url_for("my_reports.reports_list"))
                
    return render_template("reports_list.html", 
                           title=page_title, 
                           menu=menu,
                           new_report_query=new_report_query, 
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict, 
                           user_reports_rel=user_reports_rel,
                           type_subtype_editing_query=type_subtype_editing_query
                           )
