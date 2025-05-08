# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from flask_security import current_user
from models import db, User, Report, Paragraph, HeadSentence, BodySentence, TailSentence, HeadSentenceGroup, TailSentenceGroup, BodySentenceGroup, ReportShare
from utils import get_max_index, check_unique_indices, normalize_paragraph_indices
from flask_security.decorators import auth_required
from decorators import require_role_rank
from logger import logger
from openai_api import gramma_correction_ai


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

# Маршрут для запуска страницы редактирования протокола
@editing_report_bp.route('/edit_report', methods=["GET"])
@auth_required()
def edit_report():
    logger.info("(Страница редактирования протокола /edit_report) ------------------------------------------------")
    logger.info("(Страница редактирования протокола /edit_report) 🚀 Начинаю получения данных для формирования страницы.")
    report_id = request.args.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"(Страница редактирования протокола /edit_report) ❌ Протокол не найден или у вас нет прав на его редактирование")
        return jsonify({"status": "error", "message": "Протокол не найден или у вас нет прав на его редактирование"}), 403
    try:
        report_data = Report.get_report_info(report_id)
        report_paragraphs = Report.get_report_paragraphs(report_id)
        logger.info(f"(Страница редактирования протокола /edit_report) ------------------------------------------------")
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


# Маршрут для запуска страницы редактирования параграфа
@editing_report_bp.route('/edit_paragraph', methods=["GET"])
@auth_required()
def edit_paragraph():
    logger.info("(Страница редактирования параграфа /edit_paragraph) ------------------------------------------------")
    logger.info("(Страница редактирования параграфа /edit_paragraph) 🚀 Начинаю получения данных для формирования страницы.")
    paragraph_id = int(request.args.get("paragraph_id"))
    report_id = int(request.args.get("report_id"))
    report_type = Report.get_report_type(report_id)
   
    paragraph_data = Paragraph.get_paragraph_data(paragraph_id)
    logger.info(f"(Страница редактирования параграфа /edit_paragraph) ----------------------------------------------")
    logger.info(f"(Страница редактирования параграфа /edit_paragraph) ✅ Получены данные параграфа. Формирую страницу.")
    
    return render_template('edit_paragraph.html',
                            title=f"Редактирование параграфа {paragraph_data['paragraph']}",
                            paragraph=paragraph_data,
                            report_id=report_id,
                            report_type=report_type,
                            )


# Маршрут для запуска страницы редактирования главного предложения
@editing_report_bp.route('/edit_head_sentence', methods=["GET"])
@auth_required()
def edit_head_sentence():
    logger.info("(Страница редактирования head предложений) ------------------------------------------------")
    logger.info("(Страница редактирования head предложений) 🚀 Начинаю получения данных для формирования страницы.")
    
    sentence_id = request.args.get("sentence_id")
    paragraph_id = request.args.get("paragraph_id")
    report_id = request.args.get("report_id")
    report_type = Report.get_report_type(report_id)
    
    group_id = Paragraph.get_by_id(paragraph_id).head_sentence_group_id
    if not group_id:
        logger.error("(Страница редактирования head предложений) ❌ Группа head предложений не найдена")
        return jsonify({"status": "error", "message": "Группа head предложений не найдена"}), 404
    
    sentence_data = HeadSentence.get_sentence_data(sentence_id, group_id)
    logger.info("(Страница редактирования head предложений) ----------------------------------------------")
    logger.info("(Страница редактирования head предложений) ✅ Данные head предложения собраны")
    
    return render_template('edit_head_sentence.html',
                           title=f"Редактирование главного предложения: {sentence_data['sentence']}",
                           head_sentence=sentence_data,
                           paragraph_id=paragraph_id,
                           report_id=report_id,
                           report_type=report_type,
                           )


