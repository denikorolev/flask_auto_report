#working_with_reports.py

from flask import Blueprint, render_template, request, jsonify, current_app, session
from flask_security import current_user
from app.models.models import db, Report, KeyWord, TailSentence, BodySentence, ReportTextSnapshot
from app.utils.sentence_processing import group_keywords, split_sentences_if_needed, clean_and_normalize_text, compare_sentences_by_paragraph, preprocess_sentence, split_report_structure_for_ai, replace_head_sentences_with_fuzzy_check, merge_ai_response_into_skeleton
from app.utils.common import ensure_list
from app.utils.logger import logger
from flask_security.decorators import auth_required
from tasks.celery_tasks import async_analyze_dynamics



working_with_reports_bp = Blueprint('working_with_reports', __name__)

# Functions

# Routes

@working_with_reports_bp.route("/choosing_report", methods=['POST', 'GET'])
@auth_required()
def choosing_report(): 
    logger.info(f"(Выбор шаблона протокола) ------------------------------------")
    logger.info(f"(Выбор шаблона протокола) 🚀 Начинаю обработку запроса")
    profile_id = session.get("profile_id")

    if request.method == "POST":
        logger.info("(Выбор шаблона протокола) Получен POST-запрос на выбор шаблона протокола.")
        if request.is_json:
            data = request.get_json()
            logger.info(f"(Выбор шаблона протокола) Полученные данные: {data}")
            rep_area = data.get("report_area")
            reports = Report.find_by_category_2(rep_area, profile_id) if rep_area else []
            if not reports:
                logger.error("(Выбор шаблона протокола) ❌ Не найдено шаблонов протоколов для выбранного типа")
                return jsonify({"status": "error", "message": "Не найдено шаблонов протоколов для выбранного типа"}), 404
            # Возвращаем данные в формате JSON
            logger.info("(Выбор шаблона протокола) ------------------------------------")
            logger.info("(Выбор шаблона протокола) ✅ Отправляю данные о найденных шаблонах протоколов")
            return jsonify({
                "status": "success",
                "reports": [
                    {"id": report.id, "report_name": report.report_name}
                    for report in reports
                ]
            })
    logger.info("(Выбор шаблона протокола) Простая загрузка страницы.")
    return render_template(
        "choose_report.html",
        title="Выбор шаблона протокола",
    )


@working_with_reports_bp.route("/working_with_reports", methods=['GET'])
@auth_required()
def working_with_reports():
    logger.info(f"(работа с протоколом) ------------------------------------") 
    logger.info(f"(работа с протоколом) 🚀 Начинаю обработку запроса для вывода данных протокола")
    current_report_id = int(request.args.get("reportId"))
    profile_id = session.get("profile_id")
    
    if not current_report_id:
    
        logger.error(f"(работа с протоколом) ❌ Не получен id протокола")
        return render_template("errors/error.html", message="Нет данных о подходящем протоколе для работы")
    try:
        report_data, paragraphs_data = Report.get_report_data(current_report_id)
        if report_data is None or paragraphs_data is None:
            logger.error(f"(работа с протоколом) ❌ Метод get_report_data вернул None")
            return render_template("errors/error.html", message="Метод get_report_data вернул None")
    except Exception as e:
        logger.error(f"(работа с протоколом) ❌ Не получилось сгруппировать данные протокола или данные его параграфов: {e}")
        return render_template("errors/error.html", message=f"Не получилось сгруппировать данные протокола или данные его параграфов: {e}")
    
    # Получаем ключевые слова для текущего пользователя
    try:
        key_words_obj = KeyWord.get_keywords_for_report(profile_id, current_report_id)
        key_words_groups = group_keywords(key_words_obj)
    except Exception as e:
        logger.error(f"(работа с протоколом) ❌ Не получилось получить ключевые слова для текущего пользователя: {e}")
        return render_template("errors/error.html", message=f"Не получилось получить ключевые слова для текущего пользователя: {e}")
    
    # Подготовка настроек полоьзователя для передачи на страницу
   
    logger.info(f"(работа с протоколом) ------------------------------------")
    logger.info(f"(работа с протоколом) ✅ Данные протокола и его параграфов успешно получены. Загружаю страницу")
    return render_template(
        "working_with_report.html", 
        title=report_data["report_name"],
        report_data=report_data,
        paragraphs_data=paragraphs_data,
        key_words_groups=key_words_groups,
    )


    

