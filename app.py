# app.py

from flask import Flask, redirect, url_for, flash, render_template, request
from flask_login import LoginManager, current_user, login_required
from config import Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User, Report, ReportType, ReportSubtype, ReportParagraph, Sentence  
import pprint
from file_processing import extract_paragraphs_and_sentences
from werkzeug.utils import secure_filename
from working_with_reports import working_with_reports_bp  # Import logic of create and editing of reports
from my_reports import my_reports_bp  # Import new edit blueprint
from report_settings import report_settings_bp  # Import new settings blueprint

app = Flask(__name__)
app.config.from_object(Config) # Load configuration from file config.py

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(working_with_reports_bp, url_prefix="/working_with_reports")
app.register_blueprint(my_reports_bp, url_prefix="/my_reports")
app.register_blueprint(report_settings_bp, url_prefix="/report_settings")

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Use menu from config
menu = app.config['MENU']

# Functions 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

def test_db_connection():
    try:
        db.engine.connect()
        flash("Database connection successful", "success")
        return True
    except Exception as e:
        flash(f"Database connection failed: {e}", "error")
        return False

def get_user_reports():
    user_reports = Report.query.filter_by(userid=current_user.id).all()
    return user_reports



# This is only for redirection to the main page
@app.route("/")
def index():
    return redirect(url_for("main"))



@app.route('/main', methods=['POST', 'GET'])
@login_required
def main():
    test_db_connection()
    return render_template('index.html', title="Main page Radiologary", menu=menu)


@app.route('/edit_report', methods=['GET', 'POST'])
@login_required
def edit_report():
    report_id = request.args.get("report_id")
    report = None
    
    if report_id:
        report = Report.query.get(report_id)
        if not report or report.userid != current_user.id:
            flash("Report not found or you don't have permission to edit it", "error")
            return redirect(url_for('edit_report'))
    
    # load all paragraphs for this report
    report_paragraphs = report.report_paragraphs_list if report else []
    report_sentences = [sentence for paragraph in report_paragraphs for sentence in paragraph.sentences]

    # Refresh report in table
    if request.method == "POST": 
        if "report_update" in request.form:
            report.report_name = request.form["report_name"]
            report.comment = request.form["comment"]
            try:
                report.save()
                flash("Report updated successfully", "success")
            except Exception as e:
                flash(f"Can't update report. Error code: {e}")
            return redirect(url_for("edit_report", report_id=report.id))
            
        if "new_paragraph" in request.form:                   # Create new paragraph
            paragraph_index = 1
            if report_paragraphs:
                paragraph_length = len(report_paragraphs)
                paragraph_index += paragraph_length
                
            paragraph_visible = request.form.get("paragraph_visible") == "True"
                
            # Make new string in the tab paragraph via class
            try:
                ReportParagraph.create(
                    paragraph_index=paragraph_index,
                    report_id=report.id,
                    paragraph="insert your text",
                    paragraph_visible=paragraph_visible
                )
                flash("Paragraph added successfully", "success")
            except Exception as e:
                flash(f"Something went wrong. error code: {e}")
            return redirect(url_for("edit_report", report_id=report.id))
        
        if "delete_paragraph" in request.form:
            try:
                ReportParagraph.delete_by_id(request.form["paragraph_id"])
                flash("Paragraph deleted successfully", "success")
            except Exception as e:
                 flash("Paragraph not found", "error")
            return redirect(url_for("edit_report", report_id=report.id))
        
        if "edit_paragraph" in request.form:
            paragraph_for_edit = ReportParagraph.query.get(request.form["paragraph_id"])
            paragraph_for_edit.paragraph_index = request.form["paragraph_index"]
            paragraph_for_edit.paragraph = request.form["paragraph"]
            paragraph_for_edit.paragraph_visible = request.form.get("paragraph_visible") == "True" # Direct boolean assignment
            try:
                paragraph_for_edit.save()
                flash("Paragraph changed successfully", "success")
            except Exception as e:
                flash("Something went wrong. error code {e}", "error")
            return redirect(url_for("edit_report", report_id=report.id))
        
        if "add_sentence" in request.form:
            sentence_index = 1
            sentence_paragraph_id = request.form["add_sentence_paragraph"]
            sentences = Sentence.find_by_paragraph_id(sentence_paragraph_id)
            if sentences:
                sentence_lenght = len(sentences)
                sentence_index += sentence_lenght
            try:
                Sentence.create(
                paragraph_id= sentence_paragraph_id,
                index= sentence_index,
                weight= "1",
                comment= "norma",
                sentence= "add your sentence")
                flash("sentence created successfully", "success")
            except Exception as e:
                flash(f"sentence can't be created, error code: {e}", "error")
            return redirect(url_for("edit_report", report_id=report.id))
        
        if "delete_sentence" in request.form:
            try:
                Sentence.delete_by_id(request.form["sentence_id"])
                flash("sentence deleted successfully", "success")
            except Exception as e:
                flash(f"can't delete sentence. error code: {e}", "error")
            return redirect(url_for("edit_report", report_id=report.id))
        
        if "edit_sentence" in request.form:
            sentence_for_edit = Sentence.query.get(request.form["sentence_id"])
            sentence_for_edit.index = request.form["sentence_index"]
            sentence_for_edit.weight = request.form["sentence_weight"]
            sentence_for_edit.comment = request.form["sentence_comment"]
            sentence_for_edit.sentence = request.form["sentence_sentence"]
            try:
                sentence_for_edit.save()
                flash("changes saved successfully", "success")
            except Exception as e:
                flash(f"something went wrong. error code: {e}")
            return redirect(url_for("edit_report", report_id=report.id))
                
    return render_template('edit_report.html', 
                           title="Edit report", 
                           menu=menu, 
                           report=report,
                           report_paragraphs=report_paragraphs,
                           report_sentences=report_sentences
                           )

