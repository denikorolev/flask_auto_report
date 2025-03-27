# new_report_creation.py

from flask import Blueprint, render_template, request, g, jsonify
from flask_login import current_user
from models import db, Report, ReportType, Paragraph, HeadSentence, BodySentence, ReportShare
from sentence_processing import extract_paragraphs_and_sentences
from file_processing import allowed_file
from utils import ensure_list
from werkzeug.utils import secure_filename
from logger import logger
import os
import shutil 
from flask_security.decorators import auth_required

new_report_creation_bp = Blueprint('new_report_creation', __name__)


# Функции

def create_report_from_existing(report_name, report_subtype, comment, report_side, selected_reports):
    """
    Создает новый отчет на основе одного или нескольких существующих.
    Возвращает созданный объект отчета или выбрасывает исключение при ошибке.
    """
    
    user_id = current_user.id
    profile_id = g.current_profile.id
    
    new_report = Report.create(
        profile_id=profile_id,
        report_subtype=report_subtype,
        report_name=report_name,
        user_id=user_id,
        comment=comment,
        public=False,
        report_side=report_side
    )

    paragraph_index = 0
    impression_exist = []

    for report_id in selected_reports:
        existing_report = Report.query.get(report_id)
        if not existing_report:
            raise ValueError(f"Протокол с ID {report_id} не найден")

        sorted_paragraphs = sorted(existing_report.report_to_paragraphs, key=lambda p: p.paragraph_index)

        for paragraph in sorted_paragraphs:
            if paragraph.is_impression:
                if not impression_exist:
                    impression_exist.append(paragraph)
                continue

            Paragraph.create(
                report_id=new_report.id,
                paragraph_index=paragraph_index,
                paragraph=paragraph.paragraph,
                paragraph_visible=paragraph.paragraph_visible,
                title_paragraph=paragraph.title_paragraph,
                bold_paragraph=paragraph.bold_paragraph,
                head_sentence_group_id=paragraph.head_sentence_group_id or None,
                tail_sentence_group_id=paragraph.tail_sentence_group_id or None
            )
            paragraph_index += 1

    for paragraph in impression_exist:
        Paragraph.create(
            report_id=new_report.id,
            paragraph_index=paragraph_index,
            paragraph=paragraph.paragraph,
            is_impression=True,
            paragraph_visible=paragraph.paragraph_visible,
            title_paragraph=paragraph.title_paragraph,
            bold_paragraph=paragraph.bold_paragraph,
            head_sentence_group_id=paragraph.head_sentence_group_id or None,
            tail_sentence_group_id=paragraph.tail_sentence_group_id or None
        )

    return new_report



# Routes

# Загрузка основной страницы создания отчета
@new_report_creation_bp.route('/create_report', methods=['GET', 'POST'])
@auth_required()
def create_report():
    report_types_and_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    current_user_reports_data = []
    current_user_reports = Report.query.filter_by(user_id=current_user.id).all()
    print(f"Найдено протоколов {len(current_user_reports)}")
    for report in current_user_reports:
        report_info = Report.get_report_info(report.id)
        current_user_reports_data.append(report_info)
    return render_template("create_report.html",
                           title="Создание нового протокола",
                           user_reports=current_user_reports_data,
                           report_types_and_subtypes=report_types_and_subtypes
                           )
    
    
# Получение shared протоколов
@new_report_creation_bp.route("/get_shared_reports", methods=["GET"])
@auth_required()
def get_shared_reports():
    logger.info("[get_shared_reports]------------------------")
    logger.info("[get_shared_reports] 🚀 Начат запрос расшаренных протоколов")

    try:
        # Получаем записи, где текущий пользователь получатель
        shared_records = ReportShare.query.filter_by(shared_with_user_id=current_user.id).all()

        if not shared_records:
            logger.info("[get_shared_reports] ⚠️ Нет протоколов которыми кто-либо поделился с данными пользователем.")
            return jsonify({"status": "warning", "message": "Нет протоколов которыми кто-либо поделился с данными пользователем.", "reports": []})

        shared_reports = []
        for record in shared_records:
            report = record.report
            if not report:
                continue  # на случай, если отчет удалён

            shared_reports.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text,
                "shared_by_email": record.shared_by.email
            })

        logger.info(f"[get_shared_reports] ✅ Возвращено {len(shared_reports)} расшаренных протоколов")
        logger.info(f"[get_shared_reports] ------------------------")
        return jsonify({"status": "success", "reports": shared_reports})

    except Exception as e:
        logger.error(f"[get_shared_reports] ❌ Ошибка при получении расшаренных отчетов: {e}")
        return jsonify({"status": "error", "message": "Не удалось получить расшаренные отчеты"}), 500
    
    
# Получение public протоколов
@new_report_creation_bp.route("/get_public_reports", methods=["GET"])
@auth_required()
def get_public_reports():
    logger.info("(Маршрут: get_public_reports)------------------------")
    logger.info("(Маршрут: get_public_reports) 🚀 Запрос общедоступных протоколов")
    
    try:
        public_reports = Report.query.filter(
            Report.public == True,
        ).all()

        if not public_reports:
            return jsonify({
                "status": "warning",
                "message": "Нет общедоступных протоколов",
                "reports": []
            })

        public_reports = []
        for report in public_reports:
            public_reports.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text
            })

        logger.info(f"(Маршрут: get_public_reports) ✅ Найдено {len(public_reports)} общедоступных протоколов")
        return jsonify({
            "status": "success",
            "reports": public_reports
        })

    except Exception as e:
        logger.error(f"(Маршрут: get_public_reports) ❌ Ошибка: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Не удалось загрузить общедоступные протоколы: {str(e)}"
        }), 500
    
    
