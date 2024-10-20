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