@editing_report_bp.route('/update_paragraph_order', methods=["POST"])
@auth_required()
def update_paragraph_order():
    logger.info("(Обновление порядка параграфов) ------------------------------------------------")
    logger.info("(Обновление порядка параграфов) 🚀 Начато обновление порядка параграфов")
    data = request.json.get("paragraphs", [])
    
    try:
        for item in data:
            paragraph = Paragraph.get_by_id(item["id"])
            if paragraph:
                paragraph.paragraph_index = item["index"]
        
        db.session.commit()
        logger.info("(Обновление порядка параграфов) ✅ Порядок параграфов успешно обновлен")
        logger.info("(Обновление порядка параграфов) ----------------------------------------------")
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
    logger.info("(Обновление порядка главных предложений) ------------------------------------------------")
    logger.info("(Обновление порядка главных предложений) 🚀 Начато обновление порядка главных предложений")
    data = request.json
    updated_order = data.get("updated_order")
    paragraph_id = int(data.get("paragraph_id"))
    if not updated_order or not paragraph_id:
        logger.error("(Обновление порядка главных предложений) ❌ Нет данных для обновления")
        return jsonify({"status": "error", "message": "Нет данных для обновления"}), 400
    
    group_id = Paragraph.get_by_id(paragraph_id).head_sentence_group_id
    if not group_id:
        logger.error("(Обновление порядка главных предложений) ❌ Группа главных предложений не найдена")
        return jsonify({"status": "error", "message": "Группа главных предложений не найдена"}), 404

    try:
        for item in updated_order:
            sentence_id = int(item["sentence_id"])
            if sentence_id:
                HeadSentence.set_sentence_index_or_weight(sentence_id, group_id, new_index = item["new_index"])

        logger.info("(Обновление порядка главных предложений) ✅ Порядок главных предложений успешно обновлен")
        logger.info("(Обновление порядка главных предложений) ----------------------------------------------")
        return jsonify({"status": "success", "message": "Порядок обновлен"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка сохранения: {e}"}), 500



@editing_report_bp.route('/update_report', methods=["PATCH"])
@auth_required()
def update_report():
    logger.info("(Обновление протокола) ------------------------------------------------")
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
        logger.info("(Обновление протокола) ------------------------------------------------------")
        return jsonify({"status": "success", "message": "Данные протокола успешно обновлены"}), 200
    except Exception as e:
        logger.error(f"(Обновление протокола) ❌ Ошибка при обновлении протокола: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обновлении протокола: {str(e)}"}), 500
        


@editing_report_bp.route('/update_paragraph_text', methods=["PATCH"])
@auth_required()
def update_paragraph_text():
    logger.info("(Обновление текста параграфа) ------------------------------------------------")
    logger.info("(Обновление текста параграфа) 🚀 Начато обновление текста параграфа")
    data = request.json
    paragraph_id = data.get("paragraph_id")
    paragraph = Paragraph.query.get(paragraph_id)
    
    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        logger.error(f"(Обновление текста параграфа) ❌ Параграф не найден или не соответствует профилю")
        return jsonify({"status": "error", "message": "Параграф не найден или не соответствует профилю"}), 403
    
    new_paragraph_text = data.get("paragraph_text")
    ai_gramma_check = data.get("ai_gramma_check", False)
    logger.info(f"(Обновление текста параграфа) Получены данные для обновления текста параграфа: {new_paragraph_text}, проверка грамматики: {ai_gramma_check}")
    
    try:
        if ai_gramma_check:
            new_paragraph_text = gramma_correction_ai(new_paragraph_text)
        paragraph.update(paragraph=new_paragraph_text)
        logger.info(f"(Обновление текста параграфа) ✅ Текст параграфа успешно обновлен")
        logger.info("(Обновление текста параграфа) -----------------------------------------------")
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
    logger.info("(Обновление текста предложения /update_sentence_text) ------------------------------------------------")
    logger.info("(Обновление текста предложения /update_sentence_text) 🚀 Начато обновление текста предложения")
    data = request.json
    sentence_id = data.get("sentence_id")
    sentence_text = data.get("sentence_text")
    sentence_type = data.get("sentence_type")
    group_id = data.get("group_id")
    related_id = data.get("related_id")
    ai_gramma_check = data.get("ai_gramma_check", False)
    use_dublicate = data.get("use_dublicate", False)

    # Проверка типа предложения
    if sentence_type not in ["head", "body", "tail"]:
        logger.error("(Обновление текста предложения /update_sentence_text) ❌ Некорректный тип предложения")
        return jsonify({"status": "error", "message": "Некорректный тип предложения."}), 400

    # Выбор модели по типу
    sentence_class = {"head": HeadSentence, "body": BodySentence, "tail": TailSentence}.get(sentence_type)
    logger.info(f"(Обновление текста предложения /update_sentence_text)(тип предложения {sentence_class}) Получены данные для обновления текста предложения: {data}. Проверка грамматики: {ai_gramma_check}. Использовать дубликат: {use_dublicate}")
    if ai_gramma_check:
        logger.info(f"(Обновление текста предложения /update_sentence_text) Проверка грамматики через ИИ")
        try:
            sentence_text = gramma_correction_ai(sentence_text)
        except Exception as e:
            logger.error(f"(Обновление текста предложения /update_sentence_text) ❌ Ошибка при проверке грамматики через ИИ: {str(e)} текс остается прежним")
            pass
    try:
        sentence_class.edit_sentence(sentence_id=sentence_id,
                                     group_id=group_id,
                                     related_id=related_id,
                                     new_text=sentence_text,
                                     use_dublicate=use_dublicate,
                                     )
        logger.info(f"(Обновление текста предложения /update_sentence_text) ✅ Текст предложения успешно обновлен")
        logger.info("(Обновление текста предложения /update_sentence_text) ------------------------------------------------------")
        return jsonify({"status": "success", "message": "Текст предложения успешно обновлен."}), 200
    except Exception as e:
        logger.error(f"(Обновление текста предложения /update_sentence_text) ❌ Ошибка при обновлении текста предложения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка обновления текста: {str(e)}"}), 500




