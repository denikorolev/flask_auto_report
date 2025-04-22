# report_settings.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from flask_login import login_required
from models import db, ReportType, ReportSubtype
from file_processing import file_uploader
from flask_security.decorators import auth_required
from logger import logger

report_settings_bp = Blueprint('report_settings', __name__)


# Routs
# Главный маршрут страницы
@report_settings_bp.route('/report_settings', methods=['GET', 'POST'])
@auth_required()
def report_settings():
    logger.info(f"(Report_settings)--------------------------------")
    logger.info(f"(Report_settings) 🚀 Начато получение настроек протоколов")
    try:
        profile_types_with_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    except Exception as e:
        logger.error(f"(Report_settings) ❌ Ошибка: Не удалось получить типы и подтипы протоколов - {e}")
        return jsonify({"status": "error", "message": "Не удалось получить типы и подтипы протоколов"}), 400
    logger.info(f"(Report_settings) ✅ Получены типы и подтипы протоколов")
    logger.info(f"(Report_settings) ---------------------------------")
        
    return render_template('report_settings.html', 
                           title = "Настройки протоколов",
                           types_subtypes=profile_types_with_subtypes,
                           )



@report_settings_bp.route('/add_type', methods=['POST'])
@auth_required()
def add_type():
    """
    Обрабатывает добавление нового типа отчета.
    """
    logger.info(f"(Add_new_type)--------------------------------")
    logger.info(f"(Add_new_type) 🚀 Начато добавление нового типа отчета")
    
    data = request.get_json()
    new_type = data.get("new_type", "").strip()
    print(new_type)

    if not new_type:
        logger.error(f"(Add_new_type) ❌ Ошибка: Имя типа не может быть пустым")
        return jsonify({"status": "error", "message": "Имя типа не может быть пустым"}), 400

    try:
        ReportType.create(type_text=new_type, profile_id=g.current_profile.id)
        logger.info(f"(Add_new_type) ✅ Новый тип протокола - '{new_type}' успешно добавлен")
        return jsonify({"status": "success", "message": "Новый тип протокола успешно добавлен"}), 200
    except Exception as e:
        logger.error(f"(Add_new_type) ❌ Ошибка: Не удалось добавить новый тип протокола - {e}")
        return jsonify({"status": "error", "message": f"Не удалось создать новый тип протокола"}), 400



@report_settings_bp.route('/delete_type', methods=['POST'])
@auth_required()
def delete_type():
    logger.info(f"(Delete_type)--------------------------------")
    logger.info(f"(Delete_type) 🚀 Начато удаление типа отчета")
    data = request.get_json()
    type_id = data.get("type_id")
    print(type_id)

    if not type_id:
        return jsonify({"status": "error", "message": "Не передан ID типа протокола."}), 400

    try:
        # Удаление типа из базы данных
        ReportType.delete_by_id(type_id)
        logger.info(f"(Delete_type) ✅ Тип протокола успешно удален")
        return jsonify({"status": "success", "message": "Тип протокола успешно удален"}), 200
    except Exception as e:
        logger.error(f"(Delete_type) ❌ Ошибка: Не удалось удалить тип протокола - {e}")
        return jsonify({"status": "error", "message": f"Не удалось удалить тип протокола."}), 400


@report_settings_bp.route('/edit_type', methods=['POST'])
@auth_required()
def edit_type():
    logger.info(f"(Edit_type)--------------------------------")
    logger.info(f"(Edit_type) 🚀 Начато редактирование типа отчета")
    data = request.get_json()
    type_id = data.get("type_id")
    new_type_name = data.get("new_type_name", "").strip()

    if not type_id or not new_type_name:
        logger.error(f"(Edit_type) ❌ Ошибка: Не переданы ID типа и новое имя типа.")
        return jsonify({"status": "error", "message": "Ошибка: Не переданы ID типа и новое имя типа."}), 400

    try:
        # Поиск типа по ID и обновление имени
        type_for_editing = ReportType.query.filter_by(id=type_id, profile_id=g.current_profile.id).first()

        if not type_for_editing:
            logger.error(f"(Edit_type) ❌ Ошибка: У вас нет прав на редактирование этого типа.")
            return jsonify({"status": "error", "message": "Не найден данный тип протокола или у вашего текущего профиля нет прав на его редактирование."}), 403

        type_for_editing.type_text = new_type_name
        type_for_editing.save()  # Сохранение изменений в базе данных
        logger.info(f"(Edit_type) ✅ Тип протокола успешно изменен")
        logger.info(f"(Edit_type)---------------------------------")
        return jsonify({"status": "success", "message": "Тип протокола успешно изменен"}), 200
    except Exception as e:
        logger.error(f"(Edit_type) ❌ Ошибка: Не удалось изменить тип протокола - {e}")
        return jsonify({"status": "error", "message": "Type wasn't edited."}), 400


