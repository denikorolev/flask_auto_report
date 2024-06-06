from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import json

app = Flask(__name__)

# Configuration
app.config["DB_HOST"] = "localhost"
app.config["PORT"] = "5432"
app.config['DB_NAME'] = 'radiologary'
app.config['DB_USER'] = 'deniskorolev'
app.config['DB_PASS'] = ''
app.config['SECRET_KEY'] = 'your_secret_key'

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
    {"name": "edit tab", "url": "edit_tab"},
    {"name": "edit db", "url": "edit_db"}
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

# UserTable model
class UserTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String, nullable=False)
    data = db.Column(db.String, nullable=False)
    user = db.relationship('User', backref=db.backref('tables', lazy=True))

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
        flash("Invalid credentials")
    return render_template("login.html", title="LogIn")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_role = request.form["role"]
        user_email = request.form["email"]
        user_name = request.form["username"]
        password = request.form["password"]
        user_bio = request.form.get("bio", "")
        user_avatar = request.files.get("avatar").read() if request.files.get("avatar") else None
        
        user = User(user_role=user_role, user_email=user_email, user_name=user_name, user_bio=user_bio, user_avatar=user_avatar)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html", title="SignUp")

@app.route('/main', methods=['POST', 'GET'])
@login_required
def main():
    db_connection_ok = test_db_connection()
    return render_template('index.html', title="Main page Radiologary", menu=menu, db_connection_ok=db_connection_ok, db_conection_showing=True)

@app.route('/edit_tab', methods=['POST', 'GET'])
@login_required
def edit_tab():
    if request.method == "POST" and "new_tab_name" in request.form:
        tab_name = str(request.form.get("new_tab_name"))
        tab_add_query = text(f"CREATE TABLE {tab_name} (id SERIAL PRIMARY KEY, tab_type VARCHAR(10) DEFAULT NULL, report_name VARCHAR(50) DEFAULT NULL, name_section VARCHAR(255) DEFAULT NULL, position_number SMALLINT DEFAULT NULL, report_text VARCHAR(1000) DEFAULT NULL);")
        db.session.execute(tab_add_query)
        db.session.commit()
        flash('New table added successfully.')

    tabs_list_query = text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE';
                    """)
    tabs_list = db.session.execute(tabs_list_query).fetchall()
    tabs_list = [name[0] for name in tabs_list]  # Clean names from tuple syntax
    
    # Delete table from db
    if request.method == "POST" and "tab_delete" in request.form:
        tab_del_name = request.form.get("tab_del_edit_name")
        tab_del_query = f"DROP TABLE {tab_del_name};"
        try:
            db.session.execute(tab_del_query)
            db.session.commit()
            flash(f"Table {tab_del_name} deleted successfully.")
        except Exception as e:
            flash(f"Something went wrong: {e}")
            return render_template("edit_tab.html", title="Edit table", menu=menu, tabs_list=tabs_list)

    # Edit form
    if request.method == "POST" and "tab_edit" in request.form:
        tab_edit_name = request.form.get("tab_del_edit_name")
        print(tab_edit_name)
        
    return render_template("edit_tab.html", title="Edit table", menu=menu, tabs_list=tabs_list)

@app.route('/report', methods=['POST', 'GET'])
def report():
    column_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'mri_lumbar_spine'")
    column_data = db.session.execute(column_query).fetchall()
    columns = [col[0] for col in column_data]

    # Fetch distinct values for each column for populating dropdowns
    column_values = {}
    for column in columns:
        value_query = text(f"SELECT DISTINCT {column} FROM mri_lumbar_spine")
        values = db.session.execute(value_query).fetchall()
        column_values[column] = [val[0] for val in values]

    data = {}
    selections = request.form

    if request.method == "POST" and selections:
        selected_values = {key: value for key, value in selections.items() if value}
        if selected_values:
            where_clauses = ' AND '.join([f"{key} = :{key}" for key in selected_values.keys()])
            sql_query = text(f"SELECT * FROM mri_lumbar_spine WHERE {where_clauses}")
            data_rows = db.session.execute(sql_query, selected_values).fetchall()
            if data_rows:
                data = {col: [row[idx] for row in data_rows] for idx, col in enumerate(columns)}
    else:
        # Fetch the first row to display initially
        initial_query = text("SELECT * FROM mri_lumbar_spine LIMIT 1")
        initial_data = db.session.execute(initial_query).fetchone()
        if initial_data:
            data = {col: [initial_data[idx]] for idx, col in enumerate(columns)}
                
    return render_template(
        'report.html',
        title="Report",
        menu=menu,
        columns=columns,
        column_values=column_values,
        data=data,
        selections=selections
    )

@app.route('/edit_db', methods=['GET', 'POST'])
def edit_db():
    if request.method == 'POST':
        # Handle the form submission to add new data
        type = request.form.get('type')
        subtype = request.form.get('subtype')
        subsubtype = request.form.get('subsubtype')
        sentences = request.form.get('sentences')

        # Convert sentences to JSON
        try:
            sentences_json = json.loads(sentences)
        except json.JSONDecodeError as er:
            flash(f'Invalid JSON format for sentences.{er}')
            return redirect(url_for('edit_db'))

        # Insert new data into the database
        new_entry = Test(type=type, subtype=subtype, subsubtype=subsubtype, sentences=sentences_json)
        db.session.add(new_entry)
        db.session.commit()
        flash('New data added successfully.')
        return redirect(url_for('edit_db'))

    # Fetch existing data from the database
    rows = Test.query.all()

    return render_template('edit_db.html', title="Edit page", menu=menu, rows=rows)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(255), nullable=False)
    subtype = db.Column(db.String(255), nullable=False)
    subsubtype = db.Column(db.String(255), nullable=False)
    sentences = db.Column(db.JSON, nullable=False)

@app.teardown_appcontext
def close_db(error):
    db.session.remove()

def test_db_connection():
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    app.run(debug=True, port=5001)
