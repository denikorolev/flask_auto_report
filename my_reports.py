# my_reports.py

from flask import Blueprint, render_template, request, g, jsonify
from collections import defaultdict
from models import db, Report, ReportType, Paragraph
from logger import logger
from flask_security.decorators import auth_required
from sentence_processing import calculate_similarity_rapidfuzz


my_reports_bp = Blueprint('my_reports', __name__)

@my_reports_bp.route('/reports_list', methods=['GET'])
@auth_required()
def reports_list(): 
    # Initialize config variables
    reports_type_with_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    profile_reports = Report.find_by_profile(g.current_profile.id)
                
    return render_template("my_reports.html", 
                           title="Список протоколов текущего профиля", 
                           reports_type_with_subtypes = reports_type_with_subtypes, 
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


# Маршрут для связывания протоколов друг с другом
@my_reports_bp.route("/auto_link_reports", methods=["POST"])
@auth_required()
def auto_link_reports():
    logger.info("Связывание протоколов начато")
    try:
        data = request.get_json()
        report_ids = data.get("reports", [])
        
        if len(report_ids) < 2:
            return jsonify({"status": "error", "message": "Выберите минимум два отчета для связывания"}), 400
        
        reports = [Report.get_by_id(report_id) for report_id in report_ids if Report.get_by_id(report_id).profile_id == g.current_profile.id]
        
        # Проверяем, что все отчеты одного типа
        report_type = reports[0].report_to_subtype.subtype_to_type.id
        for report in reports:
            if report.report_to_subtype.subtype_to_type.id != report_type:
                return jsonify({"status": "error", "message": "Протоколы разных типов нельзя связать"}), 400
        
        # Словарь для связей (по индексу и тексту)
        paragraph_groups = defaultdict(list)

        # Собираем параграфы
        for report in reports:
            paragraphs = Paragraph.query.filter_by(report_id=report.id).all()
            for paragraph in paragraphs:
                paragraph_groups[(paragraph.paragraph_index, paragraph.paragraph)].append(paragraph)

        linked_paragraphs = []
        unlinked_paragraphs = []

        # Обрабатываем группы параграфов
        for (index, text), paragraphs in paragraph_groups.items():
            if len(paragraphs) > 1:
                # Проверяем схожесть текстов параграфов
                base_text = text
                for paragraph in paragraphs[1:]:
                    similarity = calculate_similarity_rapidfuzz(base_text, paragraph.paragraph)
                    if similarity >= 98:  # Порог схожести
                        Paragraph.link_paragraphs(paragraphs[0].id, paragraph.id)
                        linked_paragraphs.append({
                            "index": index,
                            "paragraph": paragraph.paragraph,
                            "reports": [p.paragraph_to_report.report_name for p in paragraphs]
                        })
                    else:
                        unlinked_paragraphs.append({
                            "index": index,
                            "paragraph_id": paragraph.id,
                            "paragraph": paragraph.paragraph,
                            "report": paragraph.paragraph_to_report.report_name,
                            "report_id": paragraph.paragraph_to_report.id
                        })
            else:
                # Если параграф только один - он не связан
                unlinked_paragraphs.append({
                    "index": index,
                    "paragraph_id": paragraphs[0].id,
                    "paragraph": paragraphs[0].paragraph,
                    "report": paragraphs[0].paragraph_to_report.report_name,
                    "report_id": paragraphs[0].paragraph_to_report.id
                })
                
                
        
        logger.info(f"Протоколы успешно связаны")
        return jsonify({
            "status": "success",
            "message": "Протоколы успешно связаны",
            "linked_paragraphs": linked_paragraphs,
            "unlinked_paragraphs": unlinked_paragraphs
        }), 200

    except Exception as e:
        logger.error(f"Error linking reports: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при связывании протоколов: {str(e)}"}), 500
    
    
# Маршрут для ручного связывания параграфов
@my_reports_bp.route("/manual_link_paragraphs", methods=["POST"])
@auth_required()
def manual_link_paragraphs():
    try:
        set_of_paragraph_ids = request.get_json()
        logger.info(f"Полученные параграфы для связывания: {set_of_paragraph_ids}")
        for paragraph_ids in set_of_paragraph_ids:
            paragraphs_for_linking = []
            for paragraph_id in paragraph_ids:
                print(paragraph_id)
                paragraph_id = int(paragraph_id)
                paragraphs_for_linking.append(Paragraph.get_by_id(paragraph_id))
                
            logger.info(f"Параграфы для связывания: {[p.paragraph for p in paragraphs_for_linking]}")
            if len(paragraphs_for_linking) > 1:
                try:
                    for i in range(1, len(paragraphs_for_linking)):
                        Paragraph.link_paragraphs(paragraphs_for_linking[0].id, paragraphs_for_linking[i].id)
                    logger.info("Параграфы успешно связаны")
                    return jsonify({"status": "success", "message": "Параграфы успешно связаны"}), 200
                except Exception as e:
                    logger.error(f"Ошибка на стороне БД со связыванием парагрофов: {str(e)}")
                    return jsonify({"status": "error", "message": f"Ошибка при связывании параграфов: {str(e)}"}), 500
            else:
                logger.warning("Недостаточно параграфов для связывания")
                  
    except Exception as e:
        logger.error(f"Error linking paragraphs: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при связывании параграфов: {str(e)}"}), 500
    