@app.route("/report", methods=['POST', 'GET'])
@login_required
def report(): 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    user_reports = get_user_reports()
    if request.method == "POST":
        if "select_report_type_subtype" in request.form:
            rep_type = request.form["report_type"]
            rep_subtype = request.form["report_subtype"]
            reports = Report.query.filter_by(userid = current_user.id, 
                                             report_type = rep_type, 
                                             report_subtype = rep_subtype
                                             ).all()
            return render_template(
                "report.html",
                title="Report",
                menu=menu,
                user_reports = user_reports,
                report_types = report_types,
                report_subtypes = report_subtypes,
                reports = reports
            )
        
    return render_template(
        "report.html",
        title="Report",
        menu=menu,
        user_reports = user_reports,
        report_types = report_types,
        report_subtypes = report_subtypes
    )

@app.route("/report_work", methods=['POST', 'GET'])
@login_required
def report_work(): 
    report = Report.query.get(request.args.get("report_id")) # Get report_id from url
    paragraphs = ReportParagraph.query.filter_by(report_id = report.id).order_by(ReportParagraph.paragraph_index).all()
    paragraph_data = []
    for paragraph in paragraphs:
        sentences = Sentence.query.filter_by(paragraph_id = paragraph.id).order_by(Sentence.index).all()
        
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
    pprint.pprint(paragraph_data)
                
    return render_template(
        "report_work.html", 
        title=report.report_name,
        menu=menu,
        report = report,
        paragraph_data = paragraph_data                   
    )

@app.route('/create_report', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        method = request.form.get('method')
        if method == 'manual':
            return redirect(url_for('create_report_manual'))
        elif method == 'file':
            return redirect(url_for('create_report_file'))
        elif method == 'existing':
            return redirect(url_for('create_report_existing'))
    
    return render_template('create_report.html')


@app.teardown_appcontext
def close_db(error):
    db.session.remove()



if __name__ == "__main__":
    app.run(debug=True, port=5001)