@editing_report_bp.route('/add_new_paragraph', methods=['POST'])
@auth_required()
def add_paragraph():
    logger.info("(Добавление нового параграфа) --------------------------------------------")
    logger.info(f"(Добавление нового параграфа) 🚀 Начато добавление нового параграфа")
    data = request.json
    
    report_id = data.get("report_id")
    report = Report.query.get(report_id)
    
    copy_paste = data.get("object_type") == "paragraph"
    paragraph_index = get_max_index(Paragraph, "report_id", report_id, Paragraph.paragraph_index)
    
    if not report or report.profile_id != g.current_profile.id:
        logger.error(f"(Добавление нового параграфа) ❌ Протокол не найден или не соответствует данному профилю")
        return jsonify({"status": "error", "message": "Протокол не найден или не соответствует данному профилю"}), 403
    
    if copy_paste:
        logger.info(f"(Добавление нового параграфа) Параграф будет вставлен из буфера обмена")
        paragraph_id = data.get("object_id")
        exist_paragraph = Paragraph.get_by_id(paragraph_id)
        
        paragraph_data = {
            "report_id": report_id,
            "paragraph": exist_paragraph.paragraph,
            "paragraph_index": paragraph_index,
            "head_sentence_group_id": exist_paragraph.head_sentence_group_id,
            "tail_sentence_group_id": exist_paragraph.tail_sentence_group_id,
            "paragraph_visible": exist_paragraph.paragraph_visible,
            "title_paragraph": exist_paragraph.title_paragraph,
            "bold_paragraph": exist_paragraph.bold_paragraph,
            "str_before": exist_paragraph.str_before,
            "str_after": exist_paragraph.str_after,
            "is_active": exist_paragraph.is_active,
            "is_additional": exist_paragraph.is_additional,
        }
        
        try:
            new_paragraph = Paragraph.create(**paragraph_data)
            logger.info(f"(Добавление нового параграфа) ✅ Параграф успешно добавлен")
            logger.info("(Добавление нового параграфа) --------------------------------------------")
            return jsonify({"status": "success",
                            "message": "Параграф успешно добавлен",
                            "paragraph_id": new_paragraph.id,
                            "paragraph_index": new_paragraph.paragraph_index,
                            "paragraph": new_paragraph.paragraph
                            }), 200
        except Exception as e:
            logger.error(f"(Добавление нового параграфа) ❌ Ошибка добавления параграфа: {e}")
            return jsonify({"status": "error", "message": f"Ошибка добавления параграфа: {e}"}), 400
        


    try:
        new_paragraph = Paragraph.create(
            report_id=report.id,
            paragraph_index=paragraph_index,
            paragraph="Введите текст параграфа"
        )
        logger.info(f"(Добавление нового параграфа) ✅ Параграф успешно добавлен")
        logger.info("(Добавление нового параграфа) --------------------------------------------")
        return jsonify({"status": "success", 
                        "message": "Параграф успешно добавлен",
                        "paragraph_index": paragraph_index,
                        "paragraph_id": new_paragraph.id,
                        "paragraph": "Введите текст параграфа"
                        }), 200
    except Exception as e:
        logger.error(f"(Добавление нового параграфа) ❌ Ошибка добавления параграфа: {e}")
        return jsonify({"status": "error", "message": f"Ошибка добавления параграфа, код ошибки: {e}"}), 400



