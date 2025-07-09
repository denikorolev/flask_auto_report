# new_report_creation.py

from flask import Blueprint, render_template, request, session, jsonify
from flask_login import current_user
from app.models.models import db, Report, ReportType, ReportSubtype, Paragraph, HeadSentence, BodySentence, TailSentence, ReportShare, HeadSentenceGroup, BodySentenceGroup, TailSentenceGroup
from app.utils.sentence_processing import extract_paragraphs_and_sentences
from app.utils.file_processing import allowed_file
from app.utils.common import ensure_list
from werkzeug.utils import secure_filename
from app.utils.logger import logger
import os
import shutil 
from flask_security.decorators import auth_required
from tasks.celery_tasks import template_generating

new_report_creation_bp = Blueprint('new_report_creation', __name__)


# Функции

def create_report_from_existing(report_name, report_subtype, comment, report_side, selected_reports):
    """
    Создает новый отчет на основе одного или нескольких существующих.
    Возвращает созданный объект отчета или выбрасывает исключение при ошибке.
    """
    
    user_id = current_user.id
    profile_id = session.get("profile_id")
    
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
                tail_sentence_group_id=paragraph.tail_sentence_group_id or None,
                is_impression=False,
                is_additional=paragraph.is_additional,
                str_after=paragraph.str_after,
                str_before=paragraph.str_before,
                is_active=paragraph.is_active,
                
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
            tail_sentence_group_id=paragraph.tail_sentence_group_id or None,
            is_additional=False,
            is_active=paragraph.is_active,
            str_after=paragraph.str_after,
            str_before=paragraph.str_before,
        )

    return new_report



# Routes

# Загрузка основной страницы создания отчета
@new_report_creation_bp.route('/create_report', methods=['GET', 'POST'])
@auth_required()
def create_report():
    profile_id = session.get("profile_id")
    report_types_and_subtypes = ReportType.get_types_with_subtypes(profile_id)
    
    return render_template("create_report.html",
                           title="Создание нового протокола",
                           report_types_and_subtypes=report_types_and_subtypes
                           )
    
    
@new_report_creation_bp.route("/get_existing_reports", methods=["GET"])
@auth_required()
def get_existing_reports():
    logger.info("[get_existing_reports]------------------------")
    logger.info("[get_existing_reports] 🚀 Начат запрос существующих протоколов пользователя")
    try:
        type_id = request.args.get("type_id", type=int)
        profile_id = session.get("profile_id")
        query = Report.query.filter_by(user_id=current_user.id, profile_id=profile_id)
        if type_id:
            # Подтянем только нужный тип
            query = query.join(ReportSubtype).filter(ReportSubtype.type_id == type_id)
        user_reports = query.all()

        if not user_reports:
            return jsonify({"status": "success", "reports": []})

        reports_data = []
        for report in user_reports:
            reports_data.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text,
                
            })
        print(reports_data)
        return jsonify({"status": "success", "reports": reports_data})

    except Exception as e:
        logger.error(f"[get_existing_reports] ❌ Ошибка при получении протоколов пользователя: {e}")
        return jsonify({"status": "error", "message": "Не удалось получить протоколы пользователя."}), 500
    
    
