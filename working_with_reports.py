#working_with_reports.py

from flask import Blueprint, render_template, request, current_app, jsonify, send_file, g
import os
from models import db, Report, ReportType, Paragraph, Sentence, KeyWord
from file_processing import save_to_word
from sentence_processing import split_sentences, get_new_sentences, group_keywords
from errors_processing import print_object_structure
from utils import ensure_list
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
        title="Report",
        user_reports=current_profile_reports,
        report_types_and_subtypes=report_types_and_subtypes
    )


@working_with_reports_bp.route("/working_with_reports", methods=['POST', 'GET'])
@auth_required()
def working_with_reports(): 
    current_report_id = request.args.get("reportId")
    full_name = request.args.get("fullname")
    birthdate = request.args.get("birthdate")
    report_number = request.args.get("reportNumber")
    
    report_data = Report.get_report_data(
        current_report_id, 
        g.current_profile.id
        )
    if not report_data:
        print("there is no report_data")
        
    # Получаем ключевые слова для текущего пользователя
    
    key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, current_report_id)
    key_words_group = group_keywords(key_words_obj)
    print(key_words_group)
    
    return render_template(
        "working_with_report.html", 
        title=report_data["report"]["report_name"],
        # menu=menu,
        report_data=report_data,
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number,
        key_words=key_words_group                 
    )


@working_with_reports_bp.route("/update_sentence", methods=['POST'])
@auth_required()
def update_sentence():
    data = request.get_json()
    sentence_id = data.get('sentence_id')
    new_value = data.get('new_value')

    sentence = Sentence.query.get(sentence_id)
    if sentence:
        sentence.sentence = new_value
        db.session.commit()
        return jsonify({"status": "success", "message": "Sentence updated successfully!"}), 200
    return jsonify({"status": "error", "message": "Failed to update sentence."}), 400


@working_with_reports_bp.route("/get_sentences_with_index_zero", methods=["POST"])
@auth_required()
def get_sentences_with_index_zero():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")

    # Получаем предложения с индексом 0
    sentences = Sentence.query.filter_by(paragraph_id=paragraph_id, index=0).all()

    if sentences:
        sentences_data = [{"id": sentence.id, "sentence": sentence.sentence} for sentence in sentences]
        return jsonify({"sentences": sentences_data}), 200
    return jsonify({"message": "No sentences found."}), 200


# Добавляем новое предложение с индексом 0
@working_with_reports_bp.route("/new_sentence_adding", methods=["POST"])
@auth_required()
def new_sentence_adding():
    try:
        data = request.get_json()
        paragraphs = data.get("paragraphs", [])

        
        
        if not paragraphs:
            return jsonify({"status": "error", "message": "No paragraphs provided."}), 400

        # Разбиваем предложения на более мелкие и получаем новые предложения
        processed_paragraphs = split_sentences(paragraphs)
        new_sentences = get_new_sentences(processed_paragraphs)
        
        # Возвращаем новые предложения на клиентскую часть
        return jsonify({"status": "success", "processed_paragraphs": new_sentences}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {e}"}), 500
    
    
# Сохраняем новые предложения в базу данных в автоматическом режиме учитывая индекс предложения
@working_with_reports_bp.route("/save_modified_sentences", methods=["POST"])
@auth_required()
def save_modified_sentences():
    """
    Processes and saves new or modified sentences to the database.
    """
    try:
        # Получаем данные из запроса
        data = request.get_json()

        if not data or "sentences" not in data:
            return jsonify({"status": "error", "message": "Invalid data format"}), 400

        sentences = data["sentences"]
        if not isinstance(sentences, list) or not sentences:
            return jsonify({"status": "error", "message": "No sentences provided"}), 400

        saved_count = 0  # Счётчик сохранённых предложений
        skipped_count = 0  # Счётчик пропущенных предложений
        saved_sentences = []  # Для хранения информации о сохранённых предложениях

        for sentence_data in sentences:
            paragraph_id = sentence_data.get("paragraph_id")
            sentence_index = sentence_data.get("sentence_index")
            text = sentence_data.get("text")

            # Проверяем корректность данных
            if not paragraph_id or not text or sentence_index is None:
                skipped_count += 1
                continue

            # Создаём новое предложение
            new_sentence = Sentence.create(
                paragraph_id=paragraph_id,
                index=int(sentence_index),  # Используем переданный индекс
                weight=10,  # Вес по умолчанию
                comment="Added automatically",  # Комментарий
                sentence=text
            )
            saved_sentences.append({"type": "added", "id": new_sentence.id})
            saved_count += 1

        return jsonify({
            "status": "success",
            "message": f"Processed {saved_count} sentences, skipped {skipped_count} sentences.",
            "saved_sentences": saved_sentences
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


    
@working_with_reports_bp.route("/add_sentence_to_paragraph", methods=["POST"])
@auth_required()
def add_sentence_to_paragraph():
    try:
        data = request.get_json()
        sentence_for_adding = data.get("sentence_for_adding", [])

        if not sentence_for_adding:
            return jsonify({"status": "error", "message": "Отсутствуют данные абзацев."}), 400

        # Перебираем каждый элемент списка абзацев
        for paragraph in sentence_for_adding:
            paragraph_id = paragraph.get("paragraph_id")
            sentences = paragraph.get("sentences")

            if not paragraph_id or not sentences:
                continue  # Пропускаем, если отсутствуют необходимые данные

            # Используем ensure_list, чтобы всегда иметь список предложений
            sentences_list = ensure_list(sentences)

            # Перебираем список предложений и добавляем их в базу данных
            for sentence_text in sentences_list:
                if sentence_text:
                    Sentence.create(paragraph_id=paragraph_id, index=0, weight=1, comment="", sentence=sentence_text)

        db.session.commit()  # Сохраняем все изменения в базе данных

        return jsonify({"status": "success", "message": "Все предложения успешно добавлены!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Не удалось добавить предложения: {e}"}), 500


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



    

