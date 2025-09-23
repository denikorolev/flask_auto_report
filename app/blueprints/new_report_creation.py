# new_report_creation.py

from flask import Blueprint, render_template, request, session, jsonify
from flask_login import current_user
from app.models.models import db, Report, ReportCategory, Paragraph, HeadSentence, BodySentence, TailSentence, ReportShare, HeadSentenceGroup, BodySentenceGroup, TailSentenceGroup
from app.utils.sentence_processing import extract_paragraphs_and_sentences
from app.utils.file_processing import allowed_file
from app.utils.common import ensure_list
from werkzeug.utils import secure_filename
from app.utils.logger import logger
import os
import shutil 
from flask_security.decorators import auth_required
from tasks.celery_tasks import template_generating
import json
from app.utils.redis_client import redis_set
from celery.result import AsyncResult
from app.utils.redis_client import redis_get

new_report_creation_bp = Blueprint('new_report_creation', __name__)


# Функции

def create_report_from_existing(report_name, category_2_id, comment, report_side, selected_reports):
    """
    Создает новый отчет на основе одного или нескольких существующих.
    Возвращает созданный объект отчета или выбрасывает исключение при ошибке.
    """
    cat_1_id, global_cat_id = get_parent_categories(category_2_id)
    if not cat_1_id or not global_cat_id:
        raise ValueError("Неверная категория протокола")
    
    user_id = current_user.id
    profile_id = session.get("profile_id")
    
    new_report = Report.create(
        profile_id=profile_id,
        category_1_id=cat_1_id,
        category_2_id=category_2_id,
        global_category_id=global_cat_id,
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


# Функция принимает id категории второго уровня и возвращает id категории первого уровня и глобальной категории
def get_parent_categories(category_2_id: int):
    """
    Получает категорию 2 уровня (область исследования), возвращает 
    ее родительскую категорию и глобальную категорию для модальности.
    Args:
        category_2_id (int): ID категории второго уровня.
    Returns:
        tuple: (category_1_id, global_category_id)
    """
    
    category_2 = ReportCategory.get_by_id(category_2_id)
    if not category_2:
        logger.warning(f"[get_parent_categories] ❌ Категория второго уровня с ID {category_2_id} не найдена")
        return None, None
    category_1 = ReportCategory.get_by_id(category_2.parent_id) if category_2.parent_id else None
    if not category_1:
        logger.warning(f"[get_parent_categories] ❌ Родительская категория для категории второго уровня с ID {category_2_id} не найдена")
        return None, None
    global_category = ReportCategory.get_by_id(category_1.global_id) if category_1.global_id else None
    if not global_category:
        logger.warning(f"[get_parent_categories] ⚠️ Глобальная категория для категории первого уровня с ID {category_1.id} не найдена")
        return category_1.id, None
    return category_1.id, global_category.id
# Routes


# Загрузка основной страницы создания отчета
@new_report_creation_bp.route('/create_report', methods=['GET'])
@auth_required()
def create_report():
    global_categories = ReportCategory.get_categories_tree(is_global=True)
    return render_template("new_report_creation.html",
                           title="Создание нового протокола",
                           global_categories=global_categories
                           )
    
    
@new_report_creation_bp.route("/get_existing_reports", methods=["GET"])
@auth_required()
def get_existing_reports():
    logger.info("[get_existing_reports]------------------------")
    logger.info("[get_existing_reports] 🚀 Начат запрос существующих протоколов пользователя")
    try:
        category_1_id = request.args.get("modality_id", type=int)
        global_category_id = request.args.get("global_modality_id", type=int)
         # Получаем profile_id из сессии
        profile_id = session.get("profile_id")
        # базовый запрос
        query = Report.query.filter_by(user_id=current_user.id, profile_id=profile_id)
        # узкий фильтр только по категории первого уровня (если передана)
        if category_1_id:
            query = query.filter(Report.global_category_id == global_category_id)
        user_reports = query.all()

        if not user_reports:
            return jsonify({"status": "success", "reports": []})

        reports_data = [{
            "id": r.id,
            "report_name": r.report_name,
        } for r in user_reports]
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
        global_category_id = request.args.get("global_modality_id", type=int)
        category_name = request.args.get("modality_name", type=str)
        shared_records = ReportShare.query.filter_by(shared_with_user_id=current_user.id).all()

        if not shared_records:
            logger.info("[get_shared_reports] ⚠️ Нет протоколов, которыми кто-либо поделился с данным пользователем.")
            return jsonify({"status": "warning", "message": "Нет протоколов, которыми кто-либо поделился с данным пользователем.", "reports": []})

        shared_reports = []
        for rec in shared_records:
            report = rec.report
            if not report:
                continue  # на случай, если отчет удалён
            # Фильтруем по типу, если указан
            if global_category_id and report.global_category_id != global_category_id:
                continue

            shared_reports.append({
                "id": report.id,
                "report_name": report.report_name,
                "modality": category_name,
                "shared_by": rec.shared_by.username if rec.shared_by else "Неизвестно",
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
        modality_name = request.args.get("modality_name", type=str)
        global_modality_id = request.args.get("global_modality_id", type=int)
        query = Report.query.filter(Report.public == True)
        if global_modality_id:
            query = query.filter(Report.global_category_id == global_modality_id)
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
                "modality": modality_name,
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
    logger.info("[create_manual_report] 🚀 Начато создание протокола вручную")
    logger.info("[create_manual_report]------------------------")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Не получены данные для создания протокола"}), 400
        
        report_name = data.get('report_name')
        category_2_id = data.get('report_area')
        if not report_name:
            logger.warning("[create_manual_report] ❌ Необходимо указать название протокола")
            return jsonify({"status": "error", "message": "Необходимо указать название протокола"}), 400
        comment = data.get('comment', "")
        report_side = data.get('report_side', False)
        cat_1_id, global_cat_id = get_parent_categories(category_2_id)
        if not cat_1_id or not global_cat_id:
            logger.warning("[create_manual_report] ❌ Неверная категория протокола")
            return jsonify({"status": "error", "message": "Неверная категория протокола"}), 400

        profile_id = session.get("profile_id")
        
        # Create new report
        new_report = Report.create(
            profile_id=profile_id,
            category_1_id=cat_1_id,
            category_2_id=category_2_id,
            global_category_id=global_cat_id,
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
    logger.info("[create_report_from_file] 🚀 Начато создание протокола из файла")
    logger.info("[create_report_from_file]------------------------")
    
    try:
        report_name = request.form.get('report_name')
        category_2_id = int(request.form.get('report_area'))
        if not report_name or not category_2_id:
            logger.warning("[create_report_from_file] ❌ Необходимо указать название протокола и его область исследования")
            return jsonify({"status": "error", 
                            "message": "Необходимо указать название протокола и его область исследования"}), 400
        comment = request.form.get('comment', "")
        report_side = request.form.get('report_side') == 'true'

        profile_id = session.get("profile_id")
        user_id = current_user.id
        
        cat_1_id, global_cat_id = get_parent_categories(category_2_id)
        if not cat_1_id or not global_cat_id:
            logger.warning("[create_report_from_file] ❌ Неверная категория протокола")
            return jsonify({"status": "error", 
                            "message": "Неверная категория протокола"}), 400
        

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
                        category_1_id=cat_1_id,
                        category_2_id=category_2_id,
                        global_category_id=global_cat_id,
                        report_name=report_name,
                        user_id=current_user.id,
                        comment=comment,
                        public=public,
                        report_side=report_side
                    )

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
                                        report_global_modality_id=cat_1_id,
                                        sentence=split_sentence.strip(),
                                        related_id=new_paragraph.id,
                                        sentence_index=sentence_index
                                    )
                                
                                else:
                                    BodySentence.create(
                                        user_id=user_id,
                                        report_global_modality_id=cat_1_id,
                                        sentence=split_sentence.strip(),
                                        related_id=new_head_sentence.id,
                                        sentence_index=sentence_index
                                    )
                        else:
                            HeadSentence.create(
                                user_id=user_id,
                                report_global_modality_id=cat_1_id,
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
        category_2_id = int(data.get("report_area"))
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
            category_2_id=category_2_id,
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



# Создание нового протокола на основе публичного 
@new_report_creation_bp.route('/create_report_from_public', methods=['POST'])
@auth_required()
def create_report_from_public_route():
    logger.info("(Маршрут: создание протокола из публичного) 🚀 Начато создание протокола из public")

    try:
        data = request.get_json()
        report_name = data.get("report_name")
        category_2_id = int(data.get("report_area"))
        if not report_name or not category_2_id:
            logger.warning("(Маршрут: создание протокола из публичного) ❌ Необходимо указать название протокола и его область исследования")
            return jsonify({"status": "error", "message": "Необходимо указать название протокола и его область исследования"}), 400
        comment = data.get("comment", "")
        report_side = data.get("report_side", False)
        public_report_id = int(data.get("selected_report_id"))
        profile_id = session.get("profile_id")
        cat_1_id, global_cat_id = get_parent_categories(category_2_id)
        if not cat_1_id or not global_cat_id:
            logger.warning("(Маршрут: создание протокола из публичного) ❌ Неверная категория протокола")
            return jsonify({"status": "error", "message": "Неверная категория протокола"}), 400

        public_report = Report.get_by_id(public_report_id)
        if not public_report or not public_report.public:
            logger.error("(Маршрут: создание протокола из публичного) ❌ Выбранный протокол не является общедоступным")
            return jsonify({"status": "error", "message": "Выбранный протокол не является общедоступным"}), 400

        new_report = Report.create(
            profile_id=profile_id,
            category_1_id=cat_1_id,
            category_2_id=category_2_id,
            global_category_id=global_cat_id,
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
                    report_global_modality_id=global_cat_id,
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

   
# Создание нового протокола на основе расшаренного
@new_report_creation_bp.route('/create_report_from_shared', methods=['POST'])
@auth_required()
def create_report_from_shared_route():
    logger.info("(Маршрут: создание протокола из shared) 🚀 Начато создание протокола из shared")

    try:
        data = request.get_json()
        report_name = data.get("report_name")
        category_2_id = int(data.get("report_area"))
        if not report_name or not category_2_id:
            logger.warning("(Маршрут: создание протокола из shared) ❌ Необходимо указать название протокола и его область исследования")
            return jsonify({"status": "error", "message": "Необходимо указать название протокола и его область исследования"}), 400
        comment = data.get("comment", "")
        report_side = data.get("report_side", False)
        shared_report_id = int(data.get("selected_report_id"))
        profile_id = session.get("profile_id")
        
        cat_1_id, global_cat_id = get_parent_categories(category_2_id)
        
        # Ставлю ограничительь глубины копировния предложений сюда, возможно потом сделаю возможность его менять (например, в настройках)
        deep_limit = 10

        shared_record = ReportShare.query.filter_by(report_id=shared_report_id, shared_with_user_id=current_user.id).first()
        if not shared_record:
            return jsonify({"status": "error", "message": "Выбранный расшаренный протокол не найден"}), 400

        shared_report = shared_record.report
        
        new_report = Report.create(
            profile_id=profile_id,
            category_1_id=cat_1_id,
            category_2_id=category_2_id,
            global_category_id=global_cat_id,
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
                    report_global_modality_id=global_cat_id,
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
                            report_global_modality_id=global_cat_id,
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
                        report_global_modality_id=global_cat_id,
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
    


# Маршрут для генерации шаблона отчета при помощи ИИ. 
# 1 часть сбор данных и отправка их ИИ.
@new_report_creation_bp.route('/ai_generate_template', methods=['POST'])
@auth_required()
def ai_generate_template():
    logger.info("(Маршрут: ai_generate_template) 🚀 Начата генерация шаблона с помощью AI")
    data = request.get_json()
    template_text = data.get('origin_text').strip()
    template_name = data.get('template_name').strip()
    template_modality_id = data.get('template_modality_id')
    template_modality_name = data.get('template_modality_name')
    template_area_id = data.get('template_area_id')
    template_area_name = data.get('template_area_name')
    global_template_modality_id = data.get('global_template_modality_id')
    comment = data.get('comment', "")
    report_side = data.get('report_side', False)
    
    user_id = current_user.id

    if not all([template_name, 
                template_modality_id, 
                template_area_id, 
                template_text, 
                template_modality_name, 
                template_area_name, 
                user_id]):
        return jsonify({"status": "error", "message": "Не все данные для генерации шаблона предоставлены"}), 400

    assistant_id = os.getenv("OPENAI_ASSISTANT_TEMPLATE_MAKER")
    prompt = f"""

    The report title: {template_name}
    The imaging modality: {template_modality_name}
    The anatomical area: {template_area_name}
    The text of the radiology report: {template_text}
    """
    try:
        task = template_generating.delay(template_text=prompt, 
                                         assistant_id=assistant_id,
                                         user_id=user_id, 
                                         )
        # Сохраняем контекст для последующей обработки результата (по task_id)
        try:
            data_cache = {
                "template_name": template_name,
                "template_modality_id": template_modality_id,
                "template_modality_name": template_modality_name,
                "template_area_id": template_area_id,
                "template_area_name": template_area_name,
                "global_template_modality_id": global_template_modality_id,
                "comment": comment,
                "report_side": report_side,
            }
            redis_set(f"task_ctx:ai_template:{task.id}", json.dumps(data_cache), ex=600)
        except Exception as cache_err:
            logger.warning(f"(ai_generate_template) ⚠️ Не удалось сохранить контекст задачи в Redis: {cache_err}")
            return jsonify({"status": "error", "message": "Сбой сохранения промежуточных данных. Невозможно сгенерировать шаблон при помощи ИИ. Попробуйте создать шаблон другим способом или повторите попытку позже."}), 500
                
        logger.info(f"(Маршрут: ai_generate_template) ✅ Генерация шаблона успешно запущена.")
        return jsonify({"status": "success", "message": "Генерация шаблона запущена.", "task_id": task.id}), 200
    except Exception as e:
        logger.error(f"(Маршрут: ai_generate_template) ❌ Ошибка при запуске генерации шаблона: {e}")
        return jsonify({"status": "error", "message": "Не удалось запустить генерацию шаблона."}), 500
    
    
# 2 часть получение результата от ИИ и создание шаблона
@new_report_creation_bp.route('/get_ai_generated_template', methods=['GET', 'POST'])
@auth_required()
def get_ai_generated_template():
    logger.info("(Маршрут: get_ai_generated_template) 🚀 Начато получение результата генерации шаблона с помощью AI")
    task_id = request.args.get('task_id', type=str)
    print(f"Получен task_id: {task_id}")
    if not task_id:
        logger.warning("(Маршрут: get_ai_generated_template) ❌ Не указан ID задачи")
        return jsonify({"status": "error", "message": "Не указан ID задачи"}), 400
    logger.info(f"(Маршрут: get_ai_generated_template) ▶️ Запрос результата по task_id={task_id}")
    task = AsyncResult(task_id)
    if not task:
        logger.error(f"(Маршрут: get_ai_generated_template) ❌ Задача с ID {task_id} не найдена")
        return jsonify({"status": "error", "message": "Данные по данной генерации ИИ не найдены на сервере"}), 404
    template_data_from_ai = task.result
    logger.info(f"(Маршрут: get_ai_generated_template) Ответ от ИИ получен: {template_data_from_ai}")
    if not template_data_from_ai:
        logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка получения результата задачи из Celery для task_id: {task_id}")
        return jsonify({"status": "error", "message": "Результат генерации шаблона не валиден."}), 202
    try:
        if isinstance(template_data_from_ai, dict):
            status = template_data_from_ai.get("status", "error")
            if status != "success":
                message = template_data_from_ai.get("message", "Ошибка генерации шаблона")
                logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка генерации шаблона: {message}")
                return jsonify({"status": "error", "message": message}), 500
            paragraphs = template_data_from_ai.get("paragraphs", "[]")
        else:
            template_data = json.loads(template_data)
            status = template_data.get("status", "error")
            if status != "success":
                message = template_data.get("message", "Ошибка генерации шаблона")
                logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка генерации шаблона: {message}")
                return jsonify({"status": "error", "message": message}), 500
            paragraphs = template_data.get("paragraphs", "[]")
            
        template_data = redis_get(f"task_ctx:ai_template:{task_id}")
        if not template_data:
            logger.warning(f"(Маршрут: get_ai_generated_template) ❌ Не удалось получить контекст задачи из Redis для task_id: {task_id}")
            return jsonify({"status": "error", "message": "Сбой получения промежуточных данных. Невозможно создать шаблон при помощи ИИ. Попробуйте создать шаблон другим способом или повторите попытку позже."}), 500
        template_data = json.loads(template_data)
    except Exception as e:
        logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка при обработке результата задачи: {e}")
        return jsonify({"status": "error", "message": "Не удалось обработать результат задачи."}), 500
    try:
        report_name = template_data.get("template_name", "AI Template") 
        category_2_id = template_data.get("template_area_id")
        category_1_id = template_data.get("template_modality_id")
        global_category_id = template_data.get("global_template_modality_id")
        profile_id = session.get("profile_id")
        user_id = current_user.id
        comment = template_data.get("comment", "")
        report_side = template_data.get("report_side", False)
        new_report = Report.create(
            profile_id=profile_id,
            category_1_id=category_1_id,
            category_2_id=category_2_id,
            global_category_id=global_category_id,
            report_name=report_name,
            user_id=user_id,
            comment=comment,
            public=False,
            report_side=report_side
        )
        if not new_report:
            logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка при создании нового протокола в БД")
            return jsonify({"status": "error", "message": "Не удалось создать шаблон протокола."}), 500
        for idx, paragraph in enumerate(paragraphs, start=1):
            sentences = paragraph.get('sentences', [])
            new_paragraph = Paragraph.create(
                report_id=new_report.id,
                paragraph_index=idx,
                paragraph=paragraph['paragraph'],
            )
            for sentence_index, sentence_data in enumerate(sentences, start=1):
                if isinstance(sentence_data, str):
                    HeadSentence.create(
                        user_id=user_id,
                        report_global_modality_id=global_category_id,
                        sentence=sentence_data.strip(),
                        related_id=new_paragraph.id,
                        sentence_index=sentence_index
                    )
                else:
                    logger.warning(f"(Маршрут: get_ai_generated_template) ⚠️ Неожиданный формат предложения: {sentence_data}")
                    pass
        logger.info(f"(Маршрут: get_ai_generated_template) ✅ Шаблон протокола успешно создан. ID: {new_report.id}")
        return jsonify({"status": "success", 
                        "message": "Шаблон протокола успешно создан", 
                        "report_id": new_report.id}), 200
    except Exception as e:
        logger.error(f"(Маршрут: get_ai_generated_template) ❌ Ошибка при создании шаблона протокола в БД: {e}")
        return jsonify({"status": "error", "message": "Не удалось создать шаблон протокола."}), 500
    