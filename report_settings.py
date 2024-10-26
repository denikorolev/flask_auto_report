# report_settings.py

from flask import Blueprint, render_template, request, redirect, current_app, jsonify, g
from flask_login import login_required, current_user
from models import db, ReportType, ReportSubtype, KeyWord, Report, ParagraphType 
from itertools import chain
from file_processing import file_uploader, allowed_file
from sentence_processing import group_keywords, sort_key_words_group, process_keywords, check_existing_keywords, extract_keywords_from_doc
from errors_processing import print_object_structure
from utils import ensure_list, get_max_index
from db_processing import add_keywords_to_db

report_settings_bp = Blueprint('report_settings', __name__)


# Routs
# Главный маршрут страницы
@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@login_required
def report_settings():
    menu = current_app.config["MENU"]
    
    profile_types = ReportType.find_by_profile(g.current_profile.id)
    profile_subtypes = []
    for type in profile_types:
        subtypes = ReportSubtype.find_by_report_type(type=type)
        profile_subtypes.append(subtypes)
        
        
    paragraph_types = ParagraphType.query.all() 
        
    return render_template('report_settings.html', 
                           title = "Report settings",
                           menu = menu,
                           user_types=profile_types,
                           user_subtypes=profile_subtypes,
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


@report_settings_bp.route('/add_type', methods=['POST'])
@login_required
def add_type():
    """Handles adding a new report type."""
    data = request.get_json()
    new_type = data.get("new_type", "").strip()

    if not new_type:
        return jsonify({"status": "error", "message": "Type name cannot be empty."}), 400

    try:
        ReportType.create(type=new_type, profile_id=g.current_profile.id)
        return jsonify({"status": "success", "message": "New type was created successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "New type wasn't created because of {e}."}), 400


@report_settings_bp.route('/delete_type', methods=['POST'])
@login_required
def delete_type():
    """Handles deleting a report type."""
    data = request.get_json()
    type_id = data.get("type_id")
    print(type_id)

    if not type_id:
        return jsonify({"status": "error", "message": "Type ID is required."}), 400

    try:
        # Удаление типа из базы данных
        ReportType.delete_by_id(type_id)
        return jsonify({"status": "success", "message": "Type was deleted successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Type wasn't deleted because of {str(e)}."}), 400


@report_settings_bp.route('/edit_type', methods=['POST'])
@login_required
def edit_type():
    """Handles editing a report type."""
    data = request.get_json()
    type_id = data.get("type_id")
    new_type_name = data.get("new_type_name", "").strip()

    if not type_id or not new_type_name:
        return jsonify({"status": "error", "message": "Type ID and new type name are required."}), 400

    try:
        # Поиск типа по ID и обновление имени
        type_for_editing = ReportType.query.filter_by(id=type_id, user_id=current_user.id).first()

        if not type_for_editing:
            return jsonify({"status": "error", "message": "You do not have permission to edit this type."}), 403

        type_for_editing.type = new_type_name
        type_for_editing.save()  # Сохранение изменений в базе данных
        return jsonify({"status": "success", "message": "Type edited successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", f"message": "Type wasn't edited because of {str(e)}."}), 400


@report_settings_bp.route('/add_subtype', methods=['POST'])
@login_required
def add_subtype():
    """Handles adding a new report subtype."""
    data = request.get_json()
    report_type_id = data.get("report_type_id")
    new_subtype_name = data.get("new_subtype_name", "").strip()

    if not report_type_id or not new_subtype_name:
        return jsonify({"status": "error", "message": "Both type ID and subtype name are required."}), 400

    try:
        ReportSubtype.create(type=report_type_id, subtype=new_subtype_name)
        return jsonify({"status": "success", "message": "New subtype was created successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", f"message": "Subtype wasn't created because of {str(e)}."}), 400


@report_settings_bp.route('/delete_subtype', methods=['POST'])
@login_required
def delete_subtype():
    """Handles deleting a report subtype."""
    data = request.get_json()
    subtype_id = data.get("subtype_id")

    if not subtype_id:
        return jsonify({"status": "error", "message": "Subtype ID is required."}), 400

    try:
        ReportSubtype.delete_by_id(subtype_id)
        return jsonify({"status": "success", "message": "Subtype was deleted successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", f"message": "Subtype wasn't deleted because of {str(e)}."}), 400
    
    
@report_settings_bp.route('/edit_subtype', methods=['POST'])
@login_required
def edit_subtype():
    """Handles editing a report subtype."""
    data = request.get_json()
    subtype_id = data.get("subtype_id")
    new_subtype_name = data.get("new_subtype_name", "").strip()

    if not subtype_id or not new_subtype_name:
        return jsonify({"status": "error", "message": "Both subtype ID and new subtype name are required."}), 400

    try:
        # Поиск подтипа по ID и обновление имени
        subtype_for_editing = ReportSubtype.query.filter_by(id=subtype_id, user_id=current_user.id).first()

        if not subtype_for_editing:
            return jsonify({"status": "error", "message": "You do not have permission to edit this subtype."}), 403

        subtype_for_editing.subtype = new_subtype_name
        subtype_for_editing.save()  # Сохранение изменений в базе данных
        return jsonify({"status": "success", "message": "Subtype edited successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", f"message": "Subtype wasn't edited because of {str(e)}."}), 400
