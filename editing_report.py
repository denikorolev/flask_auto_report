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
    logger.info("(Страница редактирования протокола /edit_report) 🚀 Начинаю получения данных для формирования страницы.")
    report_id = request.args.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"(Страница редактирования протокола /edit_report) ❌ Протокол не найден или у вас нет прав на его редактирование")
        return jsonify({"status": "error", "message": "Протокол не найден или у вас нет прав на его редактирование"}), 403
    try:
        report_data = Report.get_report_info(report_id)
        report_paragraphs = Report.get_report_paragraphs(report_id)
        logger.info(f"(Страница редактирования протокола /edit_report) ✅ Получены данные протокола.")
    except Exception as e:
        logger.error(f"(Страница редактирования протокола /edit_report) ❌ Ошибка при получении данных протокола: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при получении данных протокола: {str(e)}"}), 500
    # делаю выборку типов параграфов


    return render_template('edit_report.html', 
                           title=f"Редактирование протокола {report.report_name}", 
                           report_data=report_data,
                           report_paragraphs=report_paragraphs,
                           )



@editing_report_bp.route('/edit_paragraph', methods=["GET"])
@auth_required()
def edit_paragraph():
    logger.info("(Страница редактирования параграфа /edit_paragraph) 🚀 Начинаю получения данных для формирования страницы.")
    paragraph_id = int(request.args.get("paragraph_id"))
    report_id = int(request.args.get("report_id"))
   
    paragraph_data = Paragraph.get_paragraph_data(paragraph_id)
    logger.info(f"(Страница редактирования параграфа /edit_paragraph) Получены данные параграфа. Формирую страницу.")
    
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
    
    group_id = Paragraph.get_by_id(paragraph_id).head_sentence_group_id
    if not group_id:
        logger.error("(Страница редактирования head предложений) ❌ Группа head предложений не найдена")
        return jsonify({"status": "error", "message": "Группа head предложений не найдена"}), 404
    
    sentence_data = HeadSentence.get_sentence_data(sentence_id, group_id)
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



@editing_report_bp.route('/update_report', methods=["PATCH"])
@auth_required()
def update_report():
    logger.info("(Обновление протокола) 🚀 Начато обновление данных протокола")
    data = request.json
    report_id = data.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"(Обновление протокола) ❌ Протокол не найден или не соответствует профилю")
        return jsonify({"status": "error", "message": "Протокол не найден или не соответствует профилю"}), 403
    
    new_report_data = {
        "report_name": data.get("report_name"),
        "comment": data.get("report_comment"),
        "report_side": data.get("report_side") == "True"
    }
    logger.info(f"(Обновление протокола) Получены данные для обновления протокола: {new_report_data}")

    try:
        report.update(**new_report_data)
        logger.info(f"(Обновление протокола) ✅ Данные протокола успешно обновлены")
        return jsonify({"status": "success", "message": "Данные протокола успешно обновлены"}), 200
    except Exception as e:
        logger.error(f"(Обновление протокола) ❌ Ошибка при обновлении протокола: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обновлении протокола: {str(e)}"}), 500
        


@editing_report_bp.route('/update_paragraph_text', methods=["PATCH"])
@auth_required()
def update_paragraph_text():
    logger.info("(Обновление текста параграфа) 🚀 Начато обновление текста параграфа")
    data = request.json
    paragraph_id = data.get("paragraph_id")
    paragraph = Paragraph.query.get(paragraph_id)
    
    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        logger.error(f"(Обновление текста параграфа) ❌ Параграф не найден или не соответствует профилю")
        return jsonify({"status": "error", "message": "Параграф не найден или не соответствует профилю"}), 403
    
    new_paragraph_text = data.get("paragraph_text")
    logger.info(f"(Обновление текста параграфа) Получены данные для обновления текста параграфа: {new_paragraph_text}")
    
    try:
        paragraph.update(paragraph=new_paragraph_text)
        logger.info(f"(Обновление текста параграфа) ✅ Текст параграфа успешно обновлен")
        return jsonify({"status": "success", "message": "Текст параграфа успешно обновлен"}), 200
    except Exception as e:
        logger.error(f"(Обновление текста параграфа) ❌ Ошибка при обновлении текста параграфа: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обновлении текста параграфа: {str(e)}"}), 500


