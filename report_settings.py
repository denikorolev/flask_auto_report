# report_settings.py

from flask import Blueprint, render_template, request, redirect, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db, ReportType, ReportSubtype, KeyWordsGroup, Report, ParagraphType 
from itertools import chain
from file_processing import file_uploader, allowed_file
from sentence_processing import group_keywords, sort_key_words_group, process_keywords, check_existing_keywords, extract_keywords_from_doc
from errors_processing import print_object_structure
from utils import ensure_list, get_max_index
from db_processing import add_keywords_to_db

report_settings_bp = Blueprint('report_settings', __name__)

# Functions


# Routs
# Главный маршрут страницы
@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    page_title = "Report settings"
    # Get data from the config
    menu = current_app.config["MENU"]
    # Get all user reports
    user_reports = Report.find_by_user(current_user.id)
    
    # Get types
    user_types = ReportType.find_by_user(current_user.id)
    
    # Get subtypes
    user_subtypes = ReportSubtype.find_by_user(current_user.id)
    
    # Get all paragraph types
    paragraph_types = ParagraphType.query.all() 
    
    # Prepare global key words
    global_user_key_words = KeyWordsGroup.find_without_reports(current_user.id)
    unsorted_global_key_words = group_keywords(global_user_key_words, with_index=True)
    global_key_words = sort_key_words_group(unsorted_global_key_words)
    # Prepare key words linked to reports
    uncleared_report_user_key_words = []
    for report in user_reports:
        uncleared_report_user_key_words.append(KeyWordsGroup.find_by_report(report.id))
    report_user_key_words = list(chain.from_iterable(uncleared_report_user_key_words))
    
    report_key_words = group_keywords(report_user_key_words, with_report=True)
    
    # Processing type
    if request.method == "POST":
        if "add_new_type_button" in request.form:
            ReportType.create(type=request.form["new_type"],user_id=current_user.id)
            flash("New type was created successfully")
            return redirect(request.url)
        
        if "delete_type_button" in request.form:
            try:
                ReportType.delete_by_id(request.form["type_id"])
                flash("Type was deleted successfully")
            except:
                flash("It's impossible to delele the type because of existing of the reports with this type")
            return redirect(request.url)
        
        if "edit_type_button" in request.form:
            type_for_editing = ReportType.query.filter_by(id=request.form["type_id"], user_id=current_user.id).first()
            
            if not type_for_editing:
                flash("You do not have permission to edit this type.", "error")
                return redirect(request.url)
            
            type_for_editing.type = request.form["type_type"]
            type_for_editing.save()
            flash("Type edited successfully")
            return redirect(request.url)
        
        # Processing subtype
        if "add_new_subtype_button" in request.form:
            ReportSubtype.create(type=request.form["report_subtype_type"], subtype=request.form["new_subtype"], user_id=current_user.id)
            flash("New subtype was created successfully")
            return redirect(request.url)
        
        if "delete_subtype_button" in request.form:
            # Используем метод find_by_user для получения подтипов текущего пользователя
            subtype_for_deletion = ReportSubtype.find_by_user(current_user.id)
            subtype_for_deletion = next((st for st in subtype_for_deletion if st.id == int(request.form["subtype_id"])), None)

            if subtype_for_deletion:
                ReportSubtype.delete_by_id(subtype_for_deletion.id)
                flash("Subtype deleted successfully")
            else:
                flash("You don't have permission to delete this subtype")
            return redirect(request.url)
        
        if "edit_subtype_button" in request.form:
            subtype_for_editing = ReportSubtype.query.filter_by(id=request.form["subtype_id"], user_id=current_user.id).first()
            if subtype_for_editing:
                subtype_for_editing.subtype = request.form["subtype_subtype"]
                subtype_for_editing.save()
                flash("Subtype edited successfully")
            else:
                flash("You don't have permission to edit this subtype")
            return redirect(request.url)
        
    return render_template('report_settings.html', 
                           title = page_title,
                           menu = menu,
                           global_key_words=global_key_words,
                           report_key_words=report_key_words,
                           user_reports=user_reports,
                           user_types=user_types,
                           user_subtypes=user_subtypes,
                           paragraph_types=paragraph_types 
                           )