# Создание нового отчета вручную
@new_report_creation_bp.route('/create_manual_report', methods=['POST'])
@auth_required()
def create_manual_report():
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Не получены данные для создания протокола"}), 400
        
        report_name = data.get('report_name')
        report_subtype = data.get('report_subtype')
        comment = data.get('comment', "")
        report_side = data.get('report_side', False)
        
        profile_id = g.current_profile.id
        
        # Create new report
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=False,
            report_side=report_side
        )
        logger.info(f"Report created successfully. Report ID: {new_report.id}")
        return jsonify({"status": "success", 
                        "message": "Протокол создан успешно", 
                        "report_id": new_report.id}), 200

    except Exception as e:
        logger.error(f"Failed to create report. Error: {str(e)}")
        return jsonify({"status": "error", "message": f"Не удалось создать протокол. Ошибка: {str(e)}"}), 500    

    
    
# Создание нового отчета из загруженного файла
@new_report_creation_bp.route('/create_report_from_file', methods=['POST'])
@auth_required()
def create_report_from_file():
    
    try:
        report_name = request.form.get('report_name')
        report_subtype = int(request.form.get('report_subtype'))
        comment = request.form.get('comment', "")
        report_side = request.form.get('report_side') == 'true'
        
        profile_id = g.current_profile.id
        user_id = current_user.id
        

        # Обрабатываем загруженный файл
        user_temp_folder = f"{current_user.id}_temp"
        if 'report_file' not in request.files:
            return jsonify({"status": "error", 
                            "message": "В полученных данных нет файла"}), 400

        file = request.files['report_file']
        if file.filename == '':
            return jsonify({"status": "error", 
                            "message": "Файл не выбран"}), 400

        if file and allowed_file(file.filename, file_type='doc'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(user_temp_folder, filename)
            if not os.path.exists(user_temp_folder):
                os.makedirs(user_temp_folder)
            file.save(filepath)

            try:
                # Извлекаем содержимое файла
                paragraphs_from_file = extract_paragraphs_and_sentences(filepath)
                print(paragraphs_from_file)
                public = False
                # Создаем новый отчет
                new_report = Report.create(
                        profile_id=profile_id,
                        report_subtype=report_subtype,
                        report_name=report_name,
                        user_id=current_user.id,
                        comment=comment,
                        public=public,
                        report_side=report_side
                    )

                # Определяем тип протокола
                report_type_id = Report.get_report_type(new_report.id)
                # Добавляем абзацы и предложения в отчет
                for idx, paragraph in enumerate(paragraphs_from_file, start=1):

                    # Создаем новый параграф
                    new_paragraph = Paragraph.create(
                        report_id=new_report.id,
                        paragraph_index=idx,
                        paragraph=paragraph['title']
                    )

                    # Обрабатываем предложения
                    for sentence_index, sentence_data in enumerate(paragraph['sentences'], start=1):
                        if isinstance(sentence_data, list):
                            for weight, split_sentence in enumerate(sentence_data, start=1):
                                if weight == 1:
                                    new_head_sentence, _ = HeadSentence.create(
                                        user_id=user_id,
                                        report_type_id=report_type_id,
                                        sentence=split_sentence.strip(),
                                        related_id=new_paragraph.id,
                                        sentence_index=sentence_index
                                    )
                                
                                else:
                                    BodySentence.create(
                                        user_id=user_id,
                                        report_type_id=report_type_id,
                                        sentence=split_sentence.strip(),
                                        related_id=new_head_sentence.id,
                                        sentence_index=sentence_index
                                    )
                        else:
                            HeadSentence.create(
                                user_id=user_id,
                                report_type_id=report_type_id,
                                sentence=sentence_data.strip(),
                                related_id=new_paragraph.id,
                                sentence_index=sentence_index
                            )

                # Удаляем временную папку после успешной обработки
                if os.path.exists(user_temp_folder):
                    shutil.rmtree(user_temp_folder)

                # Формируем ответ с уведомлениями о замене
                return jsonify({"status": "success", 
                                "report_id": new_report.id, 
                                "message": "Протокол создан успешно"
                                }), 200

            except Exception as e:
                if os.path.exists(user_temp_folder):
                    shutil.rmtree(user_temp_folder)
                return jsonify({"status": "error", "message": f"Ошибка при создании протокола: {str(e)}"}), 500

        else:
            return jsonify({"status": "error", 
                            "message": "Неверный тип файла"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка при создании протокола: {str(e)}"}), 500

    
    
# Создание нового отчета на основе одного или нескольких существующих
@new_report_creation_bp.route('/create_report_from_existing_few', methods=['POST'])
@auth_required()
def create_report_from_existing_few():
    logger.info(f"(Маршрут: создание протокола из существующих)------------------------")
    logger.info(f"(Маршрут: создание протокола из существующих) 🚀 Начато создание протокола")
    try:
        data = request.get_json()
        logger.debug(f"(Маршрут: создание протокола из существующих) Получены данные: {data}")

        report_name = data.get("report_name")
        report_subtype = int(data.get("report_subtype"))
        comment = data.get("comment", "")
        report_side = data.get("report_side", False)
        selected_reports = ensure_list(data.get("selected_reports", []))

        if not selected_reports:
            return jsonify({
                "status": "error", 
                "message": "Не выбраны исходные протоколы для копирования"
            }), 400

        new_report = create_report_from_existing(
            report_name=report_name,
            report_subtype=report_subtype,
            comment=comment,
            report_side=report_side,
            selected_reports=selected_reports
        )
        logger.info(f"(Маршрут: создание протокола из существующих) ✅ Протокол создан успешно. ID: {new_report.id}")
        return jsonify({
            "status": "success",
            "message": "Протокол успешно создан",
            "report_id": new_report.id
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Ошибка при создании протокола: {str(e)}"
        }), 500





   
        
        