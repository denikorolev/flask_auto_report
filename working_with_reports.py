#working_with_reports.py

from flask import Blueprint, render_template, request, jsonify, send_file, g, current_app, json
from flask_security import current_user
import os
import json
from models import db, Report, ReportType, KeyWord, TailSentence, BodySentence, ReportTextSnapshot
from file_processing import save_to_word, extract_text_from_uploaded_file
from sentence_processing import group_keywords, split_sentences_if_needed, clean_and_normalize_text, compare_sentences_by_paragraph, preprocess_sentence, split_report_structure_for_ai, replace_head_sentences_with_fuzzy_check, merge_ai_response_into_skeleton
from openai_api import _process_openai_request, reset_ai_session, count_tokens
from utils.common import ensure_list
from logger import logger
from flask_security.decorators import auth_required
from spacy_manager import SpacyModel
from datetime import datetime



working_with_reports_bp = Blueprint('working_with_reports', __name__)

# Functions

# Routes

@working_with_reports_bp.route("/choosing_report", methods=['POST', 'GET'])
@auth_required()
def choosing_report(): 
    logger.info(f"(Выбор шаблона протокола) ------------------------------------")
    logger.info(f"(Выбор шаблона протокола) 🚀 Начинаю обработку запроса")
    current_profile = g.current_profile
    report_types_and_subtypes = ReportType.get_types_with_subtypes(current_profile.id) 
    # current_profile_reports = Report.find_by_profile(current_profile.id)
    default_report_types = current_app.config.get("REPORT_TYPES_DEFAULT_RU", [])

    if request.method == "POST":
        logger.info("(Выбор шаблона протокола) Получен POST-запрос на выбор шаблона протокола.")
        if request.is_json:
            data = request.get_json()
            rep_subtype = data.get("report_subtype")
            reports = Report.find_by_subtypes(rep_subtype)
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
        # user_reports=current_profile_reports,
        report_types_and_subtypes=report_types_and_subtypes,
        default_report_types=default_report_types,
    )


@working_with_reports_bp.route("/working_with_reports", methods=['GET'])
@auth_required()
def working_with_reports():
    logger.info(f"(работа с протоколом) ------------------------------------") 
    logger.info(f"(работа с протоколом) 🚀 Начинаю обработку запроса для вывода данных протокола")
    current_report_id = int(request.args.get("reportId"))
    full_name = request.args.get("fullname")
    birthdate = request.args.get("birthdate")
    report_number = request.args.get("reportNumber")
    
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
        key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, current_report_id)
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
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number,
        key_words_groups=key_words_groups,
    )


# Маршрут для просмотра сохраненных снапшотов (нужно будет потом убрать его в отдельный блюпринт)
@working_with_reports_bp.route("/snapshots", methods=["GET"])
@auth_required()
def snapshots():
    logger.info(f"(Просмотр сохраненных снапшотов) ------------------------------------")
    logger.info(f"(Просмотр сохраненных снапшотов) 🚀 Начинаю обработку запроса на получение сохраненных снапшотов")
    
    user_id = current_user.id
    current_profile = g.current_profile

    date_str = request.args.get("date")
    report_type = request.args.get("report_type")

    snapshots = []
    if date_str and report_type:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            report_type_int = int(report_type)
            snapshots = ReportTextSnapshot.find_by_date_and_type(user_id, date_obj, report_type_int)
        except Exception as e:
            logger.error(f"[report_snapshots] ❌ Ошибка фильтрации снапшотов: {e}")

    report_types = ReportType.find_by_profile(current_profile.id)

    return render_template(
        "snapshots.html",
        snapshots=snapshots,
        report_types=report_types
    )



