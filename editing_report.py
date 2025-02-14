# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from models import db, Report, Paragraph, Sentence, ParagraphType
from errors_processing import print_object_structure
from utils import get_max_index, check_main_sentences
from flask_security.decorators import auth_required
from logger import logger


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

@editing_report_bp.route('/edit_report', methods=["GET"])
@auth_required()
def edit_report():
    page_title = "Editing report"
    report_id = request.args.get("report_id")
    report = None

    report = Report.query.get(report_id)
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"Report not found or you don't have permission to edit it")
        return jsonify({"status": "error", "message": "Report not found or you don't have permission to edit it"}), 403

    report_paragraphs = sorted(report.report_to_paragraphs, key=lambda p: p.paragraph_index) if report else []
    for paragraph in report_paragraphs:
        paragraph.paragraph_to_sentences = sorted(paragraph.paragraph_to_sentences, key=lambda s: (s.index, s.weight))
        # Добавляем маркер для разделения предложений
        previous_index = None
        for sentence in paragraph.paragraph_to_sentences:
            sentence.show_separator = previous_index is not None and previous_index != sentence.index
            previous_index = sentence.index
    paragraph_types = ParagraphType.query.all()


    return render_template('edit_report.html', 
                           title=page_title, 
                           report=report,
                           report_paragraphs=report_paragraphs,
                           paragraph_types=paragraph_types
                           )


