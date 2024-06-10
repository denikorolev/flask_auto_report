# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.sql import text
import os
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload


load_dotenv()
app = Flask(__name__)

# Configuration all in the file .env
app.config["DB_HOST"] = os.getenv("DB_HOST")
app.config["PORT"] = os.getenv("PORT")
app.config['DB_NAME'] = os.getenv("DB_NAME")
app.config['DB_USER'] = os.getenv("DB_USER")
app.config['DB_PASS'] = os.getenv("DB_PASS", "")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "my_secret_key")

# Construct the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASS']}@{app.config['DB_HOST']}:{app.config['PORT']}/{app.config['DB_NAME']}"

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# List for menu
menu = [
    {"name": "main", "url": "main"},
    {"name": "report", "url": "report"},
    {"name": "edit tab", "url": "edit_tab"}
]

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    user_role = db.Column(db.String, nullable=False)
    user_email = db.Column(db.String, unique=True, nullable=False)
    user_name = db.Column(db.String, nullable=False)
    user_pass = db.Column(db.String, nullable=False)
    user_bio = db.Column(db.Text, nullable=True)
    user_avatar = db.Column(db.LargeBinary, nullable=True)

    def set_password(self, password):
        self.user_pass = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_pass, password)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.BigInteger, primary_key=True)
    userid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    report_name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.Integer, db.ForeignKey('report_type.id'), nullable=False)
    report_subtype = db.Column(db.Integer, db.ForeignKey('report_subtype.id'), nullable=False)
    report_paragraphs = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    report_type_rel = db.relationship('ReportType', backref=db.backref('reports', lazy=True))
    report_subtype_rel = db.relationship('ReportSubtype', backref=db.backref('reports', lazy=True))


class ReportType(db.Model):
    __tablename__ = 'report_type'
    id = db.Column(db.SmallInteger, primary_key=True)
    type = db.Column(db.String(50), nullable=False)

class ReportSubtype(db.Model):
    __tablename__ = 'report_subtype'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.SmallInteger, db.ForeignKey('report_type.id'), nullable=False)
    subtype = db.Column(db.String(250), nullable=False)

class ReportParagraph(db.Model):
    __tablename__ = "report_paragraphs"
    
    id = db.Column(db.BigInteger, primary_key=True)
    paragraph_index = db.Column(db.Integer, nullable=False)
    userid = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    report_type = db.Column(db.Integer, db.ForeignKey("report_type.id"), nullable=False)
    report = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)

    user = db.relationship("User", backref=db.backref("report_paragraphs", lazy=True))
    report_type_rel = db.relationship("ReportType", backref=db.backref("report_paragraphs", lazy=True))
    report_rel = db.relationship("Report", backref=db.backref("report_paragraphs", lazy=True))


# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# This is only for redirection to the main page
@app.route("/")
def index():
    return redirect(url_for("main"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(user_email=user_email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main"))
        flash("Invalid credentials", "error")
    return render_template("login.html", title="LogIn")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_role = "user"
        user_email = request.form["email"]
        user_name = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(user_email=user_email).first():
            flash("Email already exists", "error")
            return redirect(url_for("signup"))
        # Create object of class user and then create pass-hash
        user = User(user_email=user_email, user_name=user_name, user_role=user_role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully", "success")
        return redirect(url_for("login"))
    return render_template("signup.html", title="SignUp")

@app.route('/main', methods=['POST', 'GET'])
@login_required
def main():
    test_db_connection()
    return render_template('index.html', title="Main page Radiologary", menu=menu)


@app.route('/edit_tab', methods=['POST', 'GET'])
@login_required
def edit_tab(): 

    new_report_query = request.args.get("new_report_query")   # The line for check if user want to create new report
    report_types = ReportType.query.all()
    report_subtypes = ReportSubtype.query.all()
    # Convert objects to dictionary
    report_subtypes_dict = [
        {'id': rst.id, 'type_id': rst.type, 'subtype': rst.subtype}
        for rst in report_subtypes
    ]
    # All reports of current user with load of linked records (types and subtypes)
    user_reports = Report.query.filter_by(userid=current_user.id).options(
        joinedload(Report.report_type_rel),
        joinedload(Report.report_subtype_rel)
    ).all()
    
    # If user want to make new report show them form for report creation
    if request.method == "POST":
        if "report_creation_form_view" in request.form:
            return redirect(url_for('edit_tab', new_report_query=True))
        
    # If user press button "create new report we created new report and redirect to page for editing new report"
        if "report_creation" in request.form:
            report_name = request.form["report_name"]
            report_type_id = request.form["report_type"]
            report_subtype_id = request.form["report_subtype"]
            comment = request.form["comment"]

            # New string in the tab reports
            new_report = Report(
                userid=current_user.id,
                report_name=report_name,
                report_type=report_type_id,
                report_subtype=report_subtype_id,
                comment=comment
            )
            db.session.add(new_report)
            db.session.commit()
            flash("Report created successfully", "success")
            return redirect(url_for("edit_report", report_id=new_report.id))
            

        if "report_delete" in request.form:
            report_id = request.form["report_id"]
            report_to_delete = Report.query.get(report_id)
            if report_to_delete:
                db.session.delete(report_to_delete)
                db.session.commit()
                flash("Report deleted successfully", "success")
            else:
                flash("Report not found", "error")
            return redirect(url_for("edit_tab"))
                
        
    return render_template("edit_tab.html", 
                           title="Edit table", 
                           menu=menu,
                           new_report_query=new_report_query, 
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict, 
                           user_reports=user_reports)

@app.route('/report', methods=['POST', 'GET'])
@login_required
def report(): 
    return render_template(
        'report.html',
        title="Report",
        menu=menu
    )

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
    # Refresh report in table
    if request.method == "POST": 
        if "report_update" in request.form:
            report.report_name = request.form['report_name']
            report.comment = request.form['comment']
            try:
                db.session.commit()
                flash("Report updated successfully", "success")
                return redirect(url_for('edit_tab'))
            except Exception as e:
                flash(f"Can't update report. Error code: {e}")
                return redirect(url_for('edit_report'))
    
    
    return render_template('edit_report.html', 
                           title="Edit report", 
                           menu=menu, 
                           report=report,
                           report_types=report_types, 
                           report_subtypes=report_subtypes_dict)
    
    
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
