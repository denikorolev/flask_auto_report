# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify, g
from models import db, Report, Paragraph, Sentence, ParagraphType
from errors_processing import print_object_structure
from utils import get_max_index, check_main_sentences
from flask_security.decorators import auth_required


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

@editing_report_bp.route('/edit_report', methods=["GET"])
@auth_required()
def edit_report():
    page_title = "Editing report"
    report_id = request.args.get("report_id")
    report = None

    if report_id:
        report = Report.query.get(report_id)
        if not report or report.profile_id != g.current_profile.id:
            return jsonify({"status": "error", "message": "Report not found or you don't have permission to edit it"}), 403

    report_paragraphs = sorted(report.report_to_paragraphs, key=lambda p: p.paragraph_index) if report else []
    for paragraph in report_paragraphs:
        paragraph.paragraph_to_sentences = sorted(paragraph.paragraph_to_sentences, key=lambda s: (s.index, s.weight))
        # Добавляем маркер для разделения предложений
        previous_index = None
        for sentence in paragraph.paragraph_to_sentences:
            sentence.show_separator = previous_index is not None and previous_index != sentence.index
            previous_index = sentence.index
    paragraph_types = ParagraphType.query.all()


    return render_template('edit_report.html', 
                           title=page_title, 
                           report=report,
                           report_paragraphs=report_paragraphs,
                           paragraph_types=paragraph_types
                           )


@editing_report_bp.route('/update_report', methods=['PUT'])
@auth_required()
def update_report():

    report_id = request.form.get("report_id")
    report = Report.query.get(report_id)
    
    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Report not found or profile data of this paragraph doesn't match with current profile"}), 403

    try:
        report.report_name = request.form.get("report_name")
        report.comment = request.form.get("comment")
        report_side_value = request.form.get("report_side")
        report.report_side = True if report_side_value == "true" else False
        report.save()
        return jsonify({"status": "success", "message": "Report updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Can't update report. Error code: {e}"}), 400



@editing_report_bp.route('/new_paragraph', methods=['POST'])
@auth_required()
def new_paragraph():
    
    report_id = request.json.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Report not found or it's profile data doesn't match with current profile"}), 403

    try:
        paragraph_index = get_max_index(Paragraph, "report_id", report_id, Paragraph.paragraph_index)
        
        default_paragraph_type = ParagraphType.query.filter_by(type_name="text").first()
        if not default_paragraph_type:
            return jsonify({"status": "error", "message": "Default paragraph type 'text' not found."}), 400
        
        Paragraph.create(
            report_id=report.id,
            paragraph_index=paragraph_index,
            paragraph="insert your text",
            type_paragraph_id=default_paragraph_type.id,
            paragraph_visible=True,
            title_paragraph=False,
            bold_paragraph=False,
            paragraph_weight=1,
            tags="",
            comment=None
        )
        return jsonify({"status": "success", "message": "Paragraph added successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Something went wrong. Error code: {e}"}), 400


@editing_report_bp.route('/edit_paragraph', methods=['POST'])
@auth_required()
def edit_paragraph():

    paragraph_id = request.form.get("paragraph_id")
    paragraph_for_edit = Paragraph.query.get(paragraph_id)

    if not paragraph_for_edit or paragraph_for_edit.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Paragraph not found or data of this paragraph doesn't match with current profile"}), 404

    try:
        # Получаем предлагаемый тип параграфа
        new_type_paragraph_id = int(request.form.get("paragraph_type"))
        current_report_id = paragraph_for_edit.report_id
        # Список типов параграфов, которые могут быть не уникальными
        allowed_paragraph_types = [ParagraphType.find_by_name("text"), ParagraphType.find_by_name("custom"), ParagraphType.find_by_name("title")]
        # Сначала проверим, если предлагаемый тип не 'text' и не 'custom' и не "title"
        if new_type_paragraph_id not in allowed_paragraph_types:
            # Проверим, существует ли уже параграф с таким типом для данного отчета
            existing_paragraph = Paragraph.query.filter_by(
                report_id=current_report_id,
                type_paragraph_id=new_type_paragraph_id
            ).first()

            if existing_paragraph and existing_paragraph.id != paragraph_for_edit.id:
                # Если существует другой параграф с этим типом, не обновляем тип
                # Сохраняем остальные изменения
                paragraph_for_edit.paragraph_index = request.form.get("paragraph_index")
                paragraph_for_edit.paragraph = request.form.get("paragraph_name")
                paragraph_for_edit.paragraph_visible = request.form.get("paragraph_visible") == "on"
                paragraph_for_edit.title_paragraph = request.form.get("title_paragraph") == "on"
                paragraph_for_edit.bold_paragraph = request.form.get("bold_paragraph") == "on"

                paragraph_for_edit.save()
                return jsonify({
                    "status": "success",
                    "message": "Paragraph updated successfully, but the type was not changed because a paragraph with this type already exists."
                }), 200

        # Если тип 'text', 'custom' или такого типа еще нет, сохраняем все изменения, включая тип
        paragraph_for_edit.paragraph_index = request.form.get("paragraph_index")
        paragraph_for_edit.paragraph = request.form.get("paragraph_name")
        paragraph_for_edit.paragraph_visible = request.form.get("paragraph_visible") == "on"
        paragraph_for_edit.title_paragraph = request.form.get("title_paragraph") == "on"
        paragraph_for_edit.bold_paragraph = request.form.get("bold_paragraph") == "on"
        paragraph_for_edit.type_paragraph_id = new_type_paragraph_id

        paragraph_for_edit.save()
        return jsonify({"status": "success", "message": "Paragraph updated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Something went wrong. Error code: {e}"}), 400