@working_with_reports_bp.route("/save_modified_sentences", methods=["POST"])
@auth_required()
def save_modified_sentences():
    """
    Processes and saves new or modified sentences to the database.
    Handles splitting of multi-sentence inputs and normalizes valid sentences.
    Keeps track of saved, skipped, and missed sentences.
    """
    
    logger.info(f"(Сохранение измененных предложений) ------------------------------------")
    logger.info(f"(Сохранение измененных предложений) 🚀 Начинаю обработку запроса на сохранение измененных предложений")
    try:
        # Получаем данные из запроса
        data = request.get_json()
        logger.info(f"(Сохранение измененных предложений) Полученные данные: {data}")

        report_id = int(data.get("report_id"))
        sentences = ensure_list(data.get("sentences"))
        user_id = current_user.id
        report_global_modality_id = Report.get_by_id(report_id).global_category_id
        profile_id = session.get("profile_id")
        language = session.get("lang", "default_language")
        
        if not sentences or not report_id:
            logger.error(f"(Сохранение измененных предложений) ❌ Не хватает текстов предложений или id протокола")
            return jsonify({"status": "error", "message": "Не хватает текстов предложений или id протокола"}), 400
        
        processed_sentences = []  # Для хранения обработанных предложений, 
        #отправлю их потом на сравнение в функцию compare_sentences_by_paragraph
        missed_count = 0  # Счётчик пропущенных предложений
        

        for sentence_data in sentences:
            head_sentence_id = sentence_data.get("head_sentence_id", None)
            paragraph_id = sentence_data.get("paragraph_id")
            nativ_text = sentence_data.get("text")
            sentence_type = sentence_data.get("type")
            
            # Проверяем корректность данных
            if not paragraph_id or not nativ_text.strip():
                missed_count += 1
                logger.info(f"(Сохранение измененных предложений) ⚠️ Пропускаю данные без параграфа или пустой текст: {sentence_data}")
                continue  
            
            before_split_text = preprocess_sentence(nativ_text)
            
            if not before_split_text.strip():
                missed_count += 1
                continue  
            
            # Проверяем текст на наличие нескольких предложений
            unsplited_sentences, splited_sentences = split_sentences_if_needed(before_split_text, language)

            if splited_sentences:
                # Обрабатываем случаи с разделением
                for idx, splited_sentence in enumerate(splited_sentences):
                    new_sentence_type = sentence_type
                    if splited_sentence.strip() == "":
                        missed_count += 1
                        logger.info(f"(Сохранение измененных предложений) ⚠️ Пропускаю пустое предложение: {splited_sentence}")
                        continue  # Пропускаем пустые предложения
                    if sentence_type == "body":
                        new_sentence_type = "body" if idx == 0 else "tail"
                    else:
                        new_sentence_type = "tail"
                    processed_sentences.append({
                        "paragraph_id": paragraph_id,
                        "head_sentence_id": head_sentence_id,
                        "sentence_type": new_sentence_type,
                        "text": splited_sentence.strip()
                    })
            else:
                for unsplited_sentence in unsplited_sentences:
                    if unsplited_sentence.strip() == "":
                        missed_count += 1
                        logger.info(f"(Сохранение измененных предложений) ⚠️ Пропускаю пустое предложение: {unsplited_sentence}")
                        continue
                    processed_sentences.append({
                        "paragraph_id": paragraph_id,
                        "head_sentence_id": head_sentence_id,
                        "sentence_type": "body" if sentence_type == "body" else "tail",
                        "text": unsplited_sentence.strip()
                    })

        # Теперь работаем с уже разделенными предложениями в processed_sentences
        
        # Сначала сравниваем их с существующими предложениями в базе данных
        comparsion_result = compare_sentences_by_paragraph(
                                                        processed_sentences,
                                                        report_id,
                                                        profile_id=profile_id)

        new_sentences = comparsion_result["unique"]
        duplicates = comparsion_result["duplicates"]
        errors_count = comparsion_result["errors_count"]
        
        missed_count = 0  # Счётчик пропущенных предложений
        saved_count = 0  # Счётчик сохранённых предложений
        saved_sentences = []  # Для хранения сохранённых предложений и последующего включения в отчет

        for sentence in new_sentences:
            processed_paragraph_id = sentence["paragraph_id"]
            head_sent_id = sentence["head_sentence_id"]
            new_sentence_text = clean_and_normalize_text(sentence["text"], profile_id)
            sentence_type = sentence["sentence_type"]
            related_id = processed_paragraph_id if sentence_type == "tail" else head_sent_id
            try:
                if sentence_type == "tail":
                   new_sentence, sent_group = TailSentence.create(
                        sentence=new_sentence_text,
                        related_id=related_id,
                        user_id=user_id,
                        report_global_modality_id=report_global_modality_id,
                        comment="Added automatically"
                    )
                # Сохраняем предложение в базу данных в качестве body_sentence 
                # для текущего главного предложения
                else:
                    if sentence["head_sentence_id"]:
                        new_sentence, sent_group = BodySentence.create(
                        sentence=new_sentence_text,
                        related_id=related_id,
                        user_id=user_id,
                        report_global_modality_id=report_global_modality_id,
                        comment="Added automatically",
                        )
                    else:
                        logger.warning(f"(Сохранение измененных предложений) ⚠️ Не найден head_sentence_id для предложения: {new_sentence_text}. Пропускаю предложение")
                        missed_count += 1   
                        continue
                saved_count += 1
                saved_sentences.append({"id": new_sentence.id, "related_id": related_id, "sentence_type": sentence_type, "text": new_sentence_text})
            except Exception as e:
                logger.error(f"(Сохранение измененных предложений) ❌ При попытке сохранения предложения ({new_sentence_text}) произошла ошибка: {str(e)}. Ошибка добавлена в счётчик")
                missed_count += 1

        sentences_adding_report = {
            "message": f"Всего обработано предложений: {len(processed_sentences)}.",
            "saved_count": saved_count,
            "skipped_count": len(processed_sentences) - saved_count,
            "missed_count": missed_count,
            "duplicates_count": len(duplicates),
            "errors_count": errors_count,
            "saved_sentences": saved_sentences,
            "duplicates": duplicates
        }

        rendered_html = render_template(
            "sentences_adding_report_snippet.html", 
            **sentences_adding_report)
        
        logger.info(f"(Сохранение измененных предложений) ✅ Проанализировано {len(processed_sentences)} предложений.")
        logger.info(f"(Сохранение измененных предложений) ------------------------------------")
        return jsonify({
            "status": "success",
            "message": f"Проанализировано {len(processed_sentences)} предложений.",
            "html": rendered_html
        }), 200

    except Exception as e:
        logger.error(f"(Сохранение измененных предложений) ❌ При попытке сохранения предложений произошла ошибка: {str(e)}")
        return jsonify({"status": "error", "message": f"При попытке автоматического сохранения предложений произошла ошибка: {str(e)}"}), 500




