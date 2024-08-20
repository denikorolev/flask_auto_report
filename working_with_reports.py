from flask import Blueprint, render_template, request, current_app, jsonify, send_file, flash, url_for
from flask_login import login_required, current_user
from models import db, Report, ReportType, ReportSubtype, ReportParagraph, Sentence
from file_processing import file_saver, print_sqlalchemy_object

working_with_reports_bp = Blueprint('working_with_reports', __name__)

# Functions

def init_app(app):
    menu = app.config['MENU']
    return menu

def get_user_reports():
    user_reports = Report.query.filter_by(userid=current_user.id).all()
    return user_reports

# Routes

@working_with_reports_bp.route("/choosing_report", methods=['POST', 'GET'])
@login_required
def choosing_report(): 
    menu = init_app(current_app)
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    user_reports = get_user_reports()
    if request.method == "POST":
        if "select_report_type_subtype" in request.form:
            rep_type = request.form["report_type"]
            rep_subtype = request.form["report_subtype"]
            reports = Report.query.filter_by(userid=current_user.id, report_type=rep_type, report_subtype=rep_subtype).all()
            return render_template(
                "choose_report.html",
                title="Report",
                menu=menu,
                user_reports=user_reports,
                report_types=report_types,
                report_subtypes=report_subtypes,
                reports=reports
            )
        
    return render_template(
        "choose_report.html",
        title="Report",
        menu=menu,
        user_reports=user_reports,
        report_types=report_types,
        report_subtypes=report_subtypes
    )

@working_with_reports_bp.route("/working_with_reports", methods=['POST', 'GET'])
@login_required
def working_with_reports(): 
    menu = init_app(current_app)
    
    if request.method == "POST":
        data = request.get_json()
        full_name = data.get("fullname", "")
        birthdate = data.get("birthdate", "")
        report_number = data.get("reportNumber", "")
        report_id = data.get("reportId")
        if report_id:
            return jsonify({"redirect_url": url_for('working_with_reports.working_with_reports', report_id=report_id, full_name=full_name, birthdate=birthdate, reportNumber=report_number)})
        else:
            return jsonify({"message": "Invalid report ID."}), 400
        
    report = Report.query.get(request.args.get("report_id"))  # Get report_id from url
    full_name = request.args.get("full_name", "")
    birthdate = request.args.get("birthdate", "")
    report_number = request.args.get("reportNumber", "")
    paragraphs = ReportParagraph.query.filter_by(report_id=report.id).order_by(ReportParagraph.paragraph_index).all()
    subtype = report.report_subtype_rel.subtype
    report_type = report.report_type_rel.type
    print_sqlalchemy_object(report) # this is debugger
    paragraph_data = []
    for paragraph in paragraphs:
        sentences = Sentence.query.filter_by(paragraph_id=paragraph.id).order_by(Sentence.index, Sentence.weight).all()
        
        grouped_sentences = {}
        for sentence in sentences:
            index = sentence.index
            if index not in grouped_sentences:
                grouped_sentences[index] = []
            grouped_sentences[index].append(sentence)
            
        paragraph_data.append({
            "paragraph": paragraph,
            "grouped_sentences": grouped_sentences
        })
                
    return render_template(
        "working_with_report.html", 
        title=report.report_name,
        menu=menu,
        report=report,
        paragraph_data=paragraph_data,
        subtype=subtype,
        report_type=report_type,
        full_name=full_name,
        birthdate=birthdate,
        report_number=report_number                   
    )

@working_with_reports_bp.route("/update_sentence", methods=['POST'])
@login_required
def update_sentence():
    data = request.get_json()
    sentence_id = data.get('sentence_id')
    new_value = data.get('new_value')

    sentence = Sentence.query.get(sentence_id)
    if sentence:
        sentence.sentence = new_value
        db.session.commit()
        return jsonify({"message": "Sentence updated successfully!"}), 200
    return jsonify({"message": "Failed to update sentence."}), 400

