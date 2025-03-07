# new_report_creation.py

from flask import Blueprint, render_template, request, g, jsonify
from flask_login import current_user
from models import db, Report, ReportType, Paragraph, HeadSentence, BodySentence  
from sentence_processing import extract_paragraphs_and_sentences
from file_processing import allowed_file
from utils import ensure_list
from werkzeug.utils import secure_filename
from logger import logger
import os
import shutil 
from flask_security.decorators import auth_required

new_report_creation_bp = Blueprint('new_report_creation', __name__)


# Routes

# Загрузка основной страницы создания отчета
@new_report_creation_bp.route('/create_report', methods=['GET', 'POST'])
@auth_required()
def create_report():
    report_types_and_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    current_profile_reports = Report.find_by_profile(g.current_profile.id)
            
    return render_template("create_report.html",
                           title="Создание нового протокола",
                           user_reports=current_profile_reports,
                           report_types_and_subtypes=report_types_and_subtypes
                           )
    
    
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
    try:
        # Получаем данные из запроса
        data = request.get_json()
        print(f"Данные от клиента: {data}")
        print("--------------------------")
        
        report_name = data.get("report_name")
        report_subtype = int(data.get("report_subtype"))
        comment = data.get("comment")
        report_side = data.get("report_side", False)
        additional_paragraphs = int(data.get("additional_paragraphs", 0))
        selected_reports = ensure_list(data.get("selected_reports", []))
        
        user_id = current_user.id
        profile_id = g.current_profile.id

        if not selected_reports:
            return jsonify({"status": "error", 
                            "message": "Не выбран протокол для создания с него копии"}), 400

        # Создаем новый отчет
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=user_id,
            comment=comment,
            public=False,
            report_side=report_side
        )
        
            
        # Если только один протокол то просто копируем его
        if len(selected_reports) == 1:
            existing_report = Report.query.get(selected_reports[0])
            if not existing_report:
                    return jsonify({"status": "error", 
                                    "message": f"Протокол с ID {report_id} не найден"}), 404
            sorted_paragraphs = sorted(existing_report.report_to_paragraphs, key=lambda p: p.paragraph_index)
            
            for paragraph in sorted_paragraphs:
                Paragraph.create(
                    report_id=new_report.id,
                    paragraph_index=paragraph.paragraph_index,
                    paragraph=paragraph.paragraph,
                    paragraph_type=paragraph.paragraph_type,
                    paragraph_visible=paragraph.paragraph_visible,
                    title_paragraph=paragraph.title_paragraph,
                    bold_paragraph=paragraph.bold_paragraph,
                    head_sentence_group_id=paragraph.head_sentence_group_id or None,
                    tail_sentence_group_id=paragraph.tail_sentence_group_id or None
                )
        # Если протоколов несколько то нужно будет заморочиться для 
        # адекватной обработки параметров сканирования, заключений и т.д.
        else:
            paragraph_index = 2
            scanparam_exist = []
            impression_exist = []

            # Копируем данные из выбранных отчетов
            for idx, report_id in enumerate(selected_reports):
                existing_report = Report.query.get(report_id)
                if not existing_report:
                    return jsonify({"status": "error", 
                                    "message": f"Протокол с ID {report_id} не найден"}), 404
                
                # Получаем и сортируем параграфы по их индексу
                sorted_paragraphs = sorted(existing_report.report_to_paragraphs, key=lambda p: p.paragraph_index)
                
                # Копируем параграфы и предложения
                for paragraph in sorted_paragraphs:
                    if paragraph.paragraph_type == "scanparam":
                        if len(scanparam_exist) == 0:
                            scanparam_exist.append(paragraph)
                            continue
                        else:
                            print("scanparam_exist continue")
                            continue
                        
                            
                    if paragraph.paragraph_type == "impression":
                        if len(impression_exist) == 0:
                            impression_exist.append(paragraph)
                            continue
                        else:
                            print("impression_exist continue")
                            continue
                        
                    
                    Paragraph.create(
                        report_id=new_report.id,
                        paragraph_index=paragraph_index,
                        paragraph=paragraph.paragraph,
                        paragraph_type=paragraph.paragraph_type,
                        paragraph_visible=paragraph.paragraph_visible,
                        title_paragraph=paragraph.title_paragraph,
                        bold_paragraph=paragraph.bold_paragraph,
                        head_sentence_group_id=paragraph.head_sentence_group_id or None,
                        tail_sentence_group_id=paragraph.tail_sentence_group_id or None
                    )
                    paragraph_index += 1

                # Добавляем дополнительные параграфы между отчетами, кроме последнего
                if idx < len(selected_reports) - 1:
                    for _ in range(additional_paragraphs):
                        Paragraph.create(
                            report_id=new_report.id,
                            paragraph_index=paragraph_index,
                            paragraph="Автоматически добавленный параграф",
                            paragraph_type="text",  
                            paragraph_visible=True,
                            title_paragraph=True,
                            bold_paragraph=False
                        )
                        paragraph_index += 1
            
            # Добавляем параграфы с параметрами сканирования и заключениями
            for paragraph in scanparam_exist:
                Paragraph.create(
                    report_id=new_report.id,
                    paragraph_index=1,
                    paragraph=paragraph.paragraph,
                    paragraph_type=paragraph.paragraph_type,
                    paragraph_visible=paragraph.paragraph_visible,
                    title_paragraph=paragraph.title_paragraph,
                    bold_paragraph=paragraph.bold_paragraph,
                    head_sentence_group_id=paragraph.head_sentence_group_id or None,
                    tail_sentence_group_id=paragraph.tail_sentence_group_id or None
                )
            scanparam_exist = []
                
            for paragraph in impression_exist:
                Paragraph.create(
                    report_id=new_report.id,
                    paragraph_index=paragraph_index,
                    paragraph=paragraph.paragraph,
                    paragraph_type=paragraph.paragraph_type,
                    paragraph_visible=paragraph.paragraph_visible,
                    title_paragraph=paragraph.title_paragraph,
                    bold_paragraph=paragraph.bold_paragraph,
                    head_sentence_group_id=paragraph.head_sentence_group_id or None,
                    tail_sentence_group_id=paragraph.tail_sentence_group_id or None
                )
            impression_exist = []
                
        return jsonify({"status": "success", 
                        "message": "Протокол создан успешно", 
                        "report_id": new_report.id
                        }), 200

    except Exception as e:
        return jsonify({"status": "error", 
                        "message": f"Не удалось создать отчет. Ошибка: {str(e)}"}), 500