@editing_report_bp.route("/add_new_sentence", methods=["POST"])
@auth_required()
def add_new_sentence():
    """Создаёт новое дополнительное предложение (BodySentence) для главного предложения."""
    logger.info("(Создание нового дополнительного предложения) --------------------------------------------")
    logger.info("(Создание нового предложения) 🚀  Начат сбор данных для создания нового  предложения")
    data = request.get_json()
    
    if not data:
        logger.error("(Создание нового предложения) ❌ Отсутствуют данные для создания нового предложения")
        return jsonify({"status": "error", "message": "Отсутствуют данные для создания нового предложения"}), 400
    
    logger.info(f"(Создание нового предложения) Получены данные для создания нового предложения: {data}. Использовать дубликат: {data.get('use_dublicate', True)}")
    
    sentence_type = data.get("sentence_type")
    unique = data.get("unique", False)
    
    if sentence_type == "head":
        class_type = HeadSentence
    elif sentence_type == "body":
        class_type = BodySentence
    elif sentence_type == "tail":
        class_type = TailSentence
    else:
        logger.error(f"(Создание нового предложения) ❌ Неизвестный тип предложения")
        return jsonify({"status": "error", "message": "Неизвестный тип предложения"}), 400
    
    report_type_id = Report.get_report_type(int(data.get("report_id")))
    related_id = data.get("related_id")
    sentence_index = data.get("sentence_index")
    if not report_type_id or not related_id:
        logger.error(f"(Создание нового предложения) ❌ Отсутствуют необходимые данные для создания предложения")
        return jsonify({"status": "error", "message": "Отсутствуют необходимые данные для создания предложения"}), 400
    
    sentence_id = data.get("sentence_id")
    sentence_data = {
            "user_id": current_user.id,
            "report_type_id": report_type_id,
            "sentence": "Введите текст предложения",
            "related_id": related_id,
            "sentence_index": sentence_index,
            "unique": unique,
        }
    
    if sentence_id:
        sentence = class_type.get_by_id(sentence_id)
        if not sentence:
            logger.error(f"(Создание нового предложения) ❌ Предложение не найдено")
            return jsonify({"status": "error", "message": "Предложение не найдено"}), 404
        
        sentence_data["sentence"] = sentence.sentence
    
    logger.info(f"(Создание нового предложения) Получены все необходимые данные для создания предложения {sentence_data}. Начато создание нового предложения")
    
    try:
        new_sentence, new_sentence_group = class_type.create(**sentence_data)
        if sentence_id and sentence_type == "head":
            new_sentence.body_sentence_group_id = sentence.body_sentence_group_id
            db.session.commit()
            
            logger.info(f"(Создание нового предложения) ✅ Успешно добавлено новое предложение с id={new_sentence.id} из буфера обмена")
        logger.info(f"(Создание нового предложения) ✅ Успешно создано новое {sentence_type} предложение с id={new_sentence.id}")
        logger.info("(Создание нового предложения) --------------------------------------------")
        
        return jsonify({
            "status": "success",
            "message": f"Успешно создано новое {sentence_type} предложение",
        }), 201

    except Exception as e:
        logger.error(f"(Создание нового предложения) ❌ Ошибка при создании нового предложения: {e}")
        return jsonify({"status": "error", "message": f"Ошибка при создании нового предложения: {e}"}), 500
     

