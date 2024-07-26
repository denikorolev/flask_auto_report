# report_settings.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from models import Report, ReportType, ReportSubtype, ReportParagraph, Sentence

report_settings_bp = Blueprint('report_settings', __name__)

# Functions

# Access configuration parameters
def init_app(app):
    menu = app.config['MENU']
    return menu

# Routs

@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    page_title = "Report settings"
    menu = init_app(current_app)
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
        
    return render_template('report_settings.html', 
                           title = page_title,
                           menu = menu,
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict 
                           )
