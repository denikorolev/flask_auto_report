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
    menu = current_app.config['MENU']
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
        menu=menu,
        user_reports=current_profile_reports,
        report_types_and_subtypes=report_types_and_subtypes
    )


@working_with_reports_bp.route("/working_with_reports", methods=['POST', 'GET'])
@auth_required()
def working_with_reports(): 
    menu = current_app.config['MENU']
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
    
    return render_template(
        "working_with_report.html", 
        title=report_data["report"]["report_name"],
        menu=menu,
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


@working_with_reports_bp.route("/update_paragraph", methods=["POST"])
@auth_required()
def update_paragraph():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    new_value = data.get("new_value")

    paragraph = Paragraph.query.get(paragraph_id)
    if paragraph:
        paragraph.paragraph = new_value
        db.session.commit()
        return jsonify({"message": "Paragraph updated successfully!"}), 200
    return jsonify({"message": "Failed to update paragraph."}), 400


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
        name = data.get("name")
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



    

