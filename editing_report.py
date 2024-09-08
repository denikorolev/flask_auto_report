# editing_report.py

from flask import Blueprint, render_template, request, flash, current_app, jsonify
from flask_login import current_user, login_required
from models import db, Report, ReportParagraph, Sentence  


editing_report_bp = Blueprint('editing_report', __name__)

# Functions
# Access configuration parameters
def init_app(app):
    menu = app.config['MENU']
    return menu

# Routs

@editing_report_bp.route('/edit_report', methods=['GET', 'POST'])
@login_required
def edit_report():
    page_title = "Editing report"
    menu = init_app(current_app)
    report_id = request.args.get("report_id")
    report = None

    if report_id:
        report = Report.query.get(report_id)
        if not report or report.userid != current_user.id:
            return jsonify(success=False, message="Report not found or you don't have permission to edit it"), 403

    report_paragraphs = sorted(report.report_paragraphs_list, key=lambda p: p.paragraph_index) if report else []
    for paragraph in report_paragraphs:
        paragraph.sentences = sorted(paragraph.sentences, key=lambda s: (s.index, s.weight))
        # Добавляем маркер для разделения предложений
        previous_index = None
        for sentence in paragraph.sentences:
            sentence.show_separator = previous_index is not None and previous_index != sentence.index
            previous_index = sentence.index
            
    if request.method == "POST":
        if request.is_json:  # Проверка, если данные запроса в формате JSON
            data = request.get_json()  # Получение данных JSON из запроса

            if "delete_sentence" in data:
                try:
                    Sentence.delete_by_id(data["sentence_id"])
                    return jsonify(success=True, message="Sentence deleted successfully")
                except Exception as e:
                    return jsonify(success=False, message=f"Can't delete sentence. error code: {e}")

            if "report_update" in data:
                report.report_name = data["report_name"]
                report.comment = data["comment"]
                report_side_value = data.get("report_side")
                report.report_side = True if report_side_value == "true" else False if report_side_value == "false" else None
                try:
                    report.save()
                    return jsonify(success=True, message="Report updated successfully")
                except Exception as e:
                    return jsonify(success=False, message=f"Can't update report. Error code: {e}")

            if "new_paragraph" in data:
                paragraph_index = 1
                if report_paragraphs:
                    paragraph_length = len(report_paragraphs)
                    paragraph_index += paragraph_length

                paragraph_visible = data.get("paragraph_visible") == "True"
                try:
                    ReportParagraph.create(
                        paragraph_index=paragraph_index,
                        report_id=report.id,
                        paragraph="insert your text",
                        paragraph_visible=paragraph_visible
                    )
                    return jsonify(success=True, message="Paragraph added successfully")
                except Exception as e:
                    return jsonify(success=False, message=f"Something went wrong. error code: {e}")

            if "delete_paragraph" in data:
                try:
                    ReportParagraph.delete_by_id(data["paragraph_id"])
                    return jsonify(success=True, message="Paragraph deleted successfully")
                except Exception as e:
                    return jsonify(success=False, message="Paragraph not found")

            if "edit_paragraph" in data:
                paragraph_for_edit = ReportParagraph.query.get(data["paragraph_id"])
                paragraph_for_edit.paragraph_index = data["paragraph_index"]
                paragraph_for_edit.paragraph = data["paragraph"]
                paragraph_for_edit.paragraph_visible = data["paragraph_visible"]
                try:
                    paragraph_for_edit.save()
                    return jsonify(success=True, message="Paragraph changed successfully")
                except Exception as e:
                    return jsonify(success=False, message=f"Something went wrong. error code {e}")

            if "edit_sentences_bulk" in data:
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


    return render_template('edit_report.html', 
                           title=page_title, 
                           menu=menu, 
                           report=report,
                           report_paragraphs=report_paragraphs
                           )
