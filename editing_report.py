# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from flask_security import current_user
from models import db, Report, Paragraph, Sentence, HeadSentence, BodySentence, TailSentence, HeadSentenceGroup, TailSentenceGroup, BodySentenceGroup
from utils import get_max_index, check_unique_indices
from flask_security.decorators import auth_required
from logger import logger


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

@editing_report_bp.route('/edit_report', methods=["GET"])
@auth_required()
def edit_report():
    report_id = request.args.get("report_id")
    profile_id = g.current_profile.id

    report = Report.query.get(report_id)
    if not report or report.profile_id != profile_id:
        logger.error(f"Протокол не найден или у вас нет прав на его редактирование")
        return jsonify({"status": "error", "message": "Протокол не найден или у вас нет прав на его редактирование"}), 403
    report_data = Report.get_report_info(report_id, profile_id)
    report_paragraphs = Report.get_report_structure(report_id, profile_id)
    
    # делаю выборку типов параграфов
    paragraph_types = current_app.config["PARAGRAPH_TYPE_LIST"]


    return render_template('edit_report.html', 
                           title=f"Редактирование протокола {report.report_name}", 
                           report_data=report_data,
                           report_paragraphs=report_paragraphs,
                           paragraph_types=paragraph_types
                           )



@editing_report_bp.route('/edit_paragraph', methods=["GET"])
@auth_required()
def edit_paragraph():
    paragraph_id = int(request.args.get("paragraph_id"))
    report_id = int(request.args.get("report_id"))
   
    paragraph = Paragraph.query.get(paragraph_id)
    head_group_links = HeadSentenceGroup.is_linked(paragraph.head_sentence_group_id)
    tail_group_links = TailSentenceGroup.is_linked(paragraph.tail_sentence_group_id)
    if not paragraph:
        return None  # Если параграфа нет, вернем None

    # Собираем head-предложения
    head_sentences = []
    if paragraph.head_sentence_group:
        for sentence in sorted(paragraph.head_sentence_group.head_sentences, key=lambda s: s.sentence_index):
            body_sentences = False
            print(sentence.body_sentence_group_id)
            if sentence.body_sentence_group_id:
                body_sentences = True
            head_sentences.append({
                "id": sentence.id,
                "index": sentence.sentence_index,
                "sentence": sentence.sentence,
                "tags": sentence.tags,
                "comment": sentence.comment,
                "body_sentences": body_sentences
            })

    # Собираем tail-предложения
    tail_sentences = []
    if paragraph.tail_sentence_group:
        tail_sentences = [
            {
                "id": sentence.id,
                "weight": sentence.sentence_weight,
                "sentence": sentence.sentence,
                "tags": sentence.tags,
                "comment": sentence.comment
            }
            for sentence in sorted(paragraph.tail_sentence_group.tail_sentences, key=lambda s: s.sentence_weight)
        ]

    # Формируем итоговые данные параграфа
    paragraph_data = {
        "id": paragraph.id,
        "paragraph_index": paragraph.paragraph_index,
        "paragraph": paragraph.paragraph,
        "paragraph_visible": paragraph.paragraph_visible,
        "title_paragraph": paragraph.title_paragraph,
        "bold_paragraph": paragraph.bold_paragraph,
        "paragraph_type": paragraph.paragraph_type,
        "paragraph_comment": paragraph.comment,
        "paragraph_weight": paragraph.paragraph_weight,
        "tags": paragraph.tags,
        "head_group_links": head_group_links,
        "tail_group_links": tail_group_links,
        "head_sentences": head_sentences,
        "tail_sentences": tail_sentences
    }
    
    if not paragraph:
        logger.error(f"Параграф не найден.")
        return jsonify({"status": "error", "message": "Параграф не найден."}), 403
    
    return render_template('edit_paragraph.html',
                            title=f"Редактирование параграфа {paragraph_data['paragraph']}",
                            paragraph=paragraph_data,
                            report_id=report_id
                            )


@editing_report_bp.route('/edit_head_sentence', methods=["GET"])
@auth_required()
def edit_head_sentence():
    logger.info("Запускается логика формирования страницы для редактирования главного предложения")
    sentence_id = request.args.get("sentence_id")
    paragraph_id = request.args.get("paragraph_id")
    report_id = request.args.get("report_id")
    sentence = HeadSentence.query.get(sentence_id)
    body_group_links = BodySentenceGroup.is_linked(sentence.body_sentence_group_id)
    logger.debug(f"Получены данные для редактирования главного предложения: {sentence_id}, {paragraph_id}, {report_id}")
    logger.debug(f"Данные главного предложения: {sentence.sentence}")
    if not sentence:
        logger.error(f"Предложение не найдено")
        return jsonify({"status": "error", "message": "Предложение не найдено"}), 404
    body_sentences = []
    if sentence.body_sentence_group_id:
        logger.info("Собираю дополнительные предложения")
        body_sentences = [
            {
                "id": body_sentence.id,
                "weight": body_sentence.sentence_weight,
                "sentence": body_sentence.sentence,
                "tags": body_sentence.tags,
                "comment": body_sentence.comment
            }
            for body_sentence in sorted(sentence.body_sentence_group.body_sentences, key=lambda s: s.sentence_weight)
        ]
    logger.info("Формирую данные для главного предложения")
    sentence_data = {
        "id": sentence.id,
        "index": sentence.sentence_index,
        "sentence": sentence.sentence,
        "tags": sentence.tags,
        "comment": sentence.comment,
        "body_sentence_group_id": sentence.body_sentence_group_id,
        "body_group_links": body_group_links or False,
        "body_sentences": body_sentences or []
    }
    return render_template('edit_head_sentence.html',
                           title=f"Редактирование главного предложения: {sentence_data['sentence']}",
                           head_sentence=sentence_data,
                           paragraph_id=paragraph_id,
                           report_id=report_id
                           )


