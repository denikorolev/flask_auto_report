from flask import Blueprint, render_template, request, current_app, jsonify
from flask_login import login_required, current_user
from models import db, Report, ReportType, ReportSubtype, ReportParagraph, Sentence

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
    report = Report.query.get(request.args.get("report_id"))  # Get report_id from url
    paragraphs = ReportParagraph.query.filter_by(report_id=report.id).order_by(ReportParagraph.paragraph_index).all()
    paragraph_data = []
    for paragraph in paragraphs:
        sentences = Sentence.query.filter_by(paragraph_id=paragraph.id).order_by(Sentence.index).all()
        
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
        paragraph_data=paragraph_data                   
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
    sentence_text = data.get('new_sentence')

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