@report_settings_bp.route('/upload_template', methods=['POST'])
@login_required
def upload_template():
    """
    Обрабатывает загрузку шаблона Word файла.
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    file_type = request.form.get('file_type')
    
    # Устанавливаем имя файла в зависимости от типа
    if file_type == "template":
        file_name = "word_template"
        file_ext = "doc"
        folder_name = "word_template"
    elif file_type == "signature":
        file_name = "signatura"
        file_ext = "jpg"
        folder_name = "signatura"
    else:
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    
    # Загружаем файл с помощью функции file_uploader в папку "templates"
    upload_result, filepath = file_uploader(file, file_ext, folder_name, file_name=file_name)
    if "successfully" not in upload_result:
        return jsonify({"status": "error", "message": upload_result}), 400
    
    return jsonify({"status": "success", "message": upload_result}), 200



# Маршрут для добавления группы ключевых слов
@report_settings_bp.route('/add_keywords', methods=['POST'])
@login_required
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
@login_required
@report_settings_bp.route('/upload_keywords_from_word', methods=['POST'])
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
@report_settings_bp.route('/add_word_to_exist_group', methods=['POST'])
@login_required
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
    num_of_exist_key_words = len(KeyWordsGroup.query.filter_by(group_index=group_index, user_id=current_user.id).all())

        
    # Добавляем ключевые слова в нужную группу
    for i, key_word in enumerate(key_words, start=1):
        KeyWordsGroup.create(
            group_index=group_index,
            index=num_of_exist_key_words + i,
            key_word=key_word,
            user_id=current_user.id,
            reports=reports
        )
    db.session.commit()

    return {"status": "success", "message": "Keywords added successfully"}, 200
    

@report_settings_bp.route('/delete_keywords', methods=['POST'])
@login_required
def delete_keywords():
    group_index = request.json.get("group_index")

    if not group_index:
        return jsonify({"status": "error", "message": "Group index is required"}), 400

    # Удаление всех ключевых слов с данным group_index для текущего пользователя
    KeyWordsGroup.query.filter_by(group_index=group_index, user_id=current_user.id).delete()
    db.session.commit()

    return jsonify({"status": "success", "message": "Keywords group deleted successfully"}), 200

# Отвязываем группу ключевых слов от конкретного отчета
@report_settings_bp.route('/unlink_keyword_from_report', methods=['POST'])
@login_required
def unlink_keyword_from_report():
    data = request.json
    group_index = data.get("group_index")
    report_id = data.get("report_id")
    print(Report.query.get(report_id))
    if not group_index or not report_id:
        return jsonify({"status": "error", "message": "Group index and report ID are required"}), 400

    # Найдем ключевые слова в этой группе, связанные с данным отчетом
    keywords = KeyWordsGroup.find_by_group_index(group_index=group_index, user_id=current_user.id)
    print(keywords)
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


@report_settings_bp.route('/edit_keywords', methods=['POST'])
@login_required
def edit_keywords():
    data = request.json
    key_words = data.get("key_words")
    print(data)

    if not key_words:
        return jsonify({"status": "error", "message": "Words are required"}), 400

    for word in key_words:
        word_id = word.get("id")
        key_word = word.get("word")

        if not key_word:
            # Если ключевое слово пустое, удаляем его
            word_for_delete = KeyWordsGroup.query.get(word_id)
            print(word_for_delete)
            word_for_delete.delete()
            
        else:
            # Если ключевое слово есть, обновляем его
            keyword_entry = KeyWordsGroup.query.get(word_id)
            if keyword_entry:
                keyword_entry.key_word = key_word

    db.session.commit()

    return jsonify({"status": "success", "message": "Keywords updated successfully"}), 200


@report_settings_bp.route('/add_paragraph_type', methods=['POST'])
@login_required
def add_paragraph_type():
    data = request.get_json()
    new_type_name = data.get('new_paragraph_type', '').strip()
    
    if not new_type_name:
        return jsonify({"status": "error", "message": "Paragraph type name cannot be empty."}), 400

    # Проверяем, что тип с таким именем еще не существует
    existing_type = ParagraphType.query.filter_by(type_name=new_type_name).first()
    if existing_type:
        return jsonify({"status": "error", "message": "A paragraph type with this name already exists."}), 400

    # Создаем новый тип параграфа
    ParagraphType.create(type_name=new_type_name)
    return jsonify({"status": "success", "message": "New paragraph type created successfully."}), 200

