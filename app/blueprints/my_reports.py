# my_reports.py

from flask import Blueprint, render_template, request, jsonify, session
from flask_security import current_user
from collections import defaultdict
from app.models.models import db, Report, ReportType, Paragraph, AppConfig
from app.utils.logger import logger
from rapidfuzz import fuzz
from flask_security.decorators import auth_required


my_reports_bp = Blueprint('my_reports', __name__)

@my_reports_bp.route('/reports_list', methods=['GET'])
@auth_required()
def reports_list(): 
    profile_id = session.get("profile_id")
    user_id = current_user.id if current_user.is_authenticated else None
    # Initialize config variables
    all_reports_obj = Report.find_by_profile(profile_id, user_id=user_id)
    profile_reports = [Report.get_report_info(report.id) for report in all_reports_obj] if all_reports_obj else []
    return render_template("my_reports.html",
                           title="Список протоколов текущего профиля",
                           profile_reports=profile_reports,
                           )


@my_reports_bp.route("/delete_report/<int:report_id>", methods=["DELETE"])
@auth_required()
def delete_report(report_id):
    try:
        Report.delete_by_id(report_id)
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        return jsonify({"status": "error", "message": "Ошибка при удалении записи"}), 500
    logger.info(f"Протокол {report_id} успешно удален")
    return jsonify({"status": "success", "message": "Протокол успешно удален"}), 200



    
  