# my_reports.py
#v0.1.0

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Report, ReportType, ReportSubtype

my_reports_bp = Blueprint('my_reports', __name__)

# Access configuration parameters
def init_app(app):
    menu = app.config['MENU']
    return menu

@my_reports_bp.route('/reports_list', methods=['POST', 'GET'])
@login_required
def reports_list(): 
    page_title = "List of the reports"
    # Initialize config variables
    menu = init_app(current_app)
    # Geting report types and subtypes 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype, "subtype_type_name": rst.report_type_rel.type}
        for rst in report_subtypes
    ]
    # All reports of current user with load of linked records (types and subtypes) by method in class
    user_reports_rel = Report.query.filter_by(userid=current_user.id).all()
    
    
    if request.method == "POST":
        # 'Delete' button logic (button 'edit' just redirect to new page)
        if "report_delete" in request.form:
            try:
                Report.delete_by_id(request.form["report_id"])
                flash("Report deleted successfully", "success")
            except Exception as e:
                flash(f"Report not found. error code: {e}", "error")
            return redirect(url_for("my_reports.reports_list"))
                
    return render_template("my_reports.html", 
                           title=page_title, 
                           menu=menu,
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict, 
                           user_reports_rel=user_reports_rel,
                           )
