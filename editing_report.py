# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from flask_security import current_user
from models import db, Report, Paragraph, HeadSentence, BodySentence, TailSentence, HeadSentenceGroup, TailSentenceGroup, BodySentenceGroup
from utils import get_max_index, check_unique_indices, normalize_paragraph_indices
from flask_security.decorators import auth_required
from logger import logger


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

@editing_report_bp.route('/edit_report', methods=["GET"])
@auth_required()
def edit_report():
    logger.info("(Страница редактирования протокола) 🚀 Начинаю получения данных для формирования страницы.")
    report_id = request.args.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"(Страница редактирования протокола) ❌ Протокол не найден или у вас нет прав на его редактирование")
        return jsonify({"status": "error", "message": "Протокол не найден или у вас нет прав на его редактирование"}), 403
    try:
        report_data = Report.get_report_info(report_id)
        report_paragraphs = Report.get_report_structure(report_id)
    except Exception as e:
        logger.error(f"(Страница редактирования протокола) ❌ Ошибка при получении данных протокола: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при получении данных протокола: {str(e)}"}), 500
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
    logger.info("(Страница редактирования параграфа) 🚀 Начинаю получения данных для формирования страницы.")
    paragraph_id = int(request.args.get("paragraph_id"))
    report_id = int(request.args.get("report_id"))
   
    paragraph = Paragraph.query.get(paragraph_id)
    head_group_links = HeadSentenceGroup.is_linked(paragraph.head_sentence_group_id)
    tail_group_links = TailSentenceGroup.is_linked(paragraph.tail_sentence_group_id)
    logger.debug(f"(Страница редактирования параграфа) Получены данные для редактирования параграфа: paragraph_id = {paragraph_id}, report_id = {report_id}")
    logger.debug(f"(Страница редактирования параграфа) Получены данные по наличию связей с предложениями: head_group_links = {head_group_links}, tail_group_links = {tail_group_links}")
    
    if not paragraph:
        logger.error(f"(Страница редактирования параграфа) ❌ Параграф не найден")
        return None  # Если параграфа нет, вернем None

    # Собираем head-предложения
    # Инициирую переменную для хранения главных предложений, на случай если у параграфа их нет
    head_sentences = []
    if paragraph.head_sentence_group:
        head_sentences = HeadSentenceGroup.get_group_sentences(paragraph.head_sentence_group_id) or []
        logger.debug(f"(Страница редактирования параграфа) Получены главные предложения: {head_sentences}")
        logger.info(f"(Страница редактирования параграфа) Начат сбор body-предложений для главных предложений")
        for sentence in head_sentences:
            # Проверяем, есть ли у главного предложения связанная группа body-предложений
            if sentence["body_sentence_group_id"] is not None:  
                body_sentences = BodySentenceGroup.get_group_sentences(sentence["body_sentence_group_id"])
            else:
                body_sentences = []

            sentence["body_sentences"] = body_sentences  # Добавляем body-предложения внутрь head-предложения
        logger.info(f"(Страница редактирования параграфа) Сбор body-предложений для главных предложений завершен")
    # Собираем tail-предложения
    logger.info(f"(Страница редактирования параграфа) Начат сбор tail-предложений")
    tail_sentences = TailSentenceGroup.get_group_sentences(paragraph.tail_sentence_group_id) or []
    logger.info(f"(Страница редактирования параграфа) Сбор tail-предложений завершен")
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
        "head_group_links": head_group_links or False,
        "tail_group_links": tail_group_links or False,
        "head_sentences": head_sentences,
        "tail_sentences": tail_sentences
    }
    
    if not paragraph:
        logger.error(f"(Страница редактирования параграфа) ❌ Параграф не найден")
        return jsonify({"status": "error", "message": "Параграф не найден."}), 403
    
    return render_template('edit_paragraph.html',
                            title=f"Редактирование параграфа {paragraph_data['paragraph']}",
                            paragraph=paragraph_data,
                            report_id=report_id
                            )