@editing_report_bp.route('/delete_paragraph', methods=["DELETE"])
@auth_required()
def delete_paragraph():
    logger.info(f"(Логика удаления параграфа) --------------------------------------------")
    logger.info(f"(Логика удаления параграфа) 🚀 Начинаю удаление параграфа")
    paragraph_id = request.json.get("paragraph_id")
    paragraph = Paragraph.get_by_id(paragraph_id)
    report_id = paragraph.report_id
    head_sentence_group = paragraph.head_sentence_group
    tail_sentence_group = paragraph.tail_sentence_group

    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        logger.error(f"(Логика удаления параграфа) ❌ Параграф не найден или не соответствует профилю")
        return jsonify({"status": "error", "message": "Параграф не найден или не соответствует профилю"}), 404
    
    try:
        if tail_sentence_group:
            logger.info(f"(Логика удаления параграфа) У параграфа есть группа tail предложений")
            tail_sentence_group_count = TailSentenceGroup.is_linked(tail_sentence_group.id)
            if  tail_sentence_group_count > 1:
                logger.info(f"(Логика удаления параграфа) Tail предложения параграфа связаны с другими протоколами. Просто удаляю связь с текущим параграфом")
                TailSentenceGroup.unlink_group(tail_sentence_group.id, paragraph_id)
                logger.info(f"(Логика удаления параграфа) Связь с параграфом успешно удалена")
                pass
            else:
                logger.info(f"(Логика удаления параграфа) Параграф связан только с текущим протоколом. Удаляю группу tail предложений")
                TailSentenceGroup.delete_group(tail_sentence_group.id, paragraph_id)
                logger.info(f"(Логика удаления параграфа) Группа tail предложений успешно удалена")
                pass
        if head_sentence_group:
            logger.info(f"(Логика удаления параграфа) У параграфа есть группа head предложений")
            head_sentence_group_count = HeadSentenceGroup.is_linked(head_sentence_group.id)
            if head_sentence_group_count > 1:
                logger.info(f"(Логика удаления параграфа) Head предложения параграфа связаны с другими протоколами. Просто удаляю связь с текущим параграфом")
                HeadSentenceGroup.unlink_group(head_sentence_group.id, paragraph_id)
                logger.info(f"(Логика удаления параграфа) Связь с параграфом успешно удалена")
                pass
            else:
                logger.info(f"(Логика удаления параграфа) Параграф связан только с текущим протоколом. Удаляю группу head предложений")
                HeadSentenceGroup.delete_group(head_sentence_group.id, paragraph_id)
                logger.info(f"(Логика удаления параграфа) Группа head предложений успешно удалена")
                pass
        paragraph.delete()
        logger.info(f"(Логика удаления параграфа) Параграф успешно удален")
        try:
            normalize_paragraph_indices(report_id)
        except Exception as e:
            logger.error(f"(Логика удаления параграфа) ❌ Ошибка при ренормализации индексов параграфов: {e}")
            return jsonify({"status": "error", "message": f"Ошибка при ренормализации индексов параграфов: {e}"}), 500
        
            
        logger.info("(Логика удаления параграфа) --------------------------------------------")
        logger.info("(Логика удаления параграфа) ✅ Параграф успешно удален")
        return jsonify({"status": "success", "message": "Параграф успешно удален"}), 200
    except Exception as e:
        logger.error(f"Error deleting paragraph: {str(e)}")
        return jsonify({"status": "error", "message": f"Не удалось удалить параграф. Ошибка: {e}"}), 400

    
