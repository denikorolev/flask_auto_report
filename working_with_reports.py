#working_with_reports.py
#v0.1.0

from flask import Blueprint, render_template, request, current_app, jsonify, send_file, flash, url_for
from flask_login import login_required, current_user
import os
from models import db, Report, ReportType, ReportSubtype, ReportParagraph, Sentence, KeyWordsGroup
from file_processing import save_to_word
from calculating import calculate_age
from sentence_processing import split_sentences, get_new_sentences, group_key_words_by_index
from errors_processing import print_object_structure
from collections import defaultdict
from openai import OpenAI 


working_with_reports_bp = Blueprint('working_with_reports', __name__)

# Functions

def ease_group_keywords_by_index(keywords):
    """
    Функция для группировки ключевых слов по group_index.
    
    :param keywords: список объектов KeyWordsGroup
    :return: список списков, где ключевые слова сгруппированы по одинаковому group_index
    """
    grouped_keywords = defaultdict(list)

    # Проход по списку объектов и добавление слов в соответствующие группы
    for keyword in keywords:
        grouped_keywords[keyword.group_index].append(keyword.key_word)

    # Преобразование словаря в список списков
    return list(grouped_keywords.values())


def init_app(app):
    menu = app.config['MENU']
    return menu

def get_user_reports():
    user_reports = Report.query.filter_by(userid=current_user.id).all()
    return user_reports

# Routes

@working_with_reports_bp.route("/choosing_report", methods=['POST', 'GET'])
@login_required
def choosing_report(): 
    menu = init_app(current_app)
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    user_reports = get_user_reports()
    
    if request.method == "POST":
        if "select_report_type_subtype" in request.form:
            rep_type = request.form["report_type"]
            rep_subtype = request.form["report_subtype"]
            reports = Report.query.filter_by(userid=current_user.id, report_type=rep_type, report_subtype=rep_subtype).all()
            return render_template(
                "choose_report.html",
                title="Report",
                menu=menu,
                user_reports=user_reports,
                report_types=report_types,
                report_subtypes=report_subtypes,
                reports=reports
            )
        
    return render_template(
        "choose_report.html",
        title="Report",
        menu=menu,
        user_reports=user_reports,
        report_types=report_types,
        report_subtypes=report_subtypes
    )

@working_with_reports_bp.route("/working_with_reports", methods=['POST', 'GET'])
@login_required
def working_with_reports(): 
    menu = init_app(current_app)
    current_report_id = request.args.get("report_id")
    # Получаем ключевые слова для текущего пользователя
    
    easy_key = KeyWordsGroup.get_keywords_for_report(current_user.id, current_report_id)
    key_words_group = ease_group_keywords_by_index(easy_key)

    # Для отладки
    print(key_words_group)
    # print_object_structure(easy_key)        
        
    if request.method == "POST":
        data = request.get_json()
        full_name = data.get("fullname", "")
        birthdate = data.get("birthdate", "")
        report_number = data.get("reportNumber", "")
        report_id = data.get("reportId")
        if report_id:
            return jsonify({"redirect_url": url_for('working_with_reports.working_with_reports', report_id=report_id, full_name=full_name, birthdate=birthdate, reportNumber=report_number)})
        else:
            return jsonify({"message": "Invalid report ID."}), 400
        
    report = Report.query.get(current_report_id) 
    full_name = request.args.get("full_name", "")
    birthdate = request.args.get("birthdate", "")
    report_number = request.args.get("reportNumber", "")
    paragraphs = ReportParagraph.query.filter_by(report_id=report.id).order_by(ReportParagraph.paragraph_index).all()
    subtype = report.report_subtype_rel.subtype
    report_type = report.report_type_rel.type
    paragraph_data = []
    for paragraph in paragraphs:
        sentences = Sentence.query.filter_by(paragraph_id=paragraph.id).order_by(Sentence.index, Sentence.weight).all()
        
        grouped_sentences = {}
        for sentence in sentences:
            index = sentence.index
            if index not in grouped_sentences:
                grouped_sentences[index] = []
            grouped_sentences[index].append(sentence)
            
        paragraph_data.append({
            "paragraph": paragraph,
            "grouped_sentences": grouped_sentences
        })
                
    return render_template(
        "working_with_report.html", 
        title=report.report_name,
        menu=menu,
        report=report,
        paragraph_data=paragraph_data,
        subtype=subtype,
        report_type=report_type,
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number,
        key_words=key_words_group                 
    )

@working_with_reports_bp.route("/update_sentence", methods=['POST'])
@login_required
def update_sentence():
    data = request.get_json()
    sentence_id = data.get('sentence_id')
    new_value = data.get('new_value')

    sentence = Sentence.query.get(sentence_id)
    if sentence:
        sentence.sentence = new_value
        db.session.commit()
        return jsonify({"message": "Sentence updated successfully!"}), 200
    return jsonify({"message": "Failed to update sentence."}), 400




