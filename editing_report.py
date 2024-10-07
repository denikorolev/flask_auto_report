# editing_report.py

from flask import Blueprint, render_template, request, current_app, jsonify
from flask_login import current_user, login_required
from models import db, Report, ReportParagraph, Sentence, ParagraphType


editing_report_bp = Blueprint('editing_report', __name__)

# Functions

# Routs

@editing_report_bp.route('/edit_report', methods=['GET', 'POST'])
@login_required
def edit_report():
    page_title = "Editing report"
    menu = current_app.config['MENU']
    report_id = request.args.get("report_id")
    report = None

    if report_id:
        report = Report.query.get(report_id)
        if not report or report.userid != current_user.id:
            return jsonify(success=False, message="Report not found or you don't have permission to edit it"), 403

    report_paragraphs = sorted(report.report_paragraphs, key=lambda p: p.paragraph_index) if report else []
    for paragraph in report_paragraphs:
        paragraph.sentences = sorted(paragraph.sentences, key=lambda s: (s.index, s.weight))
        # Добавляем маркер для разделения предложений
        previous_index = None
        for sentence in paragraph.sentences:
            sentence.show_separator = previous_index is not None and previous_index != sentence.index
            previous_index = sentence.index
            
    paragraph_types = ParagraphType.query.all()


    return render_template('edit_report.html', 
                           title=page_title, 
                           menu=menu, 
                           report=report,
                           report_paragraphs=report_paragraphs,
                           paragraph_types=paragraph_types
                           )


@editing_report_bp.route('/update_report', methods=['POST'])
@login_required
def update_report():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    report_id = data.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.userid != current_user.id:
        return jsonify({"status": "error", "message": "Report not found or you don't have permission to edit it"}), 403

    try:
        report.report_name = data.get("report_name")
        report.comment = data.get("comment")
        report_side_value = data.get("report_side")
        report.report_side = True if report_side_value == "true" else False if report_side_value == "false" else False
        report.save()
        return jsonify({"status": "success", "message": "Report updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Can't update report. Error code: {e}"}), 400



@editing_report_bp.route('/new_paragraph', methods=['POST'])
@login_required
def new_paragraph():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    report_id = data.get("report_id")
    report = Report.query.get(report_id)

    if not report or report.userid != current_user.id:
        return jsonify({"status": "error", "message": "Report not found or you don't have permission to edit it"}), 403

    try:
        paragraph_index = len(report.report_paragraphs) + 1
        paragraph_visible = data.get("paragraph_visible") == "True"
        title_paragraph = data.get("title_paragraph") == "True"
        bold_paragraph = data.get("bold_paragraph") == "True"
        
        
        # Найти тип параграфа "text" в базе данных и получить его ID
        default_paragraph_type = ParagraphType.query.filter_by(type_name="text").first()
        if not default_paragraph_type:
            return jsonify({"status": "error", "message": "Default paragraph type 'text' not found."}), 400
        
        ReportParagraph.create(
            paragraph_index=paragraph_index,
            report_id=report.id,
            paragraph="insert your text",
            paragraph_visible=paragraph_visible,
            title_paragraph=title_paragraph,
            bold_paragraph=bold_paragraph,
            type_paragraph_id=default_paragraph_type.id
        )
        return jsonify({"status": "success", "message": "Paragraph added successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Something went wrong. Error code: {e}"}), 400


@editing_report_bp.route('/edit_paragraph', methods=['POST'])
@login_required
def edit_paragraph():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    paragraph_for_edit = ReportParagraph.query.get(paragraph_id)

    if not paragraph_for_edit:
        return jsonify({"status": "error", "message": "Paragraph not found"}), 404

    if paragraph_for_edit.report.userid != current_user.id:
        return jsonify({"status": "error", "message": "You don't have permission to edit this paragraph"}), 403

    try:
        paragraph_for_edit.paragraph_index = data.get("paragraph_index")
        paragraph_for_edit.paragraph = data.get("paragraph")
        paragraph_for_edit.paragraph_visible = data.get("paragraph_visible")
        paragraph_for_edit.title_paragraph = data.get("title_paragraph")
        paragraph_for_edit.bold_paragraph = data.get("bold_paragraph")
        paragraph_for_edit.type_paragraph_id = data.get("paragraph_type_id")
        
        paragraph_for_edit.save()
        return jsonify({"status": "success", "message": "Paragraph updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Something went wrong. Error code: {e}"}), 400


@editing_report_bp.route('/delete_paragraph', methods=['POST'])
@login_required
def delete_paragraph():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    paragraph = ReportParagraph.query.get(paragraph_id)

    if not paragraph:
        return jsonify({"status": "error", "message": "Paragraph not found"}), 404

    if paragraph.report.userid != current_user.id:
        return jsonify({"status": "error", "message": "You don't have permission to delete this paragraph"}), 403

    try:
        ReportParagraph.delete_by_id(paragraph_id)
        return jsonify({"status": "success", "message": "Paragraph deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete paragraph. Error code: {e}"}), 400


@editing_report_bp.route('/edit_sentences_bulk', methods=['POST'])
@login_required
def edit_sentences_bulk():

    if not request.is_json:
        return jsonify(success=False, message="Invalid request format"), 400

    data = request.get_json()
    try:
        for sentence_data in data["sentences"]:
            print(sentence_data)
            if sentence_data["sentence_id"] == "new":
                # Логика для создания нового предложения
                print(f"Creating new sentence for paragraph_id={sentence_data['add_sentence_paragraph']}")
                sentence_index = sentence_data["sentence_index"]
                paragraph_id = sentence_data["add_sentence_paragraph"]
                Sentence.create(
                    paragraph_id=paragraph_id,
                    index=sentence_index,
                    weight=sentence_data["sentence_weight"],
                    comment=sentence_data["sentence_comment"],
                    sentence=sentence_data["sentence_sentence"]
                )
            else:
                # Логика для обновления существующего предложения
                sentence_for_edit = Sentence.query.get(sentence_data["sentence_id"])
                print(f"Updating sentence with id={sentence_for_edit.id}")
                sentence_for_edit.index = sentence_data["sentence_index"]
                sentence_for_edit.weight = sentence_data["sentence_weight"]
                sentence_for_edit.comment = sentence_data["sentence_comment"]
                sentence_for_edit.sentence = sentence_data["sentence_sentence"]
                sentence_for_edit.save()
        return jsonify(success=True, message="All sentences updated successfully")
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, message=f"Something went wrong. error code: {e}")
    
    
@editing_report_bp.route('/delete_sentence', methods=['POST'])
@login_required
def delete_sentence():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request format"}), 400

    data = request.get_json()
    sentence_id = data.get("sentence_id")
    sentence = Sentence.query.get(sentence_id)

    if not sentence:
        return jsonify({"status": "error", "message": "Sentence not found"}), 404

    if sentence.paragraph.report.userid != current_user.id:
        return jsonify({"status": "error", "message": "You don't have permission to delete this sentence"}), 403

    try:
        Sentence.delete_by_id(sentence_id)
        return jsonify({"status": "success", "message": "Sentence deleted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to delete sentence. Error code: {e}"}), 400