@report_settings_bp.route('/add_subtype', methods=['POST'])
@auth_required()
def add_subtype():
    logger.info(f"(Add_new_subtype)--------------------------------")
    logger.info(f"(Add_new_subtype) 🚀 Начато добавление нового подтипа отчета")
    data = request.get_json()
    report_type_id = data.get("report_type_id")
    new_subtype_name = data.get("new_subtype_name", "").strip()

    if not report_type_id or not new_subtype_name:
        logger.error(f"(Add_new_subtype) ❌ Ошибка: Не переданы ID типа и имя подтипа.")
        return jsonify({"status": "error", "message": "Ошибка: Не переданы ID типа и имя подтипа."}), 400

    try:
        ReportSubtype.create(type_id=report_type_id, subtype_text=new_subtype_name)
        logger.info(f"(Add_new_subtype) ✅ Новый подтип протокола - '{new_subtype_name}' успешно добавлен")
        logger.info(f"(Add_new_subtype)---------------------------------")
        return jsonify({"status": "success", "message": "Новый подтип протокола успешно добавлен"}), 200
    except Exception as e:
        logger.error(f"(Add_new_subtype) ❌ Ошибка: Не удалось добавить новый подтип протокола - {e}")
        return jsonify({"status": "error", "message": "Не удалось добавить новый подтип протокола"}), 400


@report_settings_bp.route('/delete_subtype', methods=['POST'])
@auth_required()
def delete_subtype():
    logger.info(f"(Delete_subtype)--------------------------------")
    logger.info(f"(Delete_subtype) 🚀 Начато удаление подтипа отчета")
    data = request.get_json()
    subtype_id = data.get("subtype_id")
    print(subtype_id)

    if not subtype_id:
        logger.error(f"(Delete_subtype) ❌ Ошибка: Не передан ID подтипа.")
        return jsonify({"status": "error", "message": "Не передан ID подтипа"}), 400

    try:
        ReportSubtype.delete_by_id(subtype_id)
        logger.info(f"(Delete_subtype) ✅ Подтип протокола успешно удален")
        logger.info(f"(Delete_subtype)---------------------------------")
        return jsonify({"status": "success", "message": "Subtype was deleted successfully."}), 200
    except Exception as e:
        logger.error(f"(Delete_subtype) ❌ Ошибка: Не удалось удалить подтип протокола - {e}")
        return jsonify({"status": "error", "message": "Не удалось удалить подтип протокола"}), 400
    
    
@report_settings_bp.route('/edit_subtype', methods=['POST'])
@auth_required()
def edit_subtype():
    logger.info(f"(Edit_subtype)--------------------------------")
    logger.info(f"(Edit_subtype) 🚀 Начато редактирование подтипа отчета")
    data = request.get_json()
    subtype_id = data.get("subtype_id")
    new_subtype_name = data.get("new_subtype_name", "").strip()

    if not subtype_id or not new_subtype_name:
        logger.error(f"(Edit_subtype) ❌ Ошибка: Не переданы ID подтипа и новое имя подтипа.")
        return jsonify({"status": "error", "message": "Ошибка: Не переданы ID подтипа и новое имя подтипа."}), 400

    try:
        # Поиск подтипа по ID и обновление имени
        subtype_for_editing = ReportSubtype.query.filter_by(id=subtype_id).first()

        if not subtype_for_editing:
            logger.error(f"(Edit_subtype) ❌ Ошибка: Не найден данный подтип отчета.")
            return jsonify({"status": "error", "message": "Не найден указанный подтип или у вашего текущего профиля нет прав на редактирование данного подтипа"}), 403

        subtype_for_editing.subtype_text = new_subtype_name
        subtype_for_editing.save() 
        logger.info(f"(Edit_subtype) ✅ Подтип протокола успешно изменен")
        logger.info(f"(Edit_subtype)---------------------------------")
        return jsonify({"status": "success", "message": "Подтип протокола успешно изменен"}), 200
    except Exception as e:
        logger.error(f"(Edit_subtype) ❌ Ошибка: Не удалось изменить подтип протокола - {e}")
        return jsonify({"status": "error", "message": "Subtype wasn't edited."}), 400
    
    
    
@report_settings_bp.route('/upload_template', methods=['POST'])
@auth_required()
def upload_template():
    """
    Обрабатывает загрузку шаблона Word файла.
    """
    logger.info(f"(Upload_template)--------------------------------")
    logger.info(f"(Upload_template) 🚀 Начата загрузка шаблона Word файла")
    
    if 'file' not in request.files:
        logger.error(f"(Upload_template) ❌ Ошибка: Не передан файл.")
        return jsonify({"status": "error", "message": "Не передан файл."}), 400
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
        logger.error(f"(Upload_template) ❌ Ошибка: Неверный тип файла.")
        return jsonify({"status": "error", "message": "Неверный тип файла"}), 400
    
    # Загружаем файл с помощью функции file_uploader в папку "templates"
    upload_result, filepath = file_uploader(file, file_ext, folder_name, file_name=file_name)
    if "successfully" not in upload_result:
        logger.error(f"(Upload_template) ❌ Ошибка: Не удалось загрузить файл - {upload_result}")
        return jsonify({"status": "error", "message": upload_result}), 400
    
    logger.info(f"(Upload_template) ✅ Файл успешно загружен")
    logger.info(f"(Upload_template)---------------------------------")
    return jsonify({"status": "success", "message": upload_result}), 200