# Получение shared протоколов
@new_report_creation_bp.route("/get_shared_reports", methods=["GET"])
@auth_required()
def get_shared_reports():
    logger.info("[get_shared_reports]------------------------")
    logger.info("[get_shared_reports] 🚀 Начат запрос расшаренных протоколов")

    try:
        type_text = request.args.get("type_text", type=str)
        shared_records = ReportShare.query.filter_by(shared_with_user_id=current_user.id).all()

        if not shared_records:
            logger.info("[get_shared_reports] ⚠️ Нет протоколов, которыми кто-либо поделился с данным пользователем.")
            return jsonify({"status": "warning", "message": "Нет протоколов, которыми кто-либо поделился с данным пользователем.", "reports": []})

        shared_reports = []
        for record in shared_records:
            report = record.report
            if not report:
                continue  # на случай, если отчет удалён
            # Фильтруем по типу, если указан
            if type_text and report.report_to_subtype.subtype_to_type.type_text != type_text:
                continue

            shared_reports.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text,
                "shared_by_email": record.shared_by.email
            })
        if not shared_reports:
            logger.info("[get_shared_reports] ⚠️ Нет расшаренных протоколов для данной модальности.")
            return jsonify({"status": "warning", "message": "Нет расшаренных протоколов для данной модальности.", "reports": []})

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
        type_text = request.args.get("type_text", type=str)
        query = Report.query.filter(Report.public == True)
        if type_text:
            query = query.join(ReportSubtype).join(ReportType).filter(ReportType.type_text == type_text)
        public_reports = query.all()
        
        if not public_reports:
            return jsonify({
                "status": "warning",
                "message": "Нет общедоступных протоколов",
                "reports": []
            })
        public_reports_data = []
        for report in public_reports:
            public_reports_data.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text
            })

        logger.info(f"(Маршрут: get_public_reports) ✅ Найдено {len(public_reports)} общедоступных протоколов")
        return jsonify({
            "status": "success",
            "reports": public_reports_data
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
        
        profile_id = session.get("profile_id")
        
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

        profile_id = session.get("profile_id")
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
                report_type_id = Report.get_report_type_id(new_report.id)
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

    
    
# Создание нового протокола на основе одного или нескольких существующих
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



# Создание нового протокола на основе публичного или расшаренного
@new_report_creation_bp.route('/create_report_from_public', methods=['POST'])
@auth_required()
def create_report_from_public_route():
    logger.info("(Маршрут: создание протокола из публичного) 🚀 Начато создание протокола из public")

    try:
        data = request.get_json()
        report_name = data.get("report_name")
        report_subtype = int(data.get("report_subtype"))
        comment = data.get("comment", "")
        report_side = data.get("report_side", False)
        public_report_id = int(data.get("selected_report_id"))
        profile_id = session.get("profile_id")

        public_report = Report.get_by_id(public_report_id)
        if not public_report or not public_report.public:
            logger.error("(Маршрут: создание протокола из публичного) ❌ Выбранный протокол не является общедоступным")
            return jsonify({"status": "error", "message": "Выбранный протокол не является общедоступным"}), 400

        report_type_id = ReportSubtype.get_by_id(report_subtype).subtype_to_type.id
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=False,
            report_side=report_side
        )

        for paragraph in public_report.report_to_paragraphs:
            sentences = HeadSentenceGroup.get_group_sentences(paragraph.head_sentence_group_id)
            new_paragraph = Paragraph.create(
                report_id=new_report.id,
                paragraph_index=paragraph.paragraph_index,
                paragraph=paragraph.paragraph,
                paragraph_visible=paragraph.paragraph_visible,
                title_paragraph=paragraph.title_paragraph,
                bold_paragraph=paragraph.bold_paragraph,
                head_sentence_group_id=None,
                tail_sentence_group_id=None,
                is_impression=paragraph.is_impression,
                is_additional=paragraph.is_additional,
                str_after=paragraph.str_after,
                str_before=paragraph.str_before,
                is_active=paragraph.is_active
            )
            for s in sentences:
                HeadSentence.create(
                    user_id=current_user.id,
                    report_type_id=report_type_id,
                    sentence=s["sentence"],
                    related_id=new_paragraph.id,
                    sentence_index=s["sentence_index"],
                    tags=s["tags"],
                    comment=s["comment"]
                )
        logger.info("(Маршрут: создание протокола из публичного) ✅ Протокол успешно создан")
        return jsonify({"status": "success", "message": "Протокол успешно создан", "report_id": new_report.id}), 200

    except Exception as e:
        logger.error(f"(create_report_from_public_route) ❌ Ошибка: {e}")
        return jsonify({"status": "error", "message": "Не удалось создать протокол"}), 500

   
        
@new_report_creation_bp.route('/create_report_from_shared', methods=['POST'])
@auth_required()
def create_report_from_shared_route():
    logger.info("(Маршрут: создание протокола из shared) 🚀 Начато создание протокола из shared")

    try:
        data = request.get_json()
        report_name = data.get("report_name")
        report_subtype = int(data.get("report_subtype"))
        comment = data.get("comment", "")
        report_side = data.get("report_side", False)
        shared_report_id = int(data.get("selected_report_id"))
        profile_id = session.get("profile_id")
        
        # Ставлю ограничительь глубины копировния предложений сюда, возможно потом сделаю возможность его менять (например, в настройках)
        deep_limit = 10

        shared_record = ReportShare.query.filter_by(report_id=shared_report_id, shared_with_user_id=current_user.id).first()
        if not shared_record:
            return jsonify({"status": "error", "message": "Выбранный расшаренный протокол не найден"}), 400

        shared_report = shared_record.report
        report_type_id = ReportSubtype.get_by_id(report_subtype).subtype_to_type.id
        new_report = Report.create(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=current_user.id,
            comment=comment,
            public=False,
            report_side=report_side
        )

        for paragraph in shared_report.report_to_paragraphs:
            head_sentences = HeadSentenceGroup.get_group_sentences(paragraph.head_sentence_group_id)
            new_paragraph = Paragraph.create(
                report_id=new_report.id,
                paragraph_index=paragraph.paragraph_index,
                paragraph=paragraph.paragraph,
                paragraph_visible=paragraph.paragraph_visible,
                title_paragraph=paragraph.title_paragraph,
                bold_paragraph=paragraph.bold_paragraph,
                head_sentence_group_id=None,
                tail_sentence_group_id=None,
                is_impression=paragraph.is_impression,
                is_additional=paragraph.is_additional,
                str_after=paragraph.str_after,
                str_before=paragraph.str_before,
                is_active=paragraph.is_active
            )
            for hs in head_sentences:
                new_hs, _ = HeadSentence.create(
                    user_id=current_user.id,
                    report_type_id=report_type_id,
                    sentence=hs["sentence"],
                    related_id=new_paragraph.id,
                    sentence_index=hs["sentence_index"],
                    tags=hs["tags"],
                    comment=hs["comment"]
                )
                if hs["body_sentence_group_id"]:
                    logger.info(f"(!!!!!!!!!!!!!!!!!!!!!) У данного предложения есть группа body предложений. ID группы: {hs['body_sentence_group_id']}")
                    body_sentences = BodySentenceGroup.get_group_sentences(hs["body_sentence_group_id"])
                    logger.info(f"(!!!!!!!!!!!!!!!!!!!!!) Количество предложений в группе: {len(body_sentences)} и ниже они перечисленны: {body_sentences[:deep_limit]}")
                    for bs in body_sentences[:deep_limit]: 
                        logger.info(f"(!!!!!!!!!!!!!!!!!!!!!!) родительское предложение для данного имеет ID: {hs['id']}")
                        BodySentence.create(
                            user_id=current_user.id,
                            report_type_id=report_type_id,
                            sentence=bs["sentence"],
                            related_id=new_hs.id,
                            sentence_weight=bs["sentence_weight"],
                            tags=bs["tags"],
                            comment=bs["comment"]
                        )
            if paragraph.tail_sentence_group_id:
                tail_sentences = TailSentenceGroup.get_group_sentences(paragraph.tail_sentence_group_id)
                for ts in tail_sentences[:deep_limit]:
                    TailSentence.create(
                        user_id=current_user.id,
                        report_type_id=report_type_id,
                        sentence=ts["sentence"],
                        related_id=new_paragraph.id,
                        sentence_weight=ts["sentence_weight"],
                        tags=ts["tags"],
                        comment=ts["comment"]
                    )
                    logger.info(f"(!!!!!!!!!!!!!!!!!!!!!) Количество предложений в группе: {len(tail_sentences)} и ниже они перечисленны: {tail_sentences[:deep_limit]}")

        logger.info("(Маршрут: создание протокола из расшаренного) ✅ Протокол успешно создан")
        shared_record.delete()  
        return jsonify({"status": "success", "message": "Протокол успешно создан", "report_id": new_report.id}), 200

    except Exception as e:
        logger.error(f"(create_report_from_shared_route) ❌ Ошибка: {e}")
        return jsonify({"status": "error", "message": "Не удалось создать протокол"}), 500
    


@new_report_creation_bp.route('/ai_generate_template', methods=['POST'])
@auth_required()
def ai_generate_template():
    logger.info("(Маршрут: ai_generate_template) 🚀 Начата генерация шаблона с помощью AI")
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Не получены данные для генерации шаблона"}), 400
    template_text = data.get('origin_text', '')
    template_name = data.get('template_name', '').strip()
    template_type = data.get('template_type', '')
    template_subtype = data.get('template_subtype', '')
    
    user_id = current_user.id if current_user.is_authenticated else None
    

    if not all([template_name, template_type, template_subtype]):
        return jsonify({"status": "error", "message": "Не все данные для генерации шаблона предоставлены"}), 400

    assistant_id = os.getenv("OPENAI_ASSISTANT_TEMPLATE_MAKER")
    text = f"""

    The text of the radiology report: {template_text}
    The imaging modality: {template_type}
    The anatomical area: {template_subtype}
    The report title: {template_name}
    """
    try:
        task = template_generating.delay(template_data=text, user_id=user_id, assistant_id=assistant_id)
        logger.info(f"(Маршрут: ai_generate_template) ✅ Генерация шаблона успешно запущена.")
        return jsonify({"status": "success", "message": "Генерация шаблона запущена.", "task_id": task.id}), 200
    except Exception as e:
        logger.error(f"(Маршрут: ai_generate_template) ❌ Ошибка при запуске генерации шаблона: {e}")
        return jsonify({"status": "error", "message": "Не удалось запустить генерацию шаблона."}), 500
