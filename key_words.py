# key_words.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from flask_login import current_user
from models import db, KeyWord, Report
from itertools import chain
from file_processing import file_uploader
from sentence_processing import group_keywords, sort_key_words_group, process_keywords, check_existing_keywords, extract_keywords_from_doc
from errors_processing import print_object_structure
from utils import ensure_list
from db_processing import add_keywords_to_db
from flask_security.decorators import auth_required

key_words_bp = Blueprint("key_words", __name__)


@key_words_bp.route("/key_words", methods=["POST","GET"])
@auth_required()
def key_words():
    menu=current_app.config["MENU"]
    current_profile_reports=Report.find_by_profile(g.current_profile.id)
    
    # Prepare global key words
    global_user_key_words = KeyWord.find_without_reports(g.current_profile.id)
    unsorted_global_key_words = group_keywords(global_user_key_words, with_index=True)
    global_key_words = sort_key_words_group(unsorted_global_key_words)
    # Prepare key words linked to reports
    uncleared_report_user_key_words = []
    for report in current_profile_reports:
        uncleared_report_user_key_words.append(KeyWord.find_by_report(report.id))
    report_user_key_words = list(chain.from_iterable(uncleared_report_user_key_words))
    
    report_key_words = group_keywords(report_user_key_words, with_report=True)
    
    return render_template("/key_words.html",
                           title="Key words",
                           menu=menu,
                           user_reports=current_profile_reports,
                           global_key_words=global_key_words,
                           report_key_words=report_key_words)
    
    
    


# Маршрут для добавления группы ключевых слов
@key_words_bp.route('/add_keywords', methods=['POST'])
@auth_required()
def add_keywords():
    data = request.get_json()
    key_word_input = data.get('key_word_input').strip()
    report_ids = data.get('report_ids', [])  # Получаем список отчетов или пустой список
    ignore_unique_check = data.get('ignore_unique_check', False)
    
    if not key_word_input:
        return {"status": "error", 
                "message": "No keywords provided."}, 400

    key_words = process_keywords(key_word_input)
    
    if not key_words:
        return {"status": "error", 
                "message": "Invalid keywords format."}, 400
    
    # Если флаг игнорирования уникальности не установлен, выполняем проверку
    if not ignore_unique_check:
        # Проверяем, какие ключевые слова уже существуют у пользователя
        existing_keywords_message = check_existing_keywords(key_words)
        
        # Если хотя бы одно ключевое слово уже существует, возвращаем ошибку
        if existing_keywords_message:
            return {"status": "error", "message": existing_keywords_message}, 400
    
    # Добавляем ключевые слова в базу данных
    add_keywords_to_db(key_words, report_ids)

    return {"status": "success"}, 200


# Маршрут для добавления групп ключевых слов из файла word
@auth_required()
@key_words_bp.route('/upload_keywords_from_word', methods=['POST'])
def upload_keywords_from_word():
    
    # Логика загрузки файла
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    # Загружаем файл с помощью функции file_uploader и получаем сразу 2 переменные ответ и путь
    upload_result, file_path = file_uploader(file, "doc")
    if "successfully" not in upload_result:
        return jsonify({"status": "error", "message": upload_result}), 400
    if not file_path:
        return jsonify({"status": "error", "message": "File upload failed. No valid file path."}), 400

    # Остальная логика
    ignore_unique_check = request.form.get('ignore_unique_check', 'false').lower() == 'true'
    # Извлекаем ключевые слова из документа
    keywords = extract_keywords_from_doc(file_path)

    all_keywords = []
    for group in keywords:
        all_keywords.extend(group['key_words'])
        
    # Если флаг игнорирования уникальности не установлен, выполняем проверку
    if not ignore_unique_check:
        # Проверяем, какие ключевые слова уже существуют у пользователя
        existing_keywords_message = check_existing_keywords(all_keywords)

        # Если есть дублирующиеся ключевые слова, возвращаем сообщение об ошибке
        if existing_keywords_message:
            return jsonify({"status": "error", "message": existing_keywords_message}), 400

    # Добавляем ключевые слова в базу данных
    for group in keywords:
        report_ids = ensure_list(group['report_id'])
        key_words = group['key_words']

        add_keywords_to_db(key_words, report_ids)

    return jsonify({"status": "success", "message": "Keywords from Word document successfully uploaded"}), 200