@editing_report_bp.route('/update_paragraph_order', methods=["POST"])
@auth_required()
def update_paragraph_order():
    data = request.json.get("paragraphs", [])
    
    try:
        for item in data:
            paragraph = Paragraph.get_by_id(item["id"])
            if paragraph:
                paragraph.paragraph_index = item["index"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Порядок параграфов успешно обновлен"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Ошибка обновления порядка параграфов: {e}"}), 500


@editing_report_bp.route("/update_head_sentence_order", methods=["POST"])
@auth_required()
def update_head_sentence_order():
    """
    Обновляет индексы главных предложений в параграфе после их перетаскивания.
    """
    data = request.json
    updated_order = data.get("updated_order")

    if not updated_order:
        return jsonify({"status": "error", "message": "Нет данных для обновления"}), 400

    try:
        for item in updated_order:
            sentence = HeadSentence.query.get(item["sentence_id"])
            if sentence:
                sentence.sentence_index = item["new_index"]

        db.session.commit()
        return jsonify({"status": "success", "message": "Порядок обновлен"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Ошибка сохранения: {e}"}), 500



@editing_report_bp.route('/update_report', methods=['PUT'])
@auth_required()
def update_report():

    report_id = request.form.get("report_id")
    report = Report.query.get(report_id)
    
    report_name = request.form.get("report_name")
    if not report_name:
        logger.error(f"Не указано название протокола")
        return jsonify({"status": "error", "message": "Не указано название протокола"}), 400
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"Такой протокол в данном профиле не найден")
        return jsonify({"status": "error", "message": "Такой протокол в данном профиле не найден"}), 403

    try:
        report.report_name = report_name
        report.comment = request.form.get("comment")
        report.report_side = True if request.form.get("report_side") == "true" else False
        report.save()
        return jsonify({"status": "success", "message": "Данные протокола успешно обновлены"}), 200
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        return jsonify({"status": "error", "message": f"Не удалось обновить данные протокола. Ошибка: {e}"}), 400





@editing_report_bp.route('/new_paragraph', methods=['POST'])
@auth_required()
def new_paragraph():
    
    report_id = request.json.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Report not found or it's profile data doesn't match with current profile"}), 403

    try:
        paragraph_index = get_max_index(Paragraph, "report_id", report_id, Paragraph.paragraph_index)
        
        Paragraph.create(
            report_id=report.id,
            paragraph_index=paragraph_index,
            paragraph="Введите текст параграфа"
        )
        return jsonify({"status": "success", "message": "Параграф успешно добавлен"}), 200
    except Exception as e:
        logger.error(f"Ошибка добавления параграфа: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка добавления параграфа, код ошибки: {e}"}), 400


@editing_report_bp.route("/add_new_body_sentence", methods=["POST"])
@auth_required()
def add_new_body_sentence():
    """Создаёт новое дополнительное предложение (BodySentence) для главного предложения."""
    data = request.get_json()
    head_sentence_id = data.get("head_sentence_id")
    report_id = data.get("report_id") 
    logger.info(f"Получены данные для создания нового дополнительного предложения: {data}")

    if not head_sentence_id or not report_id:
        return jsonify({"status": "error", "message": "Отсутствует head_sentence_id или report_id"}), 400

    report_type_id = Report.get_report_type(report_id)

    try:
        new_body_sentence, _ = BodySentence.create(
            user_id=current_user.id,
            report_type_id=report_type_id,  
            sentence="Введите текст предложения", 
            related_id=head_sentence_id
        )
        if new_body_sentence:
            logger.info(f"Успешно создано новое дополнительное предложение с id={new_body_sentence.id}")
        return jsonify({
            "status": "success",
            "id": new_body_sentence.id,
            "weight": new_body_sentence.sentence_weight,
            "sentence": new_body_sentence.sentence,
            "tags": new_body_sentence.tags,
            "comment": new_body_sentence.comment
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка при создании предложения: {e}"}), 500



@editing_report_bp.route('/delete_paragraph', methods=["DELETE"])
@auth_required()
def delete_paragraph():
    logger.info("Логика удаления параграфа запущена ----------------------------")
    paragraph_id = request.json.get("paragraph_id")
    paragraph = Paragraph.query.get(paragraph_id)

    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Параграф не найден или не соответствует профилю"}), 404
    try:
        Paragraph.delete_by_id(paragraph_id)
        logger.info("Логика удаления параграфа успешно завершена ----------------------------")
        return jsonify({"status": "success", "message": "Параграф успешно удален"}), 200
    except Exception as e:
        logger.error(f"Error deleting paragraph: {str(e)}")
        return jsonify({"status": "error", "message": f"Не удалось удалить параграф. Ошибка: {e}"}), 400



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
                paragraph_id = sentence_data.get("paragraph_id")
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
    
    
    
# проверяет уникальность индексов параграфов и главных предложений
@editing_report_bp.route('/report_checkers', methods=['POST'])
@auth_required()
def report_checkers():
    data = request.get_json()
    logger.debug(f"Получены данные для запуска проверок: {data}")
    report_id = data.get("report_id")
    if not report_id:
        logger.error(f"Не указан id отчета")
        return jsonify({"status": "error", "message": "Отчет не найден"}), 404
    paragraphs_by_type = Paragraph.get_report_paragraphs(report_id)
    try:
        check_unique_indices(paragraphs_by_type)
        return jsonify({"status": "success", "message": "Индексы параграфов и главных предложений уникальны"}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": f"В протоколе присутствует ошибка: {str(e)}"}), 400