@editing_report_bp.route('/delete_sentence', methods=['DELETE'])
@auth_required()
def delete_sentence():
    """Удаляет предложение или отвязывает его от группы."""
    logger.info(f"(Удаление предложения) --------------------------------------------")
    logger.info(f"(Удаление предложения) 🚀 Начинаю удаление предложения")
    data = request.get_json()
    sentence_id = data.get("sentence_id")
    sentence_type = data.get("sentence_type")
    related_id = data.get("related_id") 
    logger.info(f"Получены данные для удаления предложения: {data}")
   
    if not sentence_id or not related_id or not sentence_type:
        logger.error(f"(Удаление предложения) ❌ Отсутствуют необходимые данные для удаления предложения")
        return jsonify({"status": "error", "message": "Отсутствуют необходимые данные для удаления предложения"}), 400
    
    group_id = 0
    if sentence_type == "body":
        group_id = HeadSentence.query.get(related_id).body_sentence_group_id
        logger.info(f"(Удаление предложения) Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            BodySentence.delete_sentence(sentence_id, group_id)
            logger.info(f"(Удаление предложения) ✅ Предложение успешно удалено")
            logger.info("(Удаление предложения) --------------------------------------------")
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"(Удаление предложения) ❌ Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
    
    elif sentence_type == "tail":
        group_id = Paragraph.query.get(related_id).tail_sentence_group_id
        logger.info(f"(Удаление предложения) Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            TailSentence.delete_sentence(sentence_id, group_id)
            logger.info(f"(Удаление предложения) ✅ Предложение успешно удалено")
            logger.info("(Удаление предложения) --------------------------------------------")
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"(Удаление предложения) ❌ Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
        
    elif sentence_type == "head":
        group_id = Paragraph.query.get(related_id).head_sentence_group_id
        logger.info(f"(Удаление предложения) Предложение является {sentence_type} и его группа предложений = {group_id}")
        try:
            HeadSentence.delete_sentence(sentence_id, group_id)
            logger.info(f"(Удаление предложения) ✅ Предложение успешно удалено")
            logger.info("(Удаление предложения) --------------------------------------------")
            return jsonify({"status": "success", "message": "Предложение удалено"}), 200
        except ValueError as e:
            logger.error(f"(Удаление предложения) ❌ Ошибка при удалении предложения: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 404
        
    else:
        logger.error(f"(Удаление предложения) ❌ Неизвестный тип предложения")
        return jsonify({"status": "error", "message": "Неизвестный тип предложения"}), 400
        
        
@editing_report_bp.route('/delete_subsidiaries', methods=["DELETE"])
@auth_required()
def delete_subsidiaries():
    logger.info(f"(Удаление дочерних групп) --------------------------------------------")
    logger.info(f"(Удаление дочерних групп) 🚀 Начинаю удаление Дочерних групп")
    data = request.get_json()
    if not data:
        logger.error(f"(Удаление дочерних групп) ❌ Отсутствуют данные для удаления")
        return jsonify({"status": "error", "message": "Отсутствуют данные для удаления"}), 400
    
    logger.info(f"(Удаление дочерних групп) Получены данные для удаления: {data}")
    object_type = data.get("object_type") or None
    
    if object_type and object_type == "paragraph":
        logger.info(f"(Удаление дочерних групп) Тип объекта - ПАРАГРАФ. Начинаю удаление дочерних групп head и tail предложений")
        paragraph_id = data.get("object_id")
        paragraph = Paragraph.get_by_id(paragraph_id)
        head_group_id = paragraph.head_sentence_group_id
        tail_group_id = paragraph.tail_sentence_group_id
        
        if head_group_id:
            HeadSentenceGroup.delete_group(head_group_id, paragraph_id)
            logger.info(f"(Удаление дочерних групп) Группа head предложений успешно удалена")
        if tail_group_id:
            TailSentenceGroup.delete_group(tail_group_id, paragraph_id)
            logger.info(f"(Удаление дочерних групп) Группа tail предложений успешно удалена")
            
        logger.info(f"(Удаление дочерних групп) ✅ Дочерние группы успешно удалены")
        logger.info(f"(Удаление дочерних групп) --------------------------------------------")
        return jsonify({"status": "success", "message": "Дочерние группы успешно удалены"}), 200
    
    elif object_type and object_type == "sentence":
        logger.info(f"(Удаление дочерних групп) Тип объекта - ПРЕДЛОЖЕНИЕ. Начинаю удаление дочерних групп body предложений")
        sentence_id = data.get("object_id") or None
        sentence = HeadSentence.query.get(sentence_id) or None
        group_id = sentence.body_sentence_group_id
        if group_id:
            BodySentenceGroup.delete_group(group_id, sentence_id)
            logger.info(f"(Удаление дочерних групп) Группа body предложений успешно удалена")
            logger.info(f"(Удаление дочерних групп) ✅ Дочерние группы успешно удалены")
            logger.info(f"(Удаление дочерних групп) --------------------------------------------")
            return jsonify({"status": "success", "message": "Дочерние группы успешно удалены"}), 200
        logger.info(f"(Удаление дочерних групп) ✅ Дочерние группы успешно удалены")
        logger.info(f"(Удаление дочерних групп) --------------------------------------------")
        return jsonify({"status": "success", "message": "Дочерние группы успешно удалены"}), 200
    
    else:
        logger.error(f"(Удаление дочерних групп) ❌ Неизвестный тип объекта")
        return jsonify({"status": "error", "message": "Неизвестный тип объекта"}), 400
        
    
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


# Создает новую группу предложений и заменяет ей старую
@editing_report_bp.route('//unlink_group', methods=['PATCH'])
@auth_required()
def unlink_group():
    logger.info(f"(Отделение группы) --------------------------------------------")
    logger.info(f"(Отделение группы) 🚀 Начинаю отделение группы")
    data = request.get_json()
    
    group_id = data.get("group_id")
    sentence_type = data.get("sentence_type")
    related_id = data.get("related_id") 
    if not group_id or not sentence_type or not related_id: 
        logger.error(f"(Отделение группы) ❌ Не указаны необходимые данные для отделения группы")
        return jsonify({"status": "error", "message": "Не указаны необходимые данные для отделения группы"}), 400
    
    
    if sentence_type == "head":
        try:
            new_group_id = HeadSentenceGroup.copy_group(group_id)
            paragragh = Paragraph.query.get(related_id)
            paragragh.head_sentence_group_id = new_group_id
            db.session.commit()
        except ValueError as e:
            logger.error(f"(Отделение группы) ❌ Ошибка при отделении группы: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при отделении группы: {str(e)}"}), 400
       
    elif sentence_type == "tail":
        try:
            new_group_id = TailSentenceGroup.copy_group(group_id)
            paragragh = Paragraph.query.get(related_id)
            paragragh.tail_sentence_group_id = new_group_id
            db.session.commit()
        except ValueError as e:
            logger.error(f"(Отделение группы) ❌ Ошибка при отделении группы: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при отделении группы: {str(e)}"}), 400
    else:
        try:
            new_group_id = BodySentenceGroup.copy_group(group_id)
            head_sentence = HeadSentence.query.get(related_id)
            head_sentence.body_sentence_group_id = new_group_id
            db.session.commit()
        except ValueError as e:
            logger.error(f"(Отделение группы) ❌ Ошибка при отделении группы: {str(e)}")
            return jsonify({"status": "error", "message": f"Ошибка при отделении группы: {str(e)}"}), 400
    
    logger.info(f"(Отделение группы) ✅ Группа успешно отделена")
    logger.info(f"(Отделение группы) --------------------------------------------")
    return jsonify({"status": "success", "message": "Группа успешно отделена"}), 200
   
    
# Обрабатывает запрос на то, чтобы поделиться протоколом с другим пользователем
@editing_report_bp.route('/share_report', methods=['POST'])
@auth_required()
def share_report():
    logger.info(f"(Поделиться протоколом) --------------------------------------------")
    logger.info(f"(Поделиться протоколом) 🚀 Начинаю обработку запроса на поделиться протоколом")
    data = request.get_json()
    report_id = data.get("report_id")
    email = data.get("email")
    if not report_id or not email:
        logger.error(f"(Поделиться протоколом) ❌ Не указаны необходимые данные необходимые чтобы поделиться протоколом")
        return jsonify({"status": "error", "message": "Не указаны необходимые данные необходимые чтобы поделиться протоколом"}), 400
    shared_with_user = User.find_by_email(email)
    if not shared_with_user:
        logger.error(f"(Поделиться протоколом) ❌ Пользователь не найден")
        return jsonify({"status": "error", "message": "Пользователь с таким email не найден"}), 404
    
    shared_with_user_id = shared_with_user.id 
    
    try:
        ReportShare.create(report_id, shared_with_user_id)
        logger.info(f"(Поделиться протоколом) ✅ Протокол успешно поделен")
        logger.info(f"(Поделиться протоколом) --------------------------------------------")
        return jsonify({"status": "success", "message": f"Удалось успешно поделиться протоколом с пользователем {email}"}), 200
    except Exception as e:
        logger.error(f"(Поделиться протоколом) ❌ Ошибка при попытке поделиться протоколом: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при попытке поделиться протоколом: {str(e)}"}), 500
    
    
    