# Маршрут для добавления одного или нескольких ключевых слов в уже существующую группу
@key_words_bp.route('/add_word_to_exist_group', methods=['POST'])
@auth_required()
def add_word_to_exist_group():
    data = request.json
    group_index = data.get("group_index")
    reports = ensure_list(data.get("report_id"))
    key_word_input = data.get("key_word_input", "").strip()
    if not group_index:
        return {"status": "error", "message": "Group index is required"}, 400

    if not key_word_input:
        return {"status": "error", "message": "No keywords provided"}, 400

    # Вынесем общую логику обработки ключевых слов в отдельную функцию
    key_words = process_keywords(key_word_input)

    if not key_words:
        return {"status": "error", "message": "Invalid keywords format"}, 400

    # Подсчитываем количество существующих ключевых слов в конкретной группе
    num_of_exist_key_words = len(KeyWord.query.filter_by(group_index=group_index, profile_id=g.current_profile.id).all())

        
    # Добавляем ключевые слова в нужную группу
    for i, key_word in enumerate(key_words, start=1):
        KeyWord.create(
            group_index=group_index,
            index=num_of_exist_key_words + i,
            key_word=key_word,
            profile_id=g.current_profile.id,
            reports=reports
        )
    db.session.commit()

    return {"status": "success", "message": "Keywords added successfully"}, 200


# Маршрут для удаления группы ключевых слов
@key_words_bp.route('/delete_keywords', methods=['POST'])
@auth_required()
def delete_keywords():
    group_index = request.json.get("group_index")

    if not group_index:
        return jsonify({"status": "error", "message": "Group index is required"}), 400

    # Удаление всех ключевых слов с данным group_index для текущего пользователя
    KeyWord.query.filter_by(group_index=group_index, profile_id=g.current_profile.id).delete()
    db.session.commit()

    return jsonify({"status": "success", "message": "Keywords group deleted successfully"}), 200


# Отвязываем группу ключевых слов от конкретного отчета
@key_words_bp.route('/unlink_keyword_from_report', methods=['POST'])
@auth_required()
def unlink_keyword_from_report():
    data = request.json
    group_index = data.get("group_index")
    report_id = data.get("report_id")
    if not group_index or not report_id:
        return jsonify({"status": "error", "message": "Group index and report ID are required"}), 400

    # Найдем ключевые слова в этой группе, связанные с данным отчетом
    keywords = KeyWord.find_by_group_index(group_index, g.current_profile.id)
    if not keywords:
        return jsonify({"status": "error", "message": "No keywords found for this group"}), 404

    # Получаем объект отчета по report_id
    report = Report.query.get(report_id)
    
    if not report:
        return jsonify({"status": "error", "message": "Report not found"}), 404

    # Убираем связь ключевых слов с данным отчетом
    for keyword in keywords:
        if report in keyword.key_word_reports:
            keyword.key_word_reports.remove(report)


    db.session.commit()

    return jsonify({"status": "success", "message": "Keywords unlinked from report successfully"}), 200


@key_words_bp.route('/edit_keywords', methods=['POST'])
@auth_required()
def edit_keywords():
    data = request.json
    key_words = data.get("key_words")

    if not key_words:
        return jsonify({"status": "error", "message": "Words are required"}), 400

    for word in key_words:
        word_id = word.get("id")
        key_word = word.get("word")

        if not key_word:
            # Если ключевое слово пустое, удаляем его
            word_for_delete = KeyWord.query.get(word_id)
            word_for_delete.delete()
            
        else:
            # Если ключевое слово есть, обновляем его
            keyword_entry = KeyWord.query.get(word_id)
            if keyword_entry:
                keyword_entry.key_word = key_word

    db.session.commit()

    return jsonify({"status": "success", "message": "Keywords updated successfully"}), 200
