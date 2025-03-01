#working_with_reports.py

from flask import Blueprint, render_template, request, jsonify, send_file, g
from flask_security import current_user
import os
from models import db, Report, ReportType, KeyWord, TailSentence, BodySentence
from file_processing import save_to_word
from sentence_processing import group_keywords, split_sentences_if_needed, clean_and_normalize_text, compare_sentences_by_paragraph, preprocess_sentence
from utils import ensure_list
from logger import logger
from flask_security.decorators import auth_required


working_with_reports_bp = Blueprint('working_with_reports', __name__)

# Functions

# Routes

@working_with_reports_bp.route("/choosing_report", methods=['POST', 'GET'])
@auth_required()
def choosing_report(): 
    logger.info("Выбор шаблона протокола")
    current_profile = g.current_profile
    report_types_and_subtypes = ReportType.get_types_with_subtypes(current_profile.id) 
    current_profile_reports = Report.find_by_profile(current_profile.id)

    if request.method == "POST":
        logger.info("Получен POST-запрос на выбор шаблона протокола текущего профиля")
        if request.is_json:
            data = request.get_json()
            rep_subtype = data.get("report_subtype")
            reports = Report.find_by_subtypes(rep_subtype)
            if not reports:
                return jsonify({"status": "error", "message": "Не найдено шаблонов протоколов для выбранного типа"}), 404
            # Возвращаем данные в формате JSON
            return jsonify({
                "status": "success",
                "reports": [
                    {"id": report.id, "report_name": report.report_name}
                    for report in reports
                ]
            })
        
    return render_template(
        "choose_report.html",
        title="Выбор шаблона протокола",
        user_reports=current_profile_reports,
        report_types_and_subtypes=report_types_and_subtypes
    )


@working_with_reports_bp.route("/working_with_reports", methods=['GET'])
@auth_required()
def working_with_reports(): 
    current_report_id = request.args.get("reportId")
    full_name = request.args.get("fullname")
    birthdate = request.args.get("birthdate")
    report_number = request.args.get("reportNumber")
    
    
    try:
        report_data, paragraphs_data = Report.get_report_data(
            current_report_id, 
            g.current_profile.id
            )
        if report_data is None or paragraphs_data is None:
            logger.error("Метод get_report_data вернул None")
            return render_template("error.html", message="Метод get_report_data вернул None")
    except Exception as e:
        logger.error(f"Не получилось сгруппировать данные протокола или данные его параграфов: {e}")
        return render_template("error.html", message=f"Не получилось сгруппировать данные протокола или данные его параграфов: {e}")
    
        
    # Получаем ключевые слова для текущего пользователя
    
    key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, current_report_id)
    key_words_groups = group_keywords(key_words_obj)
    
    
    return render_template(
        "working_with_report.html", 
        title=report_data["report_name"],
        report_data=report_data,
        paragraphs_data=paragraphs_data,
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number,
        key_words_groups=key_words_groups
    )


@working_with_reports_bp.route("/save_modified_sentences", methods=["POST"])
@auth_required()
def save_modified_sentences():
    """
    Processes and saves new or modified sentences to the database.
    Handles splitting of multi-sentence inputs and normalizes valid sentences.
    Keeps track of saved, skipped, and missed sentences.
    """
    logger.info("Начало попытки сохранения измененных предложений")
    try:
        # Получаем данные из запроса
        data = request.get_json()
        logger.debug(f"Полученные данные: {data}")

        if not data or "sentences" not in data:
            return jsonify({"status": "error", "message": "Неправильный формат данных"}), 400

        sentences = ensure_list(data.get("sentences"))
        report_id = int(data.get("report_id"))
        user_id = current_user.id
        report_type_id = Report.get_report_type(report_id)
        print(report_type_id)
        
        if not sentences or not report_id:
            return jsonify({"status": "error", "message": "Пропущена часть необходимых данных. Не хватает текстов предложений или id протокола"}), 400
        
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
                continue  # Пропускаем некорректные предложения
            
            before_split_text = preprocess_sentence(nativ_text)
            
            if not before_split_text.strip():
                missed_count += 1
                continue  # Пропускаем некорректное предложение
            
            # Проверяем текст на наличие нескольких предложений
            unsplited_sentences, splited_sentences = split_sentences_if_needed(before_split_text)

            if splited_sentences:
                # Обрабатываем случаи с разделением
                for idx, splited_sentence in enumerate(splited_sentences):
                    processed_sentences.append({
                        "paragraph_id": paragraph_id,
                        "head_sentence_id": head_sentence_id,
                        "sentence_type": "body" if idx == 0 else "tail",
                        "text": splited_sentence.strip()
                    })
            else:
                for unsplited_sentence in unsplited_sentences:
                    processed_sentences.append({
                        "paragraph_id": paragraph_id,
                        "head_sentence_id": head_sentence_id,
                        "sentence_type": "tail" if sentence_type == "tail" else "body",
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
            paragraph_id = sentence["paragraph_id"]
            new_sentence_text = clean_and_normalize_text(sentence["text"])
            sentence_type = sentence["sentence_type"]
            try:
                if sentence_type == "tail":
                   new_sentence, _ = TailSentence.create(
                        sentence=new_sentence_text,
                        related_id=paragraph_id,
                        user_id=user_id,
                        report_type_id=report_type_id,
                        comment="Added automatically"
                    )
                # Сохраняем предложение в базу данных в качестве body_sentence 
                # для текущего главного предложения
                else:
                    if sentence["head_sentence_id"]:
                        new_sentence, _ = BodySentence.create(
                        sentence=new_sentence_text,
                        related_id=head_sentence_id,
                        user_id=user_id,
                        report_type_id=report_type_id,
                        comment="Added automatically",
                        )
                    else:
                        logger.warning(f"Не удалось получить данные по id главного предложения для предложения: {new_sentence_text}. Пропускаем.")
                        missed_count += 1   
                        continue
                saved_count += 1
                saved_sentences.append({"id": new_sentence.id, "text": new_sentence_text})
            except Exception as e:
                logger.error(f"Ошибка при сохранении предложения: {str(e)}")
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
        
        return jsonify({
            "status": "success",
            "message": f"Проанализировано {len(processed_sentences)} предложений.",
            "html": rendered_html
        }), 200

    except Exception as e:
        print(e)
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



    