@editing_report_bp.route("/toggle_public_report", methods=["PATCH"])
@auth_required()
@require_role_rank(4)
def toggle_public_report():
    logger.info("[toggle_public_report] --------------------------------------------")  
    logger.info("[toggle_public_report] 🚀 Начато переключение статуса общедоступности протокола")
    try:
        data = request.get_json()
        report_id = data.get("report_id")
        logger.info(f"[toggle_public_report] Получены данные для переключения статуса: {data}")

        if not report_id:
            logger.error("[toggle_public_report] ❌ ID протокола не передан.")
            return jsonify({"status": "error", "message": "ID протокола не передан."}), 400

        report = Report.get_by_id(report_id)

        if not report or report.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Протокол не найден или не принадлежит вам."}), 403

        # Переключаем флаг public
        report.public = not report.public
        db.session.commit()
        logger.info("[toggle_public_report] ✅ Статус общедоступности успешно изменён")
        logger.info("[toggle_public_report] --------------------------------------------")

        return jsonify({
            "status": "success",
            "message": f"Статус общедоступности изменён: {'общедоступный' if report.public else 'приватный'}",
            "new_public_status": report.public
        })

    except Exception as e:
        logger.error(f"[toggle_public_report] ❌ Ошибка при переключении статуса: {e}")
        return jsonify({
            "status": "error",
            "message": f"Ошибка при переключении статуса: {str(e)}"
        }), 500
        
        
        
        