@working_with_reports_bp.route("/add_sentence", methods=['POST'])
@login_required
def add_sentence():
    data = request.get_json()
    paragraph_id = data.get('paragraph_id')
    index = data.get('index')
    sentence_text = "new_sentence"
    add_to_list_flag = data.get("add_to_list_flag")

    if add_to_list_flag:
         # Create new sentence
        new_sentence = Sentence(paragraph_id=paragraph_id, index=index, weight = 1, comment = "", sentence=sentence_text)
        db.session.add(new_sentence)
        db.session.commit()
            
    else:
        index += 1
        # Increment the index of all subsequent sentences
        sentences_to_update = Sentence.query.filter(Sentence.paragraph_id == paragraph_id, Sentence.index >= index).all()
        for sentence in sentences_to_update:
            sentence.index += 1
            db.session.commit()

        # Create new sentence
        new_sentence = Sentence(paragraph_id=paragraph_id, index=index, weight = 1, comment = "", sentence=sentence_text)
        db.session.add(new_sentence)
        db.session.commit()
    
    return jsonify({"message": "Sentence added successfully!"}), 200

@working_with_reports_bp.route("/delete_sentence", methods=['POST'])
@login_required
def delete_sentence():
    data = request.get_json()
    sentence_id = data.get('sentence_id')
    paragraph_id = data.get('paragraph_id')

    sentence = Sentence.query.get(sentence_id)
    if sentence:
        index = sentence.index
        db.session.delete(sentence)
        db.session.commit()

        # Обновляем индексы оставшихся предложений только если это не часть группы
        sentences_with_same_index = Sentence.query.filter(Sentence.paragraph_id == paragraph_id, Sentence.index == index).all()
        if len(sentences_with_same_index) == 0:
            # Обновляем индексы только если больше нет предложений с таким же индексом
            sentences_to_update = Sentence.query.filter(Sentence.paragraph_id == paragraph_id, Sentence.index > index).all()
            for sentence in sentences_to_update:
                sentence.index -= 1
                db.session.commit()

        return jsonify({"message": "Sentence deleted successfully!"}), 200
    return jsonify({"message": "Failed to delete sentence."}), 400

@working_with_reports_bp.route("/update_sentence_weight", methods=["POST"])
@login_required
def update_sentence_weight():
    data = request.get_json()
    sentence_id = data.get("sentence_id")
    new_weight = data.get("new_weight")

    sentence = Sentence.query.get(sentence_id)
    if sentence:
        sentence.weight = new_weight
        db.session.commit()
        return jsonify({"message": "Weight updated successfully!"}), 200
    return jsonify({"message": "Failed to update weight."}), 400


@working_with_reports_bp.route("/update_paragraph", methods=["POST"])
@login_required
def update_paragraph():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")
    new_value = data.get("new_value")

    paragraph = ReportParagraph.query.get(paragraph_id)
    if paragraph:
        paragraph.paragraph = new_value
        db.session.commit()
        return jsonify({"message": "Paragraph updated successfully!"}), 200
    return jsonify({"message": "Failed to update paragraph."}), 400

@working_with_reports_bp.route("/delete_paragraph", methods=["POST"])
@login_required
def delete_paragraph():
    data = request.get_json()
    paragraph_id = data.get("paragraph_id")

    paragraph = ReportParagraph.query.get(paragraph_id)
    if paragraph:
        db.session.delete(paragraph)
        db.session.commit()
        return jsonify({"message": "Paragraph deleted successfully!"}), 200
    return jsonify({"message": "Failed to delete paragraph."}), 400



@working_with_reports_bp.route("/export_to_word", methods=["POST"])
@login_required
def export_to_word():
    data = request.get_json()
    text = data.get("text")
    name = data.get("name")
    subtype = data.get("subtype")
    report_type = data.get("report_type")
    birthdate = data.get("birthdate")
    reportnumber = data.get("reportnumber")
    scanParam = data.get("scanParam")

    if not text or not name or not subtype:
        return jsonify({"message": "Missing required information."}), 400

    try:
        file_path = file_saver(text, name, subtype, report_type, birthdate, reportnumber, scanParam)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"message": f"Failed to export to Word: {e}"}), 500
