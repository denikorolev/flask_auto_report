# new_report_creation.py
# Includes create_report route

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, g, jsonify
from flask_login import current_user, login_required
from models import db, User, Report, ReportType, ReportSubtype, Paragraph, Sentence, ParagraphType  
from sentence_processing import extract_paragraphs_and_sentences
from file_processing import allowed_file
from werkzeug.utils import secure_filename
import os
import shutil 
from flask_security.decorators import auth_required

new_report_creation_bp = Blueprint('new_report_creation', __name__)

# # Check the file extensions for being in allowed list
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

# Routes

@new_report_creation_bp.route('/create_report', methods=['GET', 'POST'])
@auth_required()
def create_report():
    page_title = "New report creation"
    menu = current_app.config['MENU']
    report_types_and_subtypes = ReportType.get_types_with_subtypes(g.current_profile.id)
    current_profile_reports = Report.find_by_profile(g.current_profile.id)
            
    
    return render_template("create_report.html",
                           title=page_title,
                           menu=menu,
                           user_reports=current_profile_reports,
                           report_types_and_subtypes=report_types_and_subtypes
                           )
    
    
@new_report_creation_bp.route('/create_manual_report', methods=['POST'])
@auth_required()
def create_manual_report():
    
    try:
        report_name = request.form.get('report_name')
        report_type = request.form.get('report_type')
        report_subtype = request.form.get('report_subtype')
        profile_id = g.current_profile.id
        comment = request.form.get('comment')
        public = False
        report_side = request.form.get('report_side') == 'true'
        

        # Create new report
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=public,
            report_side=report_side
        )
        return jsonify({"status": "success", 
                        "message": "report was created succesfully", 
                        "report_id": new_report.id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500    

    

@new_report_creation_bp.route('/create_report_from_file', methods=['POST'])
@auth_required()
def create_report_from_file():
    
    try:
        report_name = request.form.get('report_name')
        report_type = request.form.get('report_type')
        report_subtype = request.form.get('report_subtype')
        comment = request.form.get('comment')
        report_side = request.form.get('report_side') == 'true'
        profile_id = g.current_profile.id

        # Обрабатываем загруженный файл
        user_temp_folder = f"{current_user.id}_temp"
        if 'report_file' not in request.files:
            return jsonify({"status": "error", 
                            "message": "No file part in the request"}), 400

        file = request.files['report_file']
        if file.filename == '':
            return jsonify({"status": "error", 
                            "message": "No selected file"}), 400

        if file and allowed_file(file.filename, file_type='doc'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(user_temp_folder, filename)
            if not os.path.exists(user_temp_folder):
                os.makedirs(user_temp_folder)
            file.save(filepath)

            try:
                # Извлекаем содержимое файла
                paragraphs_from_file = extract_paragraphs_and_sentences(filepath)

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

                # Флаг для отслеживания первого вхождения impression
                impression_exists = False
                replacement_notifications = []

                # ID типов параграфов
                impression_type_id = ParagraphType.find_by_name("impression")
                text_type_id = ParagraphType.find_by_name("text")

                # Добавляем абзацы и предложения в отчет
                for idx, paragraph in enumerate(paragraphs_from_file, start=1):
                    paragraph_type = paragraph.get('paragraph_types', 'text')
                    paragraph_type_id = ParagraphType.find_by_name(paragraph_type)

                    # Если это тип "impression" и такой параграф уже был создан, меняем на "text"
                    if paragraph_type == "impression":
                        if impression_exists:
                            # Заменяем на тип "text"
                            paragraph_type_id = text_type_id
                            replacement_notifications.append(
                                f"Paragraph {idx} with type 'impression' was replaced by 'text' because an 'impression' paragraph already exists."
                            )
                        else:
                            # Первый параграф с типом "impression"
                            impression_exists = True

                    # Создаем новый параграф
                    new_paragraph = Paragraph.create(
                        paragraph_index=idx,
                        report_id=new_report.id,
                        paragraph=paragraph['title'],
                        paragraph_visible=paragraph.get('visible', True),
                        title_paragraph=paragraph.get('is_title', False),
                        bold_paragraph=paragraph.get('bold', False),
                        type_paragraph_id=paragraph_type_id,
                        comment=None,
                        paragraph_weight=1
                    )

                    # Обрабатываем предложения
                    for sentence_index, sentence_data in enumerate(paragraph['sentences'], start=1):
                        if isinstance(sentence_data, list):
                            for weight, split_sentence in enumerate(sentence_data, start=1):
                                Sentence.create(
                                    paragraph_id=new_paragraph.id,
                                    index=sentence_index,
                                    weight=weight,
                                    comment='',
                                    sentence=split_sentence.strip()
                                )
                        else:
                            Sentence.create(
                                paragraph_id=new_paragraph.id,
                                index=sentence_index,
                                weight=1,
                                comment='',
                                sentence=sentence_data.strip()
                            )

                # Удаляем временную папку после успешной обработки
                if os.path.exists(user_temp_folder):
                    shutil.rmtree(user_temp_folder)

                # Формируем ответ с уведомлениями о замене
                return jsonify({"status": "success", 
                                "report_id": new_report.id, 
                                "message": "report was created successfully", 
                                "notifications": replacement_notifications}), 200

            except Exception as e:
                if os.path.exists(user_temp_folder):
                    shutil.rmtree(user_temp_folder)
                return jsonify({"status": "error", "message": str(e)}), 500

        else:
            return jsonify({"status": "error", 
                            "message": "Invalid file type"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@new_report_creation_bp.route('/create_report_from_existing_report', methods=['POST'])
@auth_required()
def create_report_from_existing_report():
    
    try:
        existing_report_id = request.form.get('existing_report_id')
        if not existing_report_id:
            return jsonify({"status": "error", 
                            "message": "No report selected"}), 400

        # Получаем данные для нового отчета
        report_name = request.form.get('report_name')
        report_type = request.form.get('report_type')
        report_subtype = request.form.get('report_subtype')
        comment = request.form.get('comment')
        report_side = request.form.get('report_side') == 'true'
        profile_id = g.current_profile.id

        # Получаем существующий отчет
        existing_report = Report.query.get(existing_report_id)
        if not existing_report:
            return jsonify({"status": "error", "message": "Report not found"}), 404

        public = False
        # Создаем новый отчет на основе существующего
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=public,
            report_side=report_side
        )

        # Копируем абзацы и предложения из существующего отчета в новый
        for paragraph in existing_report.report_to_paragraphs:
            new_paragraph = Paragraph.create(
                paragraph_index=paragraph.paragraph_index,
                report_id=new_report.id,
                paragraph=paragraph.paragraph,
                paragraph_visible=paragraph.paragraph_visible,
                title_paragraph=paragraph.title_paragraph,
                bold_paragraph=paragraph.bold_paragraph,
                type_paragraph_id=paragraph.type_paragraph_id,
                comment=None,
                paragraph_weight=1
            )

            for sentence in paragraph.paragraph_to_sentences:
                Sentence.create(
                    paragraph_id=new_paragraph.id,
                    index=sentence.index,
                    weight=sentence.weight,
                    comment=sentence.comment,
                    sentence=sentence.sentence
                )

        return jsonify({"status": "success", 
                        "message": "Report created from existing report successfully", 
                        "report_id": new_report.id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
    
@new_report_creation_bp.route('/create_report_from_existing_few', methods=['POST'])
@auth_required()
def create_report_from_existing_few():
    try:
        # Получаем данные из запроса
        data = request.get_json()
        report_name = data.get("report_name")
        report_subtype = data.get("report_subtype")
        comment = data.get("comment")
        report_side = data.get("report_side")
        additional_paragraphs = int(data.get("additional_paragraphs", 0))
        selected_reports = data.get("selected_reports")
        profile_id = g.current_profile.id
        scanparam = 5
        impression = 3

        if not selected_reports or not isinstance(selected_reports, list):
            return jsonify({"status": "error", 
                            "message": "No reports selected or invalid format"}), 400


        # Создаем новый отчет
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=False,
            report_side=report_side
        )

        paragraph_index = 2
        scanparam_sentences = []
        impression_sentences = []

        # Копируем данные из выбранных отчетов
        for idx, report_id in enumerate(selected_reports):
            existing_report = Report.query.get(report_id)
            if not existing_report:
                return jsonify({"status": "error", 
                                "message": f"Report with ID {report_id} not found"}), 404

            # Получаем и сортируем параграфы по их индексу
            sorted_paragraphs = sorted(existing_report.report_to_paragraphs, key=lambda p: p.paragraph_index)
            
            # Копируем параграфы и предложения
            for paragraph in sorted_paragraphs:
                if paragraph.type_paragraph_id == scanparam:
                    for sentence in paragraph.paragraph_to_sentences:
                        scanparam_sentences.append(sentence.sentence)
                    continue
                        
                if paragraph.type_paragraph_id == impression:
                    for sentence in paragraph.paragraph_to_sentences:
                        impression_sentences.append(sentence.sentence)
                    continue
                
                new_paragraph = Paragraph.create(
                    paragraph_index=paragraph_index,
                    report_id=new_report.id,
                    paragraph=paragraph.paragraph,
                    paragraph_visible=paragraph.paragraph_visible,
                    title_paragraph=paragraph.title_paragraph,
                    bold_paragraph=paragraph.bold_paragraph,
                    type_paragraph_id=paragraph.type_paragraph_id,
                    comment=paragraph.comment,
                    paragraph_weight=paragraph.paragraph_weight
                )
                paragraph_index += 1

                for sentence in paragraph.paragraph_to_sentences:
                    Sentence.create(
                        paragraph_id=new_paragraph.id,
                        index=sentence.index,
                        weight=sentence.weight,
                        comment=sentence.comment,
                        sentence=sentence.sentence
                    )

            # Добавляем дополнительные параграфы между отчетами, кроме последнего
            if idx < len(selected_reports) - 1:
                for _ in range(additional_paragraphs):
                    Paragraph.create(
                        paragraph_index=paragraph_index,
                        report_id=new_report.id,
                        paragraph="Автоматически добавленный параграф",
                        paragraph_visible=True,
                        title_paragraph=True,
                        bold_paragraph=False,
                        type_paragraph_id=8,  
                        comment=None,
                        paragraph_weight=1
                    )
                    paragraph_index += 1

        # Добавляем параграфы и предложения из impression
        new_paragraph_imression = Paragraph.create(
            paragraph_index=paragraph_index,
            report_id=new_report.id,
            paragraph="Заключение",
            paragraph_visible=True,
            title_paragraph=True,
            bold_paragraph=False,
            type_paragraph_id=impression,
            comment=None,
            paragraph_weight=1
        )
        for sentence in impression_sentences:
            Sentence.create(
                paragraph_id=new_paragraph_imression.id,
                index=1,
                weight=1,
                comment='',
                sentence=sentence
            )
        
        # Добавляем параграфы и предложения из scanparam
        new_paragraph_scanparam = Paragraph.create(
            paragraph_index=1,
            report_id=new_report.id,
            paragraph="Параметры сканирования",
            paragraph_visible=True,
            title_paragraph=True,
            bold_paragraph=False,
            type_paragraph_id= scanparam,
            comment=None,
            paragraph_weight=1
        )
        for sentence in scanparam_sentences:
            Sentence.create(
                paragraph_id=new_paragraph_scanparam.id,
                index=1,
                weight=1,
                comment='',
                sentence=sentence
            )
        
        # Возвращаем успешный ответ
        return jsonify({"status": "success", 
                        "message": "Report created successfully", 
                        "report_id": new_report.id}), 200

    except Exception as e:
        return jsonify({"status": "error", 
                        "message": str(e)}), 500