@working_with_reports_bp.route("/update_paragraph", methods=["POST"])
@login_required
def update_paragraph():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    new_value = data.get("new_value")

    paragraph = ReportParagraph.query.get(paragraph_id)
    if paragraph:
        paragraph.paragraph = new_value
        db.session.commit()
        return jsonify({"message": "Paragraph updated successfully!"}), 200
    return jsonify({"message": "Failed to update paragraph."}), 400


@working_with_reports_bp.route("/get_sentences_with_index_zero", methods=["POST"])
@login_required
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
@login_required
def new_sentence_adding():
    try:
        data = request.get_json()
        paragraphs = data.get("paragraphs", [])

        if not paragraphs:
            return jsonify({"message": "No paragraphs provided."}), 400

        # Разбиваем предложения на более мелкие и получаем новые предложения
        processed_paragraphs = split_sentences(paragraphs)
        new_sentences = get_new_sentences(processed_paragraphs)

        # Возвращаем новые предложения на клиентскую часть
        return jsonify({"processed_paragraphs": new_sentences}), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({"message": f"Unexpected error: {e}"}), 500
    
    
@working_with_reports_bp.route("/add_sentence_to_paragraph", methods=["POST"])
@login_required
def add_sentence_to_paragraph():
    try:
        data = request.get_json()
        paragraph_id = data.get("paragraph_id")
        sentence_text = data.get("sentence_text")

        if not paragraph_id or not sentence_text:
            return jsonify({"message": "Missing required data."}), 400

        # Добавляем новое предложение в БД с индексом 0, весом 1, пустым комментарием
        Sentence.create(paragraph_id=paragraph_id, index=0, weight=1, comment="", sentence=sentence_text)

        return jsonify({"message": "Sentence added successfully!"}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to add sentence: {e}")
        return jsonify({"message": f"Failed to add sentence: {e}"}), 500



@working_with_reports_bp.route("/export_to_word", methods=["POST"])
@login_required
def export_to_word():
    try:
        data = request.get_json()
        if data is None:
                return jsonify({"message": "No JSON data received"}), 400
        text = data.get("text")
        name = data.get("name")
        subtype = data.get("subtype")
        report_type = data.get("report_type")
        birthdate = data.get("birthdate")
        reportnumber = data.get("reportnumber")
        scanParam = data.get("scanParam")
        side = data.get("side")

        if not text or not name or not subtype:
            return jsonify({"message": "Missing required information."}), 400
    except Exception as e:
        return jsonify({"message": f"Error processing request: {e}"}), 500

    try:
        file_path = save_to_word(text, name, subtype, report_type, birthdate, reportnumber, scanParam, side=side)
        # Проверяем, существует ли файл
        if not os.path.exists(file_path):
            return jsonify({"message": "File not found"}), 500
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"message": f"Failed to export to Word: {e}"}), 500


@working_with_reports_bp.route("/generate_impression", methods=['POST'])
@login_required
def generate_impression():
    try:
        data = request.get_json()
        text = data.get("text")
        birthdate_str = data.get("birthdate")
        gender = data.get("gender", "Нет данных")
        report_type = data.get("report_type")

        if not text or not birthdate_str or not report_type:
            return jsonify({"message": "Missing required information."}), 400
        age = calculate_age(birthdate_str)
        if not age:
            return jsonify({"message": "Invalid birthdate format. Expected format: YYYY-MM-DD"}), 400

        # Подготовка промпта для GPT
        user_prompt = (
            f"Пациент: {gender}, возраст: {age} лет.\n"
            f"Тип отчета: {report_type}.\n"
            f"Протокол исследования:\n{text}"
        )
        
        system_prompt = (f"You are a professional radiologist speaking only Russian. Your role is to assist users in creating impressions based on provided MRI descriptions. You focus on making concise impressions for MRI reports. Your responses should be formal, clear, and precise, adhering to medical terminology standards. If there are several possible diagnoses or syndromes based on the provided descriptions, you should first mention the most likely one and then list the others in parentheses, separated by commas. When formulating a diagnosis or syndrome, adhere to the following probability classification: for 'almost certain,' state the diagnosis directly; for 'very likely,' use 'MRI findings are suggestive of...'; for 'likely,' use 'MRI findings may correspond to...'; and for '50/50' use 'MRI findings could indicate...'. Do not repeat anything from the provided description in your response, and avoid mentioning normal findings or detailed descriptions of abnormalities. Only include diagnoses or syndromes that belong in the 'Impression' section of the report.")

        # Установка API ключа и модели
        api_key = current_app.config.get('OPENAI_API_KEY')
        api_model = current_app.config.get('OPENAI_MODEL')
        # api_assistant = "asst_IpRMfZnbJXW0IalVVslKin17" check it later

        if not api_key:
            return jsonify({"message": "OpenAI API key is not configured."}), 500

        # Вызов OpenAI API
        client = OpenAI(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
            "role": "user", "content": user_prompt,
        },
                {
                    "role": "system", "content": system_prompt
                }
              ],  model=api_model
        )

       
        # Извлечение первого (и единственного) выбора
        first_choice = chat_completion.choices[0]

        # Извлечение текста сообщения
        message_content = first_choice.message.content
        return jsonify({"impression": message_content}), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({"message": f"Unexpected error: {e}"}), 500
    