@working_with_reports_bp.route("/save_report_snapshot", methods=["POST"])
@auth_required()
def save_report_snapshot():
    logger.info(f"(Сохранение копии протокола) ------------------------------------")
    logger.info(f"(Сохранение копии протокола) 🚀 Начинаю обработку запроса на сохранение копии протокола")
    try:
        data = request.get_json()
        if not data:
            logger.error(f"(Сохранение копии протокола) ❌ Не получены данные в формате JSON")
            return jsonify({"status": "error", "message": "No JSON data received"}), 400
        report_id = data.get("report_id")
        text = data.get("text")
        if not report_id or not text:
            logger.error(f"(Сохранение копии протокола) ❌ Не хватает id протокола или текста копии")
            return jsonify({"status": "error", "message": "Missing required information."}), 400
        
        user_id = current_user.id
        
    except Exception as e:
        logger.error(f"(Сохранение копии протокола) ❌ Ошибка при обработке запроса: {e}")
        return jsonify({"status": "error", "message": f"Error processing request: {e}"}), 500

    try:
        ReportTextSnapshot.create(report_id, user_id, text)
        logger.info(f"(Сохранение копии протокола) ✅ Копия протокола успешно сохранена")
        return jsonify({"status": "success", "message": "Report snapshot saved"}), 200
    except Exception as e:
        logger.error(f"(Сохранение копии протокола) ❌ Не получилось сохранить копию протокола: {e}")
        return jsonify({"status": "error", "message": f"Failed to save report snapshot: {e}"}), 500
    



# editing_report.py
@working_with_reports_bp.route("/increase_sentence_weight", methods=["POST"])
@auth_required()
def increase_sentence_weight():
    logger.info(f"(Увеличение веса предложения) ------------------------------------")
    logger.info(f"(Увеличение веса предложения) 🚀 Начинаю обработку запроса на увеличение веса предложения")
    data = request.get_json()
    sentence_id = data.get("sentence_id")
    group_id = data.get("group_id")
    sentence_type = data.get("sentence_type")
    
    logger.info(f"(Увеличение веса предложения) Полученные данные: {data}")

    if not sentence_id or not group_id or sentence_type not in ["body", "tail"]:
        logger.error(f"(Увеличение веса предложения) ❌ Не хватает данных для увеличения веса предложения")
        return jsonify({"status": "error", "message": "Недостаточно данных"}), 400

    try:
        if sentence_type == "body":
            BodySentence.increase_weight(sentence_id, group_id)
        else:
            TailSentence.increase_weight(sentence_id, group_id)
        logger.info(f"(Увеличение веса предложения) ✅ Вес предложения успешно увеличен")
        return jsonify({"status": "success", "message": "Вес предложения увеличен"}), 200
    except Exception as e:
        logger.error(f"(Увеличение веса предложения) ❌ Ошибка при обновлении веса: {e}")
        return jsonify({"status": "error", "message": f"Ошибка при обновлении веса: {e}"}), 500
    
     

