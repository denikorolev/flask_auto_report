# my_reports.py
#v0.1.0

from flask import Blueprint, render_template, request, redirect, url_for, current_app, g
from flask_login import login_required
from models import Report, ReportType
from flask_security.decorators import auth_required

my_reports_bp = Blueprint('my_reports', __name__)

@my_reports_bp.route('/reports_list', methods=['POST', 'GET'])
@auth_required()
def reports_list(): 
    page_title = "List of the reports"
    # Initialize config variables
    menu = current_app.config['MENU']
    reports_type_with_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    profile_reports = Report.find_by_profile(g.current_profile.id)
    
    if request.method == "POST":
        # 'Delete' button logic (button 'edit' just redirect to new page)
        if "report_delete" in request.form:
            try:
                Report.delete_by_id(request.form["report_id"])
            except Exception as e:
                print(f"Report not found. error code: {e}", "error")
            return redirect(url_for("my_reports.reports_list"))
                
    return render_template("my_reports.html", 
                           title=page_title, 
                           menu=menu,
                           reports_type_with_subtypes = reports_type_with_subtypes, 
                           profile_reports=profile_reports,
                           )
