from flask import Blueprint, render_template, request, jsonify, session
from flask_security import current_user
from app.models.models import ReportTextSnapshot, ReportCategory
from app.utils.logger import logger
from flask_security.decorators import auth_required
from datetime import datetime

snapshots_bp = Blueprint("snapshots", __name__)

# Functions


# Routes

# Маршрут для просмотра сохраненных снапшотов отчетов (страница "Архив")
@snapshots_bp.route("/snapshots", methods=["GET"])
@auth_required()
def snapshots():
    logger.info(f"(Просмотр сохраненных снапшотов) ------------------------------------")
    logger.info(f"(Просмотр сохраненных снапшотов) 🚀 Начинаю обработку запроса на получение сохраненных снапшотов")
    
    user_id = current_user.id
    profile_id = session.get("profile_id")

    date_str = request.args.get("date")
    report_modality = request.args.get("report_modality")

    snapshots = []
    if date_str and report_modality:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            report_modality_int = int(report_modality)
            snapshots = ReportTextSnapshot.find_by_date_and_modality(user_id, date_obj, report_modality_int)
        except Exception as e:
            logger.error(f"[report_snapshots] ❌ Ошибка фильтрации снапшотов: {e}")


    return render_template(
        "snapshots.html",
        snapshots=snapshots,
    )
    
    
    
# Маршрут для фильтрации сохраненных снапшотов по дате и типу отчета (AJAX)
@snapshots_bp.route("/snapshots_json", methods=["POST"])
@auth_required()
def snapshots_json():
    logger.info(f"(snapshots_json) ------------------------------------")
    logger.info(f"(snapshots_json) 🚀 Получен запрос на фильтрацию снапшотов")
    try:
        data = request.get_json()
        date_str = data.get("date")
        report_modality = int(data.get("report_modality"))
        global_category = None
        if report_modality:
            logger.info(f"(snapshots_json) Выбран тип отчета: {report_modality}")
            modality= ReportCategory.get_by_id(report_modality)
            if modality and not modality.is_global:
                global_category = modality.global_id
            elif modality and modality.is_global:
                global_category = modality.id
            else:
                logger.warning(f"(snapshots_json) ❌ Тип отчета с id={report_modality} не найден")
        user_id = current_user.id

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        snapshots = ReportTextSnapshot.find_by_date_and_modality(user_id, date_obj, global_category)
        logger.info(f"(snapshots_json) ✅ Найдено {len(snapshots)} снапшотов для даты {date_str} и типа {report_modality}")

        data = render_template("partials/snapshot_results_snippet.html", snapshots=snapshots)
        logger.info(f"(snapshots_json) ✅ Данные для снапшотов успешно отрендерены")
        logger.info(f"(snapshots_json) ------------------------------------")
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error(f"(snapshots_json) ❌ Ошибка при фильтрации снапшотов: {e}")
        return jsonify({"status": "error", "message": "Ошибка при загрузке снапшотов"}), 500
    