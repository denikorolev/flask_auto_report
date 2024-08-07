# report_settings.py

from flask import Blueprint, render_template, request, redirect, flash, current_app
from flask_login import login_required, current_user
from models import ReportType, ReportSubtype, AppConfig 
from file_processing import file_uploader

report_settings_bp = Blueprint('report_settings', __name__)

# Functions

# Routs

@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    page_title = "Report settings"
    # Get data from the config
    menu = current_app.config["MENU"]
    upload_folder_path = current_app.config.get("UPLOAD_FOLDER_PATH")
    upload_folder_name = current_app.config.get("UPLOAD_FOLDER_NAME")
    
    
    # Geting report types and subtypes 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype, "subtype_type_name": rst.report_type_rel.type}
        for rst in report_subtypes
    ]
    # Processing type
    if request.method == "POST":
        if "add_new_type_button" in request.form:
            ReportType.create(type=request.form["new_type"])
            flash("New type was created successfully")
            return redirect(request.url)
        
        if "delete_type_button" in request.form:
            try:
                ReportType.delete_by_id(request.form["type_id"])
                flash("Type was deleted successfully")
            except:
                flash("It's impossible to delele the type because of existing of the reports with this type")
            return redirect(request.url)
        
        if "edit_type_button" in request.form:
            type_for_editing = ReportType.query.get(request.form["type_id"])
            type_for_editing.type = request.form["type_type"]
            type_for_editing.save()
            flash("Type edited successfully")
            return redirect(request.url)
        
        # Processing subtype
        if "add_new_subtype_button" in request.form:
            ReportSubtype.create(type=request.form["report_subtype_type"], subtype=request.form["new_subtype"])
            flash("New subtype was created successfully")
            return redirect(request.url)
        
        if "delete_subtype_button" in request.form:
            try:
                ReportSubtype.delete_by_id(request.form["subtype_id"])
                flash("Subtype was deleted successfully")
            except:
                flash("It's impossible to delele the subtype because of existing of the reports with this type")
            return redirect(request.url)
        
        if "edit_subtype_button" in request.form:
            subtype_for_editing = ReportSubtype.query.get(request.form["subtype_id"])
            subtype_for_editing.subtype = request.form["subtype_subtype"]
            subtype_for_editing.save()
            flash("Subtype edited successfully")
            return redirect(request.url)
        
        # Directory and folder name settings
        if "save_directory_button" in request.form:
            directory_path = request.form["directory_path"]
            AppConfig.set_config_value("UPLOAD_FOLDER_PATH", directory_path, current_user.id)
            flash("Directory path saved successfully", "success")
            return redirect(request.url)
        
        if "save_folder_name_button" in request.form:
            folder_name = request.form["folder_name"]
            AppConfig.set_config_value("UPLOAD_FOLDER_NAME", folder_name, current_user.id)
            flash("Folder name saved successfully", "success")
            return redirect(request.url)
        
        # Handling file upload
        if 'file' in request.files:
            file = request.files['file']
            result = file_uploader(file, "doc")
            if "successfully" in result:
                flash(result, 'success')
            else:
                flash(result, 'error')
            return redirect(request.url)
        
    return render_template('report_settings.html', 
                           title = page_title,
                           menu = menu,
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict,
                           upload_folder_path=upload_folder_path,
                           upload_folder_name=upload_folder_name 
                           )