@editing_report_bp.route('/edit_head_sentence', methods=["GET"])
@auth_required()
def edit_head_sentence():
    logger.info("(Страница редактирования head предложений) 🚀 Начинаю получения данных для формирования страницы.")
    sentence_id = request.args.get("sentence_id")
    paragraph_id = request.args.get("paragraph_id")
    report_id = request.args.get("report_id")
    sentence = HeadSentence.query.get(sentence_id)
    body_group_links = BodySentenceGroup.is_linked(sentence.body_sentence_group_id)
    
    logger.debug(f"(Страница редактирования head предложений) Получены данные для редактирования head предложения: sentence_id = {sentence_id}, paragraph_id = {paragraph_id}, report_id = {report_id}")
    
    if not sentence:
        logger.error(f"(Страница редактирования head предложений) ❌ Предложение не найдено")
        return jsonify({"status": "error", "message": "Предложение не найдено"}), 404
    
    if sentence.body_sentence_group_id:
        body_sentences = BodySentenceGroup.get_group_sentences(sentence.body_sentence_group_id)
    else:
        body_sentences = []
        
    group_id = Paragraph.get_by_id(paragraph_id).head_sentence_group_id
    logger.info("(Страница редактирования head предложений) Собираю данные head предложения для формирования страницы")
    sentence_data = {
        "id": sentence.id,
        "index": HeadSentence.get_sentence_index_or_weight(sentence_id, group_id),
        "sentence": sentence.sentence,
        "tags": sentence.tags,
        "comment": sentence.comment,
        "body_sentence_group_id": sentence.body_sentence_group_id,
        "body_group_links": body_group_links or False,
        "body_sentences": body_sentences or []
    }
    logger.info("(Страница редактирования head предложений) ✅ Данные head предложения собраны")
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
    paragraph_id = int(data.get("paragraph_id"))
    if not updated_order or not paragraph_id:
        return jsonify({"status": "error", "message": "Нет данных для обновления"}), 400
    
    group_id = Paragraph.get_by_id(paragraph_id).head_sentence_group_id
    if not group_id:
        return jsonify({"status": "error", "message": "Группа главных предложений не найдена"}), 404

    try:
        for item in updated_order:
            sentence_id = int(item["sentence_id"])
            if sentence_id:
                HeadSentence.set_sentence_index_or_weight(sentence_id, group_id, new_index = item["new_index"])

        return jsonify({"status": "success", "message": "Порядок обновлен"}), 200

    except Exception as e:
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




@editing_report_bp.route('/add_new_paragraph', methods=['POST'])
@auth_required()
def add_paragraph():
    
    report_id = request.json.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Протокол не найден или не соответствует данному профилю"}), 403

    try:
        paragraph_index = get_max_index(Paragraph, "report_id", report_id, Paragraph.paragraph_index)
        
        new_paragraph = Paragraph.create(
            report_id=report.id,
            paragraph_index=paragraph_index,
            paragraph="Введите текст параграфа"
        )
        return jsonify({"status": "success", 
                        "message": "Параграф успешно добавлен",
                        "paragraph_index": paragraph_index,
                        "paragraph_id": new_paragraph.id,
                        "paragraph": "Введите текст параграфа"
                        }), 200
    except Exception as e:
        logger.error(f"Ошибка добавления параграфа: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка добавления параграфа, код ошибки: {e}"}), 400



@editing_report_bp.route("/add_new_sentence", methods=["POST"])
@auth_required()
def add_new_sentence():
    """Создаёт новое дополнительное предложение (BodySentence) для главного предложения."""
    logger.info("(Создание нового предложения) 🚀  Начат сбор данных для создания нового  предложения")
    data = request.get_json()
    
    sentence_data = {
            "user_id": current_user.id,
            "report_type_id": Report.get_report_type(int(data.get("report_id"))) or None,
            "sentence": "Введите текст предложения",
            "related_id": int(data.get("related_id")) or None,
            "sentence_index": data.get("sentence_index") or None
        }
    
    sentence_type = data.get("sentence_type")
    
    if sentence_type == "head":
        class_type = HeadSentence
    elif sentence_type == "body":
        class_type = BodySentence
    elif sentence_type == "tail":
        class_type = TailSentence
    else:
        logger.error(f"(Создание нового предложения) ❌ Неизвестный тип предложения")
        return jsonify({"status": "error", "message": "Неизвестный тип предложения"}), 400
    
    logger.info(f"(Создание нового предложения) Получены все необходимые данные для создания предложения {sentence_data}. Начато создание нового предложения")
    
    try:
        new_sentence, new_sentence_group = class_type.create(**sentence_data)
        logger.info(f"(Создание нового предложения) ✅ Успешно создано новое {sentence_type} предложение с id={new_sentence.id}")
        
        return jsonify({
            "status": "success",
            "id": new_sentence.id,
            "weight": class_type.get_sentence_index_or_weight(new_sentence.id, new_sentence_group.id),
            "sentence": new_sentence.sentence,
            "tags": new_sentence.tags,
            "comment": new_sentence.comment
        }), 201

    except Exception as e:
        logger.error(f"(Создание нового предложения) ❌ Ошибка при создании нового предложения: {e}")
        return jsonify({"status": "error", "message": f"Ошибка при создании нового предложения: {e}"}), 500
     