@editing_report_bp.route('/update_report', methods=['PUT'])
@auth_required()
def update_report():

    report_id = request.form.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"Report not found or profile data of this paragraph doesn't match with current profile")
        return jsonify({"status": "error", "message": "Report not found or profile data of this paragraph doesn't match with current profile"}), 403

    try:
        report.report_name = request.form.get("report_name")
        report.comment = request.form.get("comment")
        report_side_value = request.form.get("report_side")
        report.report_side = True if report_side_value == "true" else False
        report.save()
        return jsonify({"status": "success", "message": "Report updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        return jsonify({"status": "error", "message": f"Can't update report. Error code: {e}"}), 400



@editing_report_bp.route('/new_paragraph', methods=['POST'])
@auth_required()
def new_paragraph():
    
    report_id = request.json.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Report not found or it's profile data doesn't match with current profile"}), 403

    try:
        paragraph_index = get_max_index(Paragraph, "report_id", report_id, Paragraph.paragraph_index)
        
        default_paragraph_type = ParagraphType.query.filter_by(type_name="text").first()
        if not default_paragraph_type:
            return jsonify({"status": "error", "message": "Default paragraph type 'text' not found."}), 400
        
        Paragraph.create(
            report_id=report.id,
            paragraph_index=paragraph_index,
            paragraph="insert your text",
            type_paragraph_id=default_paragraph_type.id,
            paragraph_visible=True,
            title_paragraph=False,
            bold_paragraph=False,
            paragraph_weight=1,
            tags="",
            comment=None
        )
        return jsonify({"status": "success", "message": "Параграф успешно добавлен"}), 200
    except Exception as e:
        logger.error(f"Ошибка добавления параграфа: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка добавления параграфа, код ошибки: {e}"}), 400


@editing_report_bp.route('/edit_paragraph', methods=['POST'])
@auth_required()
def edit_paragraph():

    paragraph_id = request.form.get("paragraph_id")
    paragraph_for_edit = Paragraph.query.get(paragraph_id)

    if not paragraph_for_edit or paragraph_for_edit.paragraph_to_report.profile_id != g.current_profile.id:
        logger.error(f"Paragraph not found or data of this paragraph doesn't match with current profile")
        return jsonify({"status": "error", "message": "Paragraph not found or data of this paragraph doesn't match with current profile"}), 404

    try:
        # Получаем предлагаемый тип параграфа
        new_type_paragraph_id = int(request.form.get("paragraph_type"))
        current_report_id = paragraph_for_edit.report_id
        # Список типов параграфов, которые могут быть не уникальными
        allowed_paragraph_types = [ParagraphType.find_by_name("text"), ParagraphType.find_by_name("custom"), ParagraphType.find_by_name("title")]
        # Сначала проверим, если предлагаемый тип не 'text' и не 'custom' и не "title"
        if new_type_paragraph_id not in allowed_paragraph_types:
            # Проверим, существует ли уже параграф с таким типом для данного отчета
            existing_paragraph = Paragraph.query.filter_by(
                report_id=current_report_id,
                type_paragraph_id=new_type_paragraph_id
            ).first()

            if existing_paragraph and existing_paragraph.id != paragraph_for_edit.id:
                # Если существует другой параграф с этим типом, не обновляем тип
                # Сохраняем остальные изменения
                paragraph_for_edit.paragraph_index = request.form.get("paragraph_index")
                paragraph_for_edit.paragraph = request.form.get("paragraph_name")
                paragraph_for_edit.paragraph_visible = request.form.get("paragraph_visible") == "on"
                paragraph_for_edit.title_paragraph = request.form.get("title_paragraph") == "on"
                paragraph_for_edit.bold_paragraph = request.form.get("bold_paragraph") == "on"

                paragraph_for_edit.save()
                return jsonify({
                    "status": "success",
                    "message": "Paragraph updated successfully, but the type was not changed because a paragraph with this type already exists."
                }), 200

        # Если тип 'text', 'custom' или такого типа еще нет, сохраняем все изменения, включая тип
        paragraph_for_edit.paragraph_index = request.form.get("paragraph_index")
        paragraph_for_edit.paragraph = request.form.get("paragraph_name")
        paragraph_for_edit.paragraph_visible = request.form.get("paragraph_visible") == "on"
        paragraph_for_edit.title_paragraph = request.form.get("title_paragraph") == "on"
        paragraph_for_edit.bold_paragraph = request.form.get("bold_paragraph") == "on"
        paragraph_for_edit.type_paragraph_id = new_type_paragraph_id

        paragraph_for_edit.save()
        return jsonify({"status": "success", "message": "Paragraph updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating paragraph: {str(e)}")
        return jsonify({"status": "error", "message": f"Something went wrong. Error code: {e}"}), 400


@editing_report_bp.route('/delete_paragraph', methods=["DELETE"])
@auth_required()
def delete_paragraph():
    
    paragraph_id = request.json.get("paragraph_id")
    paragraph = Paragraph.query.get(paragraph_id)

    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Paragraph not found or data of this paragraph doesn't match with current profile"}), 404

    try:
        Paragraph.delete_by_id(paragraph_id)
        return jsonify({"status": "success", "message": "Paragraph deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting paragraph: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to delete paragraph. Error code: {e}"}), 400


# Массовое редактирование предложений
@editing_report_bp.route('/edit_sentences_bulk', methods=['POST'])
@auth_required()
def edit_sentences_bulk():
    logger.info("Логика массового редактирования предложений запущена ----------------------------")
    data = request.get_json()
    logger.info(f"Данные предложений из запроса массового редактирования: {data}")
    # Список для главных предложений сохраняю их 
    # чтобы внести изменения в главные предложения в конце, 
    # чтобы не перезаписывать логику в методе save()
    main_sentences = []

    try:
        for sentence_data in data:
            if sentence_data.get("sentence_id") == "new":
                # Логика для создания нового предложения
                logger.info("Создаю новое предложение")
                sentence_index = sentence_data.get("sentence_index")
                paragraph_id = sentence_data.get("add_sentence_paragraph")
                sentence_type = sentence_data.get("sentence_type")
                # Определяем тип предложения
                
                logger.info(f"Тип нового предложения - {sentence_type}")   
                
                try:
                    Sentence.create(
                        paragraph_id=paragraph_id,
                        index= 0 if sentence_type == "tail" else sentence_index,
                        weight=sentence_data.get("sentence_weight", 1),
                        sentence_type= sentence_type,
                        tags="",
                        comment=sentence_data.get("sentence_comment", ""),
                        sentence=sentence_data.get("sentence_sentence")
                    )
                except Exception as e:
                    logger.error(f"Error creating new sentence: {str(e)}")
                    return jsonify({"status": "error", "message": f"Не получилось создать новое предложение. Ошибка: {e}"}), 500
                    
            else:
                # Логика для обновления существующего предложения
                sentence_for_edit = Sentence.query.get(sentence_data["sentence_id"])
                if not sentence_for_edit:
                    logger.warning(f"Предложени с id {sentence_data['sentence_id']} не найдено")
                    continue
                if sentence_for_edit.sentence_type == "head":
                    main_sentences.append((sentence_for_edit, sentence_data))
                else:
                    # Обновляем неглавные предложения
                    sentence_for_edit.index = sentence_data.get("sentence_index")
                    sentence_for_edit.weight = sentence_data.get("sentence_weight")
                    sentence_for_edit.comment = sentence_data.get("sentence_comment")
                    sentence_for_edit.tag = ""
                    sentence_for_edit.sentence = sentence_data.get("sentence_sentence")
                    sentence_for_edit.save()
                    
        for sentence_for_edit, sentence_data in main_sentences:
            # Обновляем главные предложения
            # Сохраняю старый индекс, чтобы потом обновить все предложения с таким индексом
            logger.info(f"Обновляю главное предложение с id={sentence_for_edit.id}")
            old_index = sentence_for_edit.index
            sentence_for_edit.index = sentence_data["sentence_index"]
            sentence_for_edit.weight = sentence_data["sentence_weight"]
            sentence_for_edit.comment = sentence_data["sentence_comment"]
            sentence_for_edit.tag = ""
            sentence_for_edit.sentence = sentence_data["sentence_sentence"]
            sentence_for_edit.save(old_index=old_index)
            
        logger.info("Логика массового редактирования предложений успешно завершена ----------------------------")
        return jsonify(success=True, message="Все предложения успешно обновлены"), 200
    except Exception as e:
        logger.error(f"Error updating sentences: {str(e)}")
        return jsonify(success=False, message=f"Ошибка при обновлении предложений. Код ошибки: {e}"), 500
    
    
@editing_report_bp.route('/delete_sentence', methods=['DELETE'])
@auth_required()
def delete_sentence():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    sentence_id = data.get("sentence_id")
    sentence = Sentence.query.get(sentence_id)

    if not sentence:
        return jsonify({"status": "error", "message": "Sentence not found"}), 404

    if sentence.sentence_to_paragraph.paragraph_to_report.report_to_profile.id != g.current_profile.id:
        return jsonify({"status": "error", "message": "You don't have permission to delete this sentence"}), 403

    try:
        Sentence.delete_by_id(sentence_id)
        return jsonify({"status": "success", "message": "Sentence deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete sentence. Error code: {e}"}), 400


@editing_report_bp.route("change_sentence_type", methods=["POST"])
@auth_required()
def change_sentence_type():
    logger.info("Логика изменения типа предложения запущена----------------------------")
    if not request.is_json:
        return jsonify({"status": "error", "message": "Ошибочный формат данных в запросе"}), 400

    data = request.get_json()
    logger.debug(f"Данные предложения из запроса на изменения типа предложения: {data}")
    
    sentence_id = int(data.get("sentence_id"))
    sentence_type = data.get("sentence_type")  
    
    if not sentence_id or not sentence_type:
        logger.error("В запросе не хватает данных о id предложения или типе")
        return jsonify({"status": "error", "message": "В запросе не хватает данных о предложении или типе"}), 400
    
    if sentence_type == "body":
        try:
            sentence = Sentence.get_by_id(sentence_id)
            sentence.sentence_type = sentence_type
            sentence.save()
            logger.info("Логика изменения типа предложения (body) успешно завершена --------------------------------")
            return jsonify({"status": "success", "message": "Тип предложения изменен"}), 200
        except Exception as e:
            logger.error(f"Ошибка при изменении типа предложения: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при изменении типа предложения. Код ошибки: {e}"}), 400
    if sentence_type == "tail":
        try:
            sentence = Sentence.get_by_id(sentence_id)
            sentence.sentence_type = sentence_type
            sentence.index = 0
            sentence.save()
            logger.info("Логика изменения типа предложения (tail) успешно завершена --------------------------------")
            return jsonify({"status": "success", "message": "Тип предложения изменен"}), 200
        except Exception as e:
            logger.error(f"Ошибка при изменении типа предложения: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при изменении типа предложения. Код ошибки: {e}"}), 400
        
    paragraph_id = int(data.get("paragraph_id"))
    sentence_index = int(data.get("sentence_index"))
    
    if  not paragraph_id or sentence_index == None:
        logger.error("В запросе не хватает данных параграфа")
        return jsonify({"status": "error", "message": "В запросе не хватает данных о параграфе или индексе"}), 400

    try:
        sentences = Sentence.query.filter_by(
            paragraph_id = paragraph_id,
            index = sentence_index
        ).all()
        
        for sentence in sentences:
            logger.info(f"Обрабатываю предложение с id={sentence.id}")
            if sentence.id == sentence_id:
                logger.info(f"Это теперь главное предложение - {sentence.sentence}")
                sentence.sentence_type = "head"
            else:
                sentence.sentence_type = "body"
                
            sentence.save(old_index=sentence.index)
            
        logger.info("Логика изменения типа предложения успешно завершена --------------------------------")
        return jsonify({"status": "success", "message": "Тип предложения изменен"}), 200
    except Exception as e:
        logger.error(f"Ошибка при изменении типа предложения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при изменении типа предложения. Код ошибки: {e}"}), 400



@editing_report_bp.route('/check_report_for_excess_ishead', methods=['POST'])
@auth_required()
def check_report_for_excess_ishead():
    """
    Проверяет, есть ли в каждом наборе предложений с одинаковым index ровно одно главное предложение.
    Если index = 0, то в этом наборе не должно быть главных предложений.
    Возвращает отчет с информацией о проблемах в параграфах.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Неправильный формат данных"}), 400

    data = request.get_json()
    report_id = data.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Отчет не найден или не соответствует данному профилю"}), 404

    errors = check_main_sentences(report)
    
    return jsonify({"status": "success", "errors": errors}), 200