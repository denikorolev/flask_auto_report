#working_with_reports.py

from flask import Blueprint, render_template, request, jsonify, send_file, g
import os
from models import db, Report, ReportType, Paragraph, Sentence, KeyWord
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
    current_profile = g.current_profile
    report_types_and_subtypes = ReportType.get_types_with_subtypes(current_profile.id) 
    current_profile_reports = Report.find_by_profile(current_profile.id)

    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            rep_type = data.get("report_type")
            rep_subtype = data.get("report_subtype")
            reports = Report.find_by_subtypes(rep_subtype)

            # Возвращаем данные в формате JSON
            return jsonify({
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
        report_data = Report.get_report_data(
            current_report_id, 
            g.current_profile.id
            )
    except Exception as e:
        return render_template("error.html", message=f"An error occurred: {e}")
    
        
    # Получаем ключевые слова для текущего пользователя
    
    key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, current_report_id)
    key_words_groups = group_keywords(key_words_obj)
    
    
    return render_template(
        "working_with_report.html", 
        title=report_data["report"]["report_name"],
        report_data=report_data,
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number,
        key_words_groups=key_words_groups               
    )


# @working_with_reports_bp.route("/update_sentence", methods=['POST'])
# @auth_required()
# def update_sentence():
#     data = request.get_json()
#     sentence_id = data.get('sentence_id')
#     new_value = data.get('new_value')

#     sentence = Sentence.query.get(sentence_id)
#     if sentence:
#         sentence.sentence = new_value
#         sentence.save(old_index=sentence.index)
#         return jsonify({"status": "success", "message": "Предложение успешно обновлено!"}), 200
#     return jsonify({"status": "error", "message": "Ошибка при обновлении данных предложения."}), 400


@working_with_reports_bp.route("/get_sentences_with_type_tail", methods=["POST"])
@auth_required()
def get_sentences_with_type_tail():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    
    if not paragraph_id:
        logger.warning("В запресе нет данных по ID параграфа")
        return jsonify({"status": "error", "message": "В запросе отсутствует информация по ID параграфа для запрашиваемых предложений"}), 400
    
    tail_sentences = Sentence.get_sentences_by_type(paragraph_id=paragraph_id, sentence_type="tail")

    if tail_sentences:
        sentences_data = [{"id": sentence.id, "sentence": sentence.sentence} for sentence in tail_sentences]
        logger.info(f"Found {len(sentences_data)} sentences with type 'tail' for paragraph {paragraph_id}")
        return jsonify({"sentences": sentences_data}), 200
    return jsonify({"sentences": []}), 200


# @working_with_reports_bp.route("/new_sentence_adding", methods=["POST"])
# @auth_required()
# def new_sentence_adding():
#     try:
#         data = request.get_json()
#         paragraphs = data.get("paragraphs", [])
        
#         if not paragraphs:
#             return jsonify({"status": "error", "message": "No paragraphs provided."}), 400

#         # Разбиваем предложения на более мелкие и получаем новые предложения
#         processed_paragraphs = split_sentences(paragraphs)
#         new_sentences = get_new_sentences(processed_paragraphs)
        
#         # Возвращаем новые предложения на клиентскую часть
#         return jsonify({"status": "success", "processed_paragraphs": new_sentences}), 200

#     except Exception as e:
#         logger.error(f"Произошла ошибка при добавлении нового предложения: {e}")
#         return jsonify({"status": "error", "message": f"Ошибка при добавлении предложения: {e}"}), 500
    

@working_with_reports_bp.route("/save_modified_sentences", methods=["POST"])
@auth_required()
def save_modified_sentences():
    """
    Processes and saves new or modified sentences to the database.
    Handles splitting of multi-sentence inputs and normalizes valid sentences.
    Keeps track of saved, skipped, and missed sentences.
    """
    try:
        # Получаем данные из запроса
        data = request.get_json()

        if not data or "sentences" not in data:
            return jsonify({"status": "error", "message": "Invalid data format"}), 400

        sentences = ensure_list(data.get("sentences"))
        report_id = data.get("report_id")
        
        if not sentences or not report_id:
            return jsonify({"status": "error", "message": "Some required data is missing."}), 400
        
        processed_sentences = []  # Для хранения обработанных предложений
        missed_count = 0  # Счётчик пропущенных предложений

        for sentence_data in sentences:
            paragraph_id = sentence_data.get("paragraph_id")
            sentence_index = sentence_data.get("sentence_index")
            nativ_text = sentence_data.get("text")
            sentence_type = sentence_data.get("type")

            # Проверяем корректность данных
            if not paragraph_id or not nativ_text.strip() or sentence_index is None:
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
                        "sentence_index": int(sentence_index) if idx == 0 else 0,
                        "sentence_type": "tail" if sentence_type == "tail" else "body",
                        "text": splited_sentence.strip()
                    })
            else:
                for unsplited_sentence in unsplited_sentences:
                    processed_sentences.append({
                        "paragraph_id": paragraph_id,
                        "sentence_index": int(sentence_index),
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
            sentence_index = sentence["sentence_index"]
            new_sentence_text = clean_and_normalize_text(sentence["text"])
            sentence_type = sentence["sentence_type"]
            logger.info(f"New sentence: {new_sentence_text}")
            try:
                # Сохраняем предложение в базу данных
                new_sentence = Sentence.create(
                    paragraph_id=paragraph_id,
                    index=sentence_index,
                    weight=10,  # Вес по умолчанию
                    sentence_type=sentence_type,
                    tags="",
                    comment="Added automatically",
                    sentence=new_sentence_text
                )
                saved_count += 1
                saved_sentences.append({"id": new_sentence.id, "text": new_sentence_text})
            except Exception as e:
                print(f"Failed to save sentence: {new_sentence_text}. Error: {e}")
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
            "message": f"Processed {len(processed_sentences)} sentences.",
            "html": rendered_html
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


    
# @working_with_reports_bp.route("/add_sentence_to_paragraph", methods=["POST"])
# @auth_required()
# def add_sentence_to_paragraph():
#     try:
#         data = request.get_json()
#         sentence_for_adding = data.get("sentence_for_adding", [])

#         if not sentence_for_adding:
#             return jsonify({"status": "error", "message": "Отсутствуют данные абзацев."}), 400

#         # Перебираем каждый элемент списка абзацев
#         for paragraph in sentence_for_adding:
#             paragraph_id = paragraph.get("paragraph_id")
#             sentences = paragraph.get("sentences")

#             if not paragraph_id or not sentences:
#                 continue  # Пропускаем, если отсутствуют необходимые данные

#             # Используем ensure_list, чтобы всегда иметь список предложений
#             sentences_list = ensure_list(sentences)

#             # Перебираем список предложений и добавляем их в базу данных
#             for sentence_text in sentences_list:
#                 if sentence_text:
#                     Sentence.create(paragraph_id=paragraph_id, 
#                                     index=0, 
#                                     weight=10, # Вес по умолчанию
#                                     sentence_type="tail",
#                                     tags="",
#                                     comment="", 
#                                     sentence=sentence_text
#                                     )

#         db.session.commit()  # Сохраняем все изменения в базе данных

#         return jsonify({"status": "success", "message": "Все предложения успешно добавлены!"}), 200
#     except Exception as e:
#         return jsonify({"status": "error", "message": f"Не удалось добавить предложения: {e}"}), 500


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



    