@editing_report_bp.route('/update_paragraph_flags', methods=["PATCH"])
@auth_required()
def update_paragraph_flags():
    logger.info("(Обновление флагов параграфа) ------------------------------------------------")
    logger.info("(Обновление флагов параграфа) 🚀 Запрос на обновление флагов параграфа получен")
    
    data = request.json
    paragraph_id = data.pop("paragraph_id", None)
    if not paragraph_id:
        logger.error("(Обновление флагов параграфа) ❌ Не указан ID параграфа")
        return jsonify({"status": "error", "message": "Не указан ID параграфа"}), 400

    # Проверяем, существует ли параграф и принадлежит ли он текущему профилю
    paragraph = Paragraph.query.get(paragraph_id)
    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        logger.error("(Обновление флагов параграфа) ❌ Параграф не найден или не принадлежит профилю")
        return jsonify({"status": "error", "message": "Параграф не найден или не принадлежит вашему профилю"}), 403
    
    logger.info(f"(Обновление флагов параграфа) Получены все необходимые данные для обновления флагов параграфа ID= {paragraph_id}. Начинаю обновление флагов")
    # Обновляем данные
    try:
        paragraph.update(**data)

        db.session.commit()
        logger.info(f"(Обновление флагов параграфа) ✅ Флаги параграфа ID {paragraph_id} успешно обновлены")
        logger.info(f"(Обновление флагов параграфа) ------------------------------------------------------")

        return jsonify({"status": "success", "message": "Флаги параграфа успешно обновлены"}), 200

    except Exception as e:
        logger.error(f"(Обновление флагов параграфа) ❌ Ошибка при обновлении: {str(e)}")
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Ошибка при обновлении флагов параграфа: {str(e)}"}), 500



@editing_report_bp.route('/update_sentence_text', methods=["PATCH"])
@auth_required()
def update_sentence_text():
    """Обновляет текст head, body или tail предложения."""
    logger.info("(Обновление текста предложения /update_sentence_text) 🚀 Начато обновление текста предложения")
    data = request.json
    sentence_id = data.get("sentence_id")
    sentence_text = data.get("sentence_text")
    sentence_type = data.get("sentence_type")
    group_id = data.get("group_id")
    related_id = data.get("related_id")
    hard_edit = data.get("hard_edit") == "True"

    # Проверка типа предложения
    if sentence_type not in ["head", "body", "tail"]:
        logger.error("(Обновление текста предложения /update_sentence_text) ❌ Некорректный тип предложения")
        return jsonify({"status": "error", "message": "Некорректный тип предложения."}), 400

    # Выбор модели по типу
    sentence_class = {"head": HeadSentence, "body": BodySentence, "tail": TailSentence}.get(sentence_type)
    logger.info(f"(Обновление текста предложения /update_sentence_text)(тип предложения {sentence_class}) Получены данные для обновления текста предложения: {data}")
    try:
        sentence_class.edit_sentence(sentence_id=sentence_id,
                                     group_id=group_id,
                                     related_id=related_id,
                                     new_text=sentence_text,
                                     hard_edit=hard_edit
                                     )
        logger.info(f"(Обновление текста предложения /update_sentence_text) ✅ Текст предложения успешно обновлен")
        return jsonify({"status": "success", "message": "Текст предложения успешно обновлен."}), 200
    except Exception as e:
        logger.error(f"(Обновление текста предложения /update_sentence_text) ❌ Ошибка при обновлении текста предложения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка обновления текста: {str(e)}"}), 500




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
    paragraphs_by_type = Report.get_report_paragraphs(report_id)
    try:
        check_unique_indices(paragraphs_by_type)
        return jsonify({"status": "success", "message": "Индексы параграфов и главных предложений уникальны"}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": f"В протоколе присутствует ошибка: {str(e)}"}), 400