@working_with_reports_bp.route("/snapshots_json", methods=["POST"])
@auth_required()
def snapshots_json():
    logger.info(f"(snapshots_json) ------------------------------------")
    logger.info(f"(snapshots_json) 🚀 Получен запрос на фильтрацию снапшотов")
    logger.info(f"(snapshots_json) Полученные данные: {request.get_json()}")
    try:
        data = request.get_json()
        date_str = data.get("date")
        report_type = int(data.get("report_type"))
        user_id = current_user.id

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        snapshots = ReportTextSnapshot.find_by_date_and_type(user_id, date_obj, report_type)
        logger.info(f"(snapshots_json) ✅ Найдено {len(snapshots)} снапшотов для даты {date_str} и типа {report_type}")

        data = render_template("partials/snapshot_results_snippet.html", snapshots=snapshots)
        logger.info(f"(snapshots_json) ✅ Данные для снапшотов успешно отрендерены")
        logger.info(f"(snapshots_json) ------------------------------------")
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error(f"(snapshots_json) ❌ Ошибка при фильтрации снапшотов: {e}")
        return jsonify({"status": "error", "message": "Ошибка при загрузке снапшотов"}), 500
    
    

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
        report_type_id = Report.get_report_type_id(report_id)
        
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
            unsplited_sentences, splited_sentences = split_sentences_if_needed(before_split_text)

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
                                                        report_id)
        
        new_sentences = comparsion_result["unique"]
        duplicates = comparsion_result["duplicates"]
        errors_count = comparsion_result["errors_count"]
        
        missed_count = 0  # Счётчик пропущенных предложений
        saved_count = 0  # Счётчик сохранённых предложений
        saved_sentences = []  # Для хранения сохранённых предложений и последующего включения в отчет

        for sentence in new_sentences:
            processed_paragraph_id = sentence["paragraph_id"]
            head_sent_id = sentence["head_sentence_id"]
            new_sentence_text = clean_and_normalize_text(sentence["text"])
            sentence_type = sentence["sentence_type"]
            related_id = processed_paragraph_id if sentence_type == "tail" else head_sent_id
            try:
                if sentence_type == "tail":
                   new_sentence, sent_group = TailSentence.create(
                        sentence=new_sentence_text,
                        related_id=related_id,
                        user_id=user_id,
                        report_type_id=report_type_id,
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
                        report_type_id=report_type_id,
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



@working_with_reports_bp.route("/export_to_word", methods=["POST"])
@auth_required()
def export_to_word():
    try:
        data = request.get_json()
        if data is None:
                return jsonify({"status": "error", "message": "No JSON data received"}), 400
        text = data.get("text")
        name = data.get("name") or "noname"
        subtype = data.get("subtype")
        report_type = data.get("report_type")
        birthdate = data.get("birthdate")
        reportnumber = data.get("reportnumber")
        scanParam = data.get("scanParam")
        side = data.get("side")

        if not text or not name or not subtype:
            return jsonify({"status": "error", "message": "Missing required information."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error processing request: {e}"}), 500

    try:
        file_path = save_to_word(text, name, subtype, report_type, birthdate, reportnumber, scanParam, side=side)
        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 500
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to export to Word: {e}"}), 500




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
    


@working_with_reports_bp.route("/train_sentence_boundary", methods=["POST"])
@auth_required()
def train_sentence_boundary():
    """
    Получает размеченное предложение и сохраняет его для дообучения SpaCy.
    """
    data = request.get_json()
    text = data.get("text")
    sent_starts = data.get("sent_starts")
    if not text or not sent_starts:
        return jsonify({"status": "error", "message": "Missing text or sent_starts"}), 400
    
    try:
        # Сохраняем в jsonl
        training_example = {
            "text": text,
            "sent_starts": sent_starts
        }

        file_path = os.path.join("spacy_training_data", "sent_boundary.jsonl")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return jsonify({"status": "success", "message": "Example saved"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
    
# считаю токены от SpaCy это не часть работы с OpenAI,
@working_with_reports_bp.route("/get_spacy_tokens", methods=["POST"])
@auth_required()
def get_spacy_tokens():
    """
    Принимает текст и возвращает список токенов от SpaCy с is_sent_start.
    """
    
    language = current_app.config.get("PROFILE_SETTINGS", {}).get("APP_LANGUAGE", "ru")

    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"status": "error", "message": "Текст не передан"}), 400

    try:
        nlp = SpacyModel.get_instance(language)
        doc = nlp(text)
        tokens = [
            {
                "text": token.text,
                "idx": token.idx,
                "is_sent_start": token.is_sent_start
            }
            for token in doc
        ]
        return jsonify({"status": "success", "tokens": tokens}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
    
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
    
    

@working_with_reports_bp.route("/analyze_dynamics", methods=["POST"])
@auth_required()
def analyze_dynamics():
    logger.info(f"(Анализ динамики) ------------------------------------")
    logger.info(f"(Анализ динамики) 🚀 Начинаю анализ динамики по тексту и шаблону отчета")
    data = request.get_json()
    raw_text = data.get("raw_text", "").strip()
    report_id = data.get("report_id")
    logger.info(f"(Анализ динамики) Полученные данные: raw_text={raw_text[:50]}..., report_id={report_id}")

    if not raw_text or not report_id:
        logger.error(f"(Анализ динамики) Не передан текст или report_id")
        return jsonify({"status": "error", "message": "Не передан текст или report_id"}), 400

    report_data, sorted_parag = Report.get_report_data(report_id)
    if not report_data:
        logger.error(f"(Анализ динамики) Шаблон отчета не найден")
        return jsonify({"status": "error", "message": "Шаблон отчета не найден"}), 404

    # Попытка собрать ключевые слова для возможного перерендеривания страницы при успшном синтезе протокола
    try:
        key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, report_id)
        key_words_groups = group_keywords(key_words_obj)
    except Exception as e:
        logger.error(f"(Анализ динамики) ❌ Не получилось получить ключевые слова для текущего пользователя: {e}")
        key_words_groups = []
    
    # Сбор шаблона отчета
    skeleton, template_text = split_report_structure_for_ai(sorted_parag)
    if not template_text or not skeleton:
        logger.error(f"(Анализ динамики) ❌ Не удалось собрать шаблон отчета")
        return jsonify({"status": "error", "message": "Не удалось собрать шаблон отчета"}), 500
    logger.info(f"(Анализ динамики) Шаблон отчета для отправки ИИ: {template_text[:3]}...{template_text[-3:]}") 
    logger.info(f"(Анализ динамики) Скелет шаблона отчета: {skeleton[:3]}...{skeleton[-3:]}")

    structurer_assistant_id = current_app.config.get("OPENAI_ASSISTANT_DYNAMIC_STRUCTURER")
    cleaner_assistant_id = current_app.config.get("OPENAI_ASSISTANT_TEXT_CLEANER")

    if not structurer_assistant_id or not cleaner_assistant_id:
        logger.error(f"(Анализ динамики) Не удалось получить ID ассистента OpenAI для динамического структурирования")
        return jsonify({"status": "error", "message": "Не удалось получить ID ИИ ассистента для динамического структурирования"}), 500
    
    try:
        # Сначала очищаем текст от лишних кусков фио, названия организации и т.д. и оставляем только протокол
        cleaned_text = _process_openai_request(
            text=raw_text,
            assistant_id=cleaner_assistant_id,
            file_id=None,
            clean_response=False,
        )
        if not cleaned_text:
            logger.warning(f"(Анализ динамики) ❌ Первая попытка очистки текста не удалась, пробую еще раз...")
            # Вторая попытка
            cleaned_text = _process_openai_request(
                text=raw_text,
                assistant_id=cleaner_assistant_id,
                file_id=None,
                clean_response=False,
            )
            if not cleaned_text:
                logger.warning(f"(Анализ динамики) ❌ Вторая попытка очистки текста тоже не удалась — использую исходный текст без очистки")
                cleaned_text = raw_text # Используем исходный текст без очистки
        
    except Exception as e:
        logger.error(f"(Анализ динамики) ❌ Ошибка при попытке очистки текста: {e}")
        cleaned_text = raw_text  # Используем исходный текст без очистки
    
    logger.info(f"(Анализ динамики) ✅ Текст успешно очищен от мусора")
    print("--------------------------------------------")
    print(f"Полученный результат после очистки от мусора: {cleaned_text}")
    print("--------------------------------------------")
    
    # Теперь структурируем текст в соответствии с шаблоном
    prompt_structuring = f"""
                This is the report template:
                {template_text}
                This is the original medical report text:
                {cleaned_text}
                """
   
    try:
        result_text = _process_openai_request(
            text=prompt_structuring,
            assistant_id=structurer_assistant_id,
            file_id=None,
            clean_response=False,
        )
    except Exception as e:
        logger.error(f"(Анализ динамики) ❌ Ошибка вызова OpenAI: {e}")
        # Вторая попытка на случай временной ошибки
        try:
            result_text = _process_openai_request(
                text=prompt_structuring,
                assistant_id=structurer_assistant_id,
                file_id=None,
                clean_response=False,
            )
            logger.info("(Анализ динамики) ✅ 2️⃣ Вторая попытка вызова OpenAI прошла успешно")
        except Exception as e2:
            logger.error(f"(Анализ динамики) ❌❌ 2️⃣ Повторная попытка тоже не удалась: {e2}")
            return jsonify({
                "status": "error",
                "message": f"Ошибка при повторной попытке вызова OpenAI: {e2}"
            }), 500

    print("--------------------------------------------")
    print(f"Полученный результат после системного структурирования: {result_text}")
    print("--------------------------------------------")
    parsed = json.loads(result_text)
    result = parsed.get("items", [])
    try:
        # Восстанавливаю структуру параграфов из результата по skeleton. Тут не ожидаю ошибок.
        merged_parag, misc_sentences = merge_ai_response_into_skeleton(skeleton, result)
        # Это первая попытка замены предложений в параграфах 
        initial_report = replace_head_sentences_with_fuzzy_check(sorted_parag, merged_parag)
        logger.info("(Анализ динамики) ✅ Удалось исправить структуру и заменить предложения с первой попытки 1️⃣.")

        new_html = render_template(
            "working_with_report.html",
            title=report_data["report_name"],
            report_data=report_data,
            paragraphs_data=initial_report,
            key_words_groups=key_words_groups,
        )
        print(misc_sentences)
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
        error_message = str(e)
        logger.error(f"(Анализ динамики) ❌ Ошибка при изменении структуры отчета и замене предложений: {error_message}")

        try:
            # Вторая попытка структурирования отчета
            retry_prompt = f"""
                            The following error occurred while analyzing the generated report structure:
                            {error_message}
                            Ensure that you use only the information from the original medical report and the given template.
                            """
            retry_response = _process_openai_request(
                text=retry_prompt,
                assistant_id=structurer_assistant_id,
                file_id=None,
                clean_response=False
            )
            
            print("--------------------------------------------")
            print(f"Полученный результат структурирования, вторая попытка: {retry_response}")
            print("--------------------------------------------")
            
            parsed_retry = json.loads(retry_response)
            result = parsed_retry.get("items", [])
            
            try:
                # Восстанавливаю структуру параграфов из результата по skeleton (вторая попытка).
                merged_parag, misc_sentences = merge_ai_response_into_skeleton(skeleton, result)
                # Вторая попытка замены предложений в параграфах
                initial_report = replace_head_sentences_with_fuzzy_check(sorted_parag, merged_parag)
                logger.info("(Анализ динамики) ✅ Удалось исправить структуру и заменить предложения со второй попытки.")
            except Exception as e3:
                logger.error(f"(Анализ динамики) ❌ Ошибка при повторной попытке замены предложений: {e3}")
                return jsonify({"status": "error", "message": f"Ошибка при повторной попытке замены предложений: {e3}"}), 500
            
            new_html = render_template(
                "working_with_report.html",
                title=report_data["report_name"],
                report_data=report_data,
                paragraphs_data=initial_report,
                key_words_groups=key_words_groups,
            )
            print(misc_sentences)
            return jsonify({
                "status": "success",
                "message": "Структура отчета успешно обновлена после повторной попытки",
                "report_data": report_data,
                "paragraphs_data": initial_report,
                "key_words_groups": key_words_groups,
                "html": new_html,
                "misc_sentences": misc_sentences,
            }), 200
        except Exception as e2:
            logger.error(f"(Анализ динамики) ❌ Ошибка при повторной попытке после корректировки ассистентом: {e2}")
            return jsonify({"status": "error", "message": f"Ошибка даже после повторной попытки: {e2}. Не получилось синтезировать протокол"}), 500
    finally:
        reset_ai_session(assistant_id=structurer_assistant_id)
        reset_ai_session(assistant_id=cleaner_assistant_id)
        logger.info(f"(Анализ динамики) 📌 Сессии ассистентов OpenAI успешно сброшены")
        
        


@working_with_reports_bp.route("/ocr_extract_text", methods=["POST"])
@auth_required()
def ocr_extract_text():
    logger.info(f"(Извлечение текста из загруженного файла) ------------------------------------")
    logger.info(f"(Извлечение текста из загруженного файла) 🚀 Начинаю обработку запроса на извлечение текста из загруженного файла")
    try:
        file = request.files.get("file")
        if not file:
            logger.error(f"(Извлечение текста из загруженного файла) ❌ Не получен файл для обработки")
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        from file_processing import extract_text_from_uploaded_file
        text, error = extract_text_from_uploaded_file(file)
        if error:
            # Если pdf — отдать код 200, но сообщить что не поддерживается
            if "PDF files are not supported" in error:
                logger.info(f"(Извлечение текста из загруженного файла) 📄 PDF файл не поддерживается")
                return jsonify({"status": "success", "text": "", "message": error}), 200
            logger.error(f"(Извлечение текста из загруженного файла) ❌ Ошибка при извлечении текста: {error}")
            return jsonify({"status": "error", "message": error}), 400
        logger.info(f"(Извлечение текста из загруженного файла) ✅ Текст успешно извлечен")
        return jsonify({"status": "success", "text": text}), 200
    except Exception as e:
        logger.error(f"(Извлечение текста из загруженного файла) ❌ Ошибка при обработке файла: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500