@editing_report_bp.route('/delete_paragraph', methods=["DELETE"])
@auth_required()
def delete_paragraph():
    
    paragraph_id = request.json.get("paragraph_id")
    paragraph = Paragraph.query.get(paragraph_id)

    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Paragraph not found or data of this paragraph doesn't match with current profile"}), 404

    try:
        Paragraph.delete_by_id(paragraph_id)
        return jsonify({"status": "success", "message": "Paragraph deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete paragraph. Error code: {e}"}), 400

# Массовое редактирование предложений
@editing_report_bp.route('/edit_sentences_bulk', methods=['POST'])
@auth_required()
def edit_sentences_bulk():

    data = request.get_json()

    try:
        for sentence_data in data:
            if sentence_data.get("sentence_id") == "new":
                # Логика для создания нового предложения
                print(f"Creating new sentence for paragraph_id={sentence_data.get('add_sentence_paragraph')}")
                print(f"Данные из редактирования отчета, для проверки, теперь тут только main!!!!!! {sentence_data.get('is_main')}")
                sentence_index = sentence_data.get("sentence_index")
                paragraph_id = sentence_data.get("add_sentence_paragraph")
                try:
                    Sentence.create(
                        paragraph_id=paragraph_id,
                        index=sentence_index,
                        weight=sentence_data.get("sentence_weight"),
                        is_main=sentence_data.get("is_main"),
                        tags="",
                        comment=sentence_data.get("sentence_comment"),
                        sentence=sentence_data.get("sentence_sentence")
                    )
                except Exception as e:
                    print(f"can't create new sentence - {e}")
                    return jsonify({"status": "error", "message": "can't create new sentence"}), 500
                    
            else:
                # Логика для обновления существующего предложения
                sentence_for_edit = Sentence.query.get(sentence_data["sentence_id"])
                print(f"Updating sentence with id={sentence_for_edit.id}")
                print(f"Данные по статусу предложения, is_main={sentence_data['is_main']}")
                sentence_for_edit.index = sentence_data["sentence_index"]
                sentence_for_edit.weight = sentence_data["sentence_weight"]
                sentence_for_edit.comment = sentence_data["sentence_comment"]
                sentence_for_edit.sentence = sentence_data["sentence_sentence"]
                sentence_for_edit.save()
        return jsonify(success=True, message="All sentences updated successfully")
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, message=f"Something went wrong. error code: {e}")
    
    
@editing_report_bp.route('/delete_sentence', methods=['DELETE'])
@auth_required()
def delete_sentence():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    sentence_id = data.get("sentence_id")
    sentence = Sentence.query.get(sentence_id)

    if not sentence:
        return jsonify({"status": "error", "message": "Sentence not found"}), 404

    if sentence.sentence_to_paragraph.paragraph_to_report.report_to_profile.id != g.current_profile.id:
        return jsonify({"status": "error", "message": "You don't have permission to delete this sentence"}), 403

    try:
        Sentence.delete_by_id(sentence_id)
        return jsonify({"status": "success", "message": "Sentence deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete sentence. Error code: {e}"}), 400


@editing_report_bp.route("make_sentence_main", methods=["POST"])
@auth_required()
def make_sentence_main():
    print("make_sentence_main start--------------------------------")
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    print(data)
    sentence_id = int(data.get("sentence_id"))
    paragraph_id = int(data.get("paragraph_id"))
    sentence_index = int(data.get("sentence_index"))
    
    if not sentence_id or not paragraph_id or not sentence_index:
        print("There is no sentence_id or paragraph_id or sentence_index in request")
        return jsonify({"status": "error", "message": "В запросе не хватает данных"}), 400

    paragraph = Paragraph.query.get(paragraph_id)
    if not paragraph or paragraph.paragraph_to_report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Paragraph not found or data of this paragraph doesn't match with current profile"}), 404

    try:
        sentences = Sentence.query.filter_by(paragraph_id = paragraph_id, index = sentence_index).all()
        for sentence in sentences:
            print(f"sentence id={sentence.id} checked sentence_id={sentence_id}")
            if sentence.id == sentence_id:
                print(f"make sentence main id={sentence.id}!!!!!!!!!!!!!!!!")
                sentence.is_main = True
            else:
                sentence.is_main = False
            sentence.save()
        print("make_sentence_main end--------------------------------")
        return jsonify({"status": "success", "message": "Sentence is now main"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to make sentence main. Error code: {e}"}), 400



@editing_report_bp.route('/check_report_for_excess_ismain', methods=['POST'])
@auth_required()
def check_report_for_excess_ismain():
    """
    Проверяет, есть ли в каждом наборе предложений с одинаковым index ровно одно is_main.
    Если index = 0, то в этом наборе не должно быть is_main.
    Возвращает отчет с информацией о проблемах в параграфах.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    report_id = data.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.profile_id != g.current_profile.id:
        return jsonify({"status": "error", "message": "Report not found or data of this report doesn't match with current profile"}), 404

    errors = check_main_sentences(report)
    
    return jsonify({"status": "success", "errors": errors}), 200