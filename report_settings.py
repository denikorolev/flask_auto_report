# report_settings.py

from flask import Blueprint, render_template, request, redirect, flash, current_app
from flask_login import login_required, current_user
from models import db, ReportType, ReportSubtype, AppConfig, KeyWordsGroup 
from file_processing import file_uploader
from sentence_processing import group_key_words_by_index

report_settings_bp = Blueprint('report_settings', __name__)

# Functions

# Routs

@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    page_title = "Report settings"
    # Get data from the config
    menu = current_app.config["MENU"]
    upload_folder_path = current_app.config.get("UPLOAD_FOLDER_PATH")
    upload_folder_name = current_app.config.get("UPLOAD_FOLDER_NAME")
    
    
    # Geting report types and subtypes 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype, "subtype_type_name": rst.report_type_rel.type}
        for rst in report_subtypes
    ]
    # Группируем ключевые слова с использованием  функции
    key_words_group = group_key_words_by_index(current_user.id)
    
    # Processing type
    if request.method == "POST":
        if "add_new_type_button" in request.form:
            ReportType.create(type=request.form["new_type"])
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
            type_for_editing = ReportType.query.get(request.form["type_id"])
            type_for_editing.type = request.form["type_type"]
            type_for_editing.save()
            flash("Type edited successfully")
            return redirect(request.url)
        
        # Processing subtype
        if "add_new_subtype_button" in request.form:
            ReportSubtype.create(type=request.form["report_subtype_type"], subtype=request.form["new_subtype"])
            flash("New subtype was created successfully")
            return redirect(request.url)
        
        if "delete_subtype_button" in request.form:
            try:
                ReportSubtype.delete_by_id(request.form["subtype_id"])
                flash("Subtype was deleted successfully")
            except:
                flash("It's impossible to delele the subtype because of existing of the reports with this type")
            return redirect(request.url)
        
        if "edit_subtype_button" in request.form:
            subtype_for_editing = ReportSubtype.query.get(request.form["subtype_id"])
            subtype_for_editing.subtype = request.form["subtype_subtype"]
            subtype_for_editing.save()
            flash("Subtype edited successfully")
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
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict,
                           upload_folder_path=upload_folder_path,
                           upload_folder_name=upload_folder_name,
                           key_words_group=key_words_group 
                           )


@report_settings_bp.route('/add_keywords', methods=['POST'])
@login_required
def add_keywords():
    key_word_input = request.json.get("key_word_input", "").strip()
    
    if not key_word_input:
        return {"status": "error", 
                "message": "No keywords provided."}, 400

    key_words = []
    for word in key_word_input.split(','):
        stripped_word = word.strip()
        if stripped_word:
            key_words.append(stripped_word)
    
    if not key_words:
        return {"status": "error", 
                "message": "Invalid keywords format."}, 400
    
    # Получаем все ключевые слова пользователя
    user_key_words = KeyWordsGroup.find_by_user_id(current_user.id)

    # Определяем максимальный group_index чтобы понять какой индекс присвоить новой группе
    max_group_index = max([kw.group_index for kw in user_key_words], default=0)
    new_group_index = max_group_index + 1
    
    for i, key_word in enumerate(key_words):
        KeyWordsGroup.create(
            group_index=new_group_index,
            index=i,
            key_word=key_word,
            user_id=current_user.id
        )

    # Группируем ключевые слова с использованием новой функции
    key_words_group = group_key_words_by_index(current_user.id)
    
    return {"status": "success", 
            "message": "New key words group added successfully.", 
            "key_words_group": key_words_group}, 200
    
    
@report_settings_bp.route('/delete_keywords', methods=['POST'])
@login_required
def delete_keywords():
    group_index = request.json.get("group_index")

    if not group_index:
        return {"status": "error", "message": "Group index is required"}, 400

    # Удаление всех ключевых слов с данным group_index для текущего пользователя
    KeyWordsGroup.query.filter_by(group_index=group_index, user_id=current_user.id).delete()
    db.session.commit()

    return {"status": "success", "message": "Keywords group deleted successfully"}, 200


@report_settings_bp.route('/edit_keywords', methods=['POST'])
@login_required
def edit_keywords():
    data = request.json
    group_index = data.get("group_index")
    words = data.get("words")

    if not group_index or not words:
        return {"status": "error", "message": "Group index and\or words are required"}, 400

    for word_data in words:
        word_id = word_data.get("id")
        key_word = word_data.get("key_word")

        if not key_word:
            # Если ключевое слово пустое, удаляем его
            KeyWordsGroup.query.filter_by(index=word_id, user_id=current_user.id).delete()
        else:
            # Если ключевое слово есть, обновляем его
            keyword_entry = KeyWordsGroup.query.filter_by(index=word_id, user_id=current_user.id).first()
            if keyword_entry:
                keyword_entry.key_word = key_word

    db.session.commit()

    return {"status": "success", "message": "Keywords updated successfully"}, 200

