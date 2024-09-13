# report_settings.py
#v0.2.0

from flask import Blueprint, render_template, request, redirect, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db, ReportType, ReportSubtype, AppConfig, KeyWordsGroup, Report 
from itertools import chain
from file_processing import file_uploader
from sentence_processing import group_keywords, sort_key_words_group

report_settings_bp = Blueprint('report_settings', __name__)

# Functions

def process_keywords(key_word_input):
    """Обрабатываем строку ключевых слов, разделенных запятой, и возвращаем список"""
    key_words = []
    for word in key_word_input.split(','):
        stripped_word = word.strip()
        if stripped_word:
            key_words.append(stripped_word)
    return key_words

# Routs

@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    page_title = "Report settings"
    # Get data from the config
    menu = current_app.config["MENU"]
    upload_folder_path = current_app.config.get("UPLOAD_FOLDER_PATH")
    upload_folder_name = current_app.config.get("UPLOAD_FOLDER_NAME")
    
    # Get all user reports
    user_reports = Report.find_by_user(current_user.id)
    
    # Get types
    user_types = ReportType.find_by_user(current_user.id)
    
    # Get subtypes
    user_subtypes = ReportSubtype.find_by_user(current_user.id)
    
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
        
        # Directory and folder name settings
        if "save_directory_button" in request.form:
            directory_path = request.form["directory_path"]
            AppConfig.set_config_value("UPLOAD_FOLDER_PATH", directory_path, current_user.id)
            flash("Directory path saved successfully", "success")
            return redirect(request.url)
        
        if "save_folder_name_button" in request.form:
            folder_name = request.form["folder_name"]
            AppConfig.set_config_value("UPLOAD_FOLDER_NAME", folder_name, current_user.id)
            flash("Folder name saved successfully", "success")
            return redirect(request.url)
        
        # Handling file upload
        if 'file' in request.files:
            file = request.files['file']
            result = file_uploader(file, "doc")
            if "successfully" in result:
                flash(result, 'success')
            else:
                flash(result, 'error')
            return redirect(request.url)
        
    return render_template('report_settings.html', 
                           title = page_title,
                           menu = menu,
                           upload_folder_path=upload_folder_path,
                           upload_folder_name=upload_folder_name,
                           global_key_words=global_key_words,
                           report_key_words=report_key_words,
                           user_reports=user_reports,
                           user_types=user_types,
                           user_subtypes=user_subtypes 
                           )


@report_settings_bp.route('/add_keywords', methods=['POST'])
@login_required
def add_keywords():
    data = request.get_json()
    key_word_input = data.get('key_word_input').strip()
    report_ids = data.get('report_ids', [])  # Получаем список отчетов или пустой список
    
    if not key_word_input:
        return {"status": "error", 
                "message": "No keywords provided."}, 400

    key_words = process_keywords(key_word_input)
    
    if not key_words:
        return {"status": "error", 
                "message": "Invalid keywords format."}, 400
    
    # Получаем все ключевые слова пользователя
    user_key_words = KeyWordsGroup.find_by_user(current_user.id)

    # Определяем максимальный group_index чтобы понять какой индекс присвоить новой группе
    max_group_index = max([kw.group_index for kw in user_key_words], default=0)
    new_group_index = max_group_index + 1
    
    for i, key_word in enumerate(key_words):
        KeyWordsGroup.create(
            group_index=new_group_index,
            index=i,
            key_word=key_word,
            user_id=current_user.id,
            reports=report_ids
        )

    return {"status": "success"}, 200
    

@report_settings_bp.route('/add_word_to_exist_group', methods=['POST'])
@login_required
def add_word_to_exist_group():
    data = request.json
    group_index = data.get("group_index")
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
            user_id=current_user.id
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