@editing_report_bp.route('/unlink_sentence', methods=["POST"])
@auth_required()
def unlink_sentence():
    """Отвязывает предложение от группы."""
    logger.info(f"(Отвязка предложения) --------------------------------------------")
    logger.info(f"(Отвязка предложения) 🚀 Начинаю отвязывать предложение от группы")
    data = request.get_json()
    
    sentence_id = data.get("sentence_id")
    sentence_type = data.get("sentence_type")
    related_id = data.get("related_id") 
    group_id = data.get("group_id")
    sentence_index = data.get("sentence_index")
    logger.info(f"(Отвязка предложения) Получены данные для отвязки предложения: {data}")
    
    if not sentence_id or not related_id: 
        logger.error(f"(Отвязка предложения) ❌ Не указаны необходимые данные для отвязки предложения от группы")
        return jsonify({"status": "error", "message": "Не указаны необходимые данные для отвязки предложения от группы"}), 400
    
    if sentence_type == "head":
        sentence_class = HeadSentence
    elif sentence_type == "tail":
        sentence_class = TailSentence
    elif sentence_type == "body":
        sentence_class = BodySentence
    else:
        logger.error(f"(Отвязка предложения) ❌ Неизвестный тип предложения")
        return jsonify({"status": "error", "message": "Неизвестный тип предложения"}), 400
    
    sentence = sentence_class.get_by_id(sentence_id)
    if not sentence:
        logger.error(f"(Отвязка предложения) ❌ Предложение не найдено")
        return jsonify({"status": "error", "message": "Предложение не найдено"}), 404
    
    new_sentence_data = {
        "user_id": current_user.id,
        "report_type_id": sentence.report_type_id,
        "sentence": sentence.sentence,
        "related_id": related_id,
        "sentence_index": sentence_index if sentence_type == "head" else None,
        "tags": sentence.tags,
        "comment": sentence.comment,
        "sentence_weight": None if sentence_type == "head" else sentence_index,
        "unique": True,
    }
    try:
        new_sentence, new_group = sentence_class.create(**new_sentence_data)
        if sentence_type == "head":
            new_sentence.body_sentence_group_id = sentence.body_sentence_group_id
            db.session.commit()
            logger.info(f"(Отвязка предложения) ✅ Успешно отвязано предложение с id={sentence.id} от группы")
        # Так как данное предложение имеет другие связи, то метод не удалит его а только отвяжет от текущей группы
        sentence_class.delete_sentence(sentence_id, group_id)
    except Exception as e:
        logger.error(f"(Отвязка предложения) ❌ Ошибка при создании нового предложения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при создании нового предложения: {str(e)}"}), 500
    
    logger.info(f"(Отвязка предложения) ✅ Предложение успешно отвязано от группы")
    logger.info(f"(Отвязка предложения) --------------------------------------------")
    return jsonify({"status": "success", "message": "Предложение успешно отвязано от группы"}), 200




@editing_report_bp.route('/update_sentence_weight', methods=["PATCH"])
@auth_required()
def update_sentence_weight():
    """Обновляет вес предложения."""
    logger.info(f"(Обновление веса предложения) --------------------------------------------")
    logger.info(f"(Обновление веса предложения) 🚀 Начато обновление веса предложения")
    data = request.json
    sentence_id = data.get("sentence_id")
    sentence_weight = data.get("sentence_weight")
    group_id = data.get("group_id")
    sentence_type = data.get("sentence_type")
    
    if not sentence_id or not sentence_weight or not group_id or not sentence_type:
        logger.error(f"(Обновление веса предложения) ❌ Не указаны необходимые данные для обновления веса предложения")
        return jsonify({"status": "error", "message": "Не указаны необходимые данные для обновления веса предложения"}), 400
    
    if sentence_type not in ["body", "tail"]:
        logger.error(f"(Обновление веса предложения) ❌ Неподходящий тип предложения")
        return jsonify({"status": "error", "message": "Неподходящий тип предложения"}), 400

    # Выбор модели по типу
    sentence_class = {"body": BodySentence, "tail": TailSentence}.get(sentence_type)
    logger.info(f"(Обновление веса предложения) Получены данные для обновления веса предложения: {data}")
    
    try:
        sentence_class.set_sentence_index_or_weight(sentence_id, group_id, new_weight=sentence_weight,)
        logger.info(f"(Обновление веса предложения) ✅ Вес предложения успешно обновлен")
        logger.info(f"(Обновление веса предложения) --------------------------------------------")
        return jsonify({"status": "success", "message": "Вес предложения успешно обновлен."}), 200
    
    except Exception as e:
        logger.error(f"(Обновление веса предложения) ❌ Ошибка при обновлении веса предложения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка обновления веса"}), 500