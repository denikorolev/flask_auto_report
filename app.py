# app.py


from flask import Flask, redirect, url_for, flash, render_template, request
from flask_login import LoginManager, current_user, login_required
from config import Config
from flask_migrate import Migrate
from auth import auth_bp  
from models import db, User, Report, ReportType, ReportSubtype, ReportParagraph, Sentence  

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

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# This is only for redirection to the main page
@app.route("/")
def index():
    return redirect(url_for("main"))

# List for menu
menu = [
    {"name": "main", "url": "main"},
    {"name": "report", "url": "report"},
    {"name": "edit tab", "url": "edit_tab"}
]

@app.route('/main', methods=['POST', 'GET'])
@login_required
def main():
    test_db_connection()
    return render_template('index.html', title="Main page Radiologary", menu=menu)

@app.route('/report', methods=['POST', 'GET'])
@login_required
def report(): 
    return render_template(
        'report.html',
        title="Report",
        menu=menu
    )

@app.route('/edit_tab', methods=['POST', 'GET'])
@login_required
def edit_tab(): 
    new_report_query = request.args.get("new_report_query")   # The line for check if user want to create new report
    report_types = ReportType.query.all()  # Need to check if i can remove this line
    report_subtypes = ReportSubtype.query.all() # Need to check if i can remove this line
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype}
        for rst in report_subtypes
    ]
    # All reports of current user with load of linked records (types and subtypes) by method in class
    user_reports = Report.get_reports_with_relations(current_user.id)
    
    # If user want to make new report show them form for report creation
    if request.method == "POST":
        if "report_creation_form_view" in request.form:
            return redirect(url_for('edit_tab', new_report_query=True))
        
    # If user press button "create new report we created new report and redirect to page for editing new report"
        if "report_creation" in request.form:
            # New string in the tab reports
            new_report = Report.create(
                userid=current_user.id,
                report_name=request.form["report_name"],
                report_type=request.form["report_type"],
                report_subtype=request.form["report_subtype"],
                comment=request.form["comment"]
            )
            flash("Report created successfully", "success")
            return redirect(url_for("edit_report", report_id=new_report.id))
            
        if "report_delete" in request.form:
            try:
                Report.delete_by_id(request.form["report_id"])
                flash("Report deleted successfully", "success")
            except Exception as e:
                flash(f"Report not found. error code: {e}", "error")
            return redirect(url_for("edit_tab"))
                
    return render_template("edit_tab.html", 
                           title="Edit table", 
                           menu=menu,
                           new_report_query=new_report_query, 
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict, 
                           user_reports=user_reports)


@app.route('/edit_report', methods=['GET', 'POST'])
@login_required
def edit_report():
    report_id = request.args.get('report_id')
    report = None
    
    if report_id:
        report = Report.query.get(report_id)
        if not report or report.userid != current_user.id:
            flash("Report not found or you don't have permission to edit it", "error")
            return redirect(url_for('edit_report'))
    
    report_types = ReportType.query.all()
    report_subtypes = ReportSubtype.query.all()
    # Convert objects to dictionary
    report_subtypes_dict = [
        {"id": rst.id, "type": rst.type, "subtype": rst.subtype} for rst in report_subtypes
    ]
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
            # Make new string in the tab paragraph via class
            try:
                ReportParagraph.create(
                    paragraph_index=paragraph_index,
                    report_id=report.id,
                    paragraph="insert your text"
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
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict,
                           report_paragraphs=report_paragraphs,
                           report_sentences=report_sentences
                           )

@app.teardown_appcontext
def close_db(error):
    db.session.remove()

def test_db_connection():
    try:
        db.engine.connect()
        flash("Database connection successful", "success")
        return True
    except Exception as e:
        flash(f"Database connection failed: {e}", "error")
        return False

if __name__ == "__main__":
    app.run(debug=True, port=5001)