@editing_report_bp.route('/delete_paragraph', methods=["DELETE"])
@auth_required()
def delete_paragraph():
    logger.info("Логика удаления параграфа запущена ----------------------------")
    paragraph_id = request.json.get("paragraph_id")
    paragraph = Paragraph.get_by_id(paragraph_id)
    report_id = paragraph.report_id
    head_sentence_group = paragraph.head_sentence_group
    tail_sentence_group = paragraph.tail_sentence_group

    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Параграф не найден или не соответствует профилю"}), 404
    
    try:
        if tail_sentence_group:
            logger.info(f"У параграфа есть группа tail предложений")
            tail_sentence_group_count = TailSentenceGroup.is_linked(tail_sentence_group.id)
            if  tail_sentence_group_count > 1:
                logger.info(f"Tail предложения параграфа связаны с другими протоколами. Просто удаляю связь с текущим параграфом")
                TailSentenceGroup.unlink_groupe(tail_sentence_group.id, paragraph_id)
                logger.info(f"Связь с параграфом успешно удалена")
                pass
            else:
                logger.info(f"Параграф связан только с текущим протоколом. Удаляю группу tail предложений")
                TailSentenceGroup.delete_group(tail_sentence_group.id, paragraph_id)
                logger.info(f"Группа tail предложений успешно удалена")
                pass
        if head_sentence_group:
            logger.info(f"У параграфа есть группа head предложений")
            head_sentence_group_count = HeadSentenceGroup.is_linked(head_sentence_group.id)
            if head_sentence_group_count > 1:
                logger.info(f"Head предложения параграфа связаны с другими протоколами. Просто удаляю связь с текущим параграфом")
                HeadSentenceGroup.unlink_groupe(head_sentence_group.id, paragraph_id)
                logger.info(f"Связь с параграфом успешно удалена")
                pass
            else:
                logger.info(f"Параграф связан только с текущим протоколом. Удаляю группу head предложений")
                HeadSentenceGroup.delete_group(head_sentence_group.id, paragraph_id)
                logger.info(f"Группа head предложений успешно удалена")
                pass
        paragraph.delete()
        logger.info(f"Параграф успешно удален")
        try:
            normalize_paragraph_indices(report_id)
        except Exception as e:
            logger.error(f"Ошибка при нормализации индексов параграфов: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при ренормализации индексов параграфов: {e}"}), 500
        
            
        logger.info("Логика удаления параграфа успешно завершена ----------------------------")
        return jsonify({"status": "success", "message": "Параграф успешно удален"}), 200
    except Exception as e:
        logger.error(f"Error deleting paragraph: {str(e)}")
        return jsonify({"status": "error", "message": f"Не удалось удалить параграф. Ошибка: {e}"}), 400


    
@editing_report_bp.route('/delete_sentence', methods=['DELETE'])
@auth_required()
def delete_sentence():
    """Удаляет предложение или отвязывает его от группы."""
    data = request.get_json()
    sentence_id = data.get("sentence_id")
    sentence_type = data.get("sentence_type")
    related_id = data.get("related_id") 
    logger.info(f"Получены данные для удаления предложения: {data}")
   
    if not sentence_id or not related_id or not sentence_type:
        logger.error(f"Отсутствуют необходимые данные для удаления предложения")
        return jsonify({"status": "error", "message": "Отсутствуют необходимые данные для удаления предложения"}), 400
    
    group_id = 0
    if sentence_type == "body":
        group_id = HeadSentence.query.get(related_id).body_sentence_group_id
        logger.info(f"Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            BodySentence.delete_sentence(sentence_id, group_id)
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
    
    elif sentence_type == "tail":
        group_id = Paragraph.query.get(related_id).tail_sentence_group_id
        logger.info(f"Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            TailSentence.delete_sentence(sentence_id, group_id)
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
        
    elif sentence_type == "head":
        group_id = Paragraph.query.get(related_id).head_sentence_group_id
        logger.info(f"Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            HeadSentence.delete_sentence(sentence_id, group_id)
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
        
    else:
        logger.error(f"Неизвестный тип предложения: {sentence_type}")
        return jsonify({"status": "error", "message": "Неизвестный тип предложения"}), 400
        
        
        
        
    

    
    
    
    
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


