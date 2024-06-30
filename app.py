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

# Functions 

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


@app.route('/edit_tab', methods=['POST', 'GET'])
@login_required
def edit_tab(): 
    new_report_query = request.args.get("new_report_query")   # The line for check if user want to create new report
    type_subtype_editing_query = request.args.get("type_subtype_editing_query") 
    report_types = ReportType.query.all()  
    report_subtypes = ReportSubtype.query.all() 
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype}
        for rst in report_subtypes
    ]
    # All reports of current user with load of linked records (types and subtypes) by method in class
    user_reports_rel = get_user_reports()
    
    # If user want to make new report show them form for report creation
    if request.method == "POST":
        if "report_creation_form_view" in request.form:
            return redirect(url_for("edit_tab", new_report_query=True))
        
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
        
        # If user press button "add new type or subtype we show them form for editing types and subtypes"
        if "type_subtype_edit_form_view" in request.form:
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        
        # Processing type
        if "add_new_type_button" in request.form:
            ReportType.create(type=request.form["new_type"])
            flash("New type was created successfully")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        if "delete_type_button" in request.form:
            try:
                ReportType.delete_by_id(request.form["type_id"])
                flash("Type was deleted successfully")
            except:
                flash("It's impossible to delele the type because of existing of the reports with this type")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        if "edit_type_button" in request.form:
            type_for_editing = ReportType.query.get(request.form["type_id"])
            type_for_editing.type = request.form["type_type"]
            type_for_editing.save()
            flash("Type edited successfully")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        
        # Processing subtype
        if "add_new_subtype_button" in request.form:
            ReportSubtype.create(type=request.form["report_subtype_type"], subtype=request.form["new_subtype"])
            flash("New subtype was created successfully")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        if "delete_subtype_button" in request.form:
            try:
                ReportSubtype.delete_by_id(request.form["subtype_id"])
                flash("Subtype was deleted successfully")
            except:
                flash("It's impossible to delele the subtype because of existing of the reports with this type")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        if "edit_subtype_button" in request.form:
            subtype_for_editing = ReportSubtype.query.get(request.form["subtype_id"])
            subtype_for_editing.subtype = request.form["subtype_subtype"]
            subtype_for_editing.save()
            flash("Subtype edited successfully")
            return redirect(url_for("edit_tab", type_subtype_editing_query=True))
        
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
                           user_reports_rel=user_reports_rel,
                           type_subtype_editing_query=type_subtype_editing_query
                           )


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
                
    return render_template(
        "report_work.html", 
        title=report.report_name,
        menu=menu,
        report = report,
        paragraph_data = paragraph_data                   
    )

@app.teardown_appcontext
def close_db(error):
    db.session.remove()



if __name__ == "__main__":
    app.run(debug=True, port=5001)