# Маршрут для переделывания протокола предыдущего исследования по образу предоставленного шаблона
@working_with_reports_bp.route("/analyze_dynamics", methods=["POST"])
@auth_required()
def analyze_dynamics():
    logger.info(f"(Анализ динамики) ---------------------------------------------")
    logger.info(f"(Анализ динамики) 🚀 Начинаю анализ динамики по тексту и шаблону отчета")
    logger.info("----------------------------------------------------------------")
    
    data = request.get_json()
    origin_text = data.get("origin_text", "").strip()
    report_id = data.get("report_id")
    user_id = current_user.id

    if not origin_text or not report_id:
        logger.error("Не передан текст или report_id")
        return jsonify({"status": "error", "message": "Не передан текст или report_id"}), 400

    report_data, sorted_parag = Report.get_report_data(report_id)
    if not report_data:
        logger.error("Шаблон отчета не найден")
        return jsonify({"status": "error", "message": "Шаблон отчета не найден"}), 404

    skeleton, template_text = split_report_structure_for_ai(sorted_parag)
    if not template_text or not skeleton:
        logger.error("Не удалось собрать шаблон отчета")
        return jsonify({"status": "error", "message": "Не удалось собрать шаблон отчета"}), 500

    logger.info(f"✅ Шаблон отчета успешно собран. Получены json структуры skeleton и template_text")
    
    try:
        first_look_assistant_id = current_app.config.get("OPENAI_ASSISTANT_FIRST_LOOK_RADIOLOGIST")
        structure_assistant_id = current_app.config.get("OPENAI_ASSISTANT_DYNAMIC_STRUCTURER")
        task = async_analyze_dynamics.delay(origin_text, template_text, user_id, skeleton, report_id, first_look_assistant_id, structure_assistant_id)
    except Exception as e:
        logger.error(f"❌ Не удалось запустить celery задачу async_analyze_dynamics: {e}")
        return jsonify({
            "status": "error",
            "message": f"Ошибка запуска анализа динамики: {str(e)}"
        }), 500

    return jsonify({
        "status": "success",
        "message": "Анализ динамики запущен",
        "task_id": task.id,
    }), 200

       
        

# Маршрут для финального этапа трансформации шаблона в соответствии с предыдущим протоколом
@working_with_reports_bp.route("/analyze_dynamics_finalize", methods=["POST"])
def analyze_dynamics_finalize():
    logger.info(f"(Финальный этап анализа динамики) ------------------------------------")
    logger.info(f"(Финальный этап анализа динамики) 🚀 Начинаю финальный этап анализа динамики")
    
    try:
        data = request.get_json()
        result = data.get("result")  # результат работы celery задачи
        report_id = data.get("report_id")
        skeleton = data.get("skeleton")
        profile_id = session.get("profile_id")

        if not result or not report_id:
            return jsonify({"status": "error", "message": "Missing required data"}), 400

        report_data, sorted_parag = Report.get_report_data(report_id)
        
        try:
            key_words_obj = KeyWord.get_keywords_for_report(profile_id, report_id)
            key_words_groups = group_keywords(key_words_obj)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки ключевых слов: {e}")
            key_words_groups = []
        

        merged_parag, misc_sentences = merge_ai_response_into_skeleton(skeleton, result)
        initial_report = replace_head_sentences_with_fuzzy_check(sorted_parag, merged_parag)

        new_html = render_template(
            "working_with_report.html",
            title=report_data["report_name"],
            report_data=report_data,
            paragraphs_data=initial_report,
            key_words_groups=key_words_groups,
        )
        return jsonify({
            "status": "success",
            "message": "Структура отчета успешно обновлена",
            "report_data": report_data,
            "paragraphs_data": initial_report,
            "key_words_groups": key_words_groups,
            "html": new_html,
            "misc_sentences": misc_sentences,
        }), 200
    except Exception as e:
        logger.error(f"(Финальный этап анализа динамики) ❌ Ошибка при финальном этапе анализа динамики: {e}")
        return jsonify({"status": "error", "message": f"Ошибка замены предложений: {e}"}), 500






