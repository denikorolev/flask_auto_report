from flask import Flask, render_template, request, redirect, url_for, flash, g
import psycopg2
import json

app = Flask(__name__)

# Configuration
app.config["DB_HOST"] = "localhost"
app.config["PORT"] = "5432"
app.config['DB_NAME'] = 'radiologary'
app.config['DB_USER'] = 'deniskorolev'
app.config['DB_PASS'] = ''
app.config['SECRET_KEY'] = 'your_secret_key'
menu = [{"name" : "main", "url" : "/"}, 
        {"name" : "report", "url" : "report"}, 
        {"name" : "edit tab", "url" : "edit_tab"},
        {"name" : "edit db", "url" : "edit_db"}
        ]

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASS'],
            host=app.config['DB_HOST']
        )
    return g.db

def query_db(query, args=(), commit=False, fetch=False, one=False): # When you are colling this function don't forget to point commit or fetch
    cur = get_db().cursor()
    cur.execute(query, args)
    if commit:
        get_db().commit()
    rv = None
    if fetch:
        rv = cur.fetchall()
    cur.close()
    if fetch:
        return (rv[0] if rv else None) if one else (rv if rv else None) 
    else:
        return None

def test_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASS'],
            host=app.config['DB_HOST']
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None and db.closed == 0:  # Check if the connection is open
        db.close()

# Main page
@app.route('/', methods=['POST', 'GET'])
def index():
    # Test the database connection at start-up
    db_connection_ok = test_db_connection()
    return render_template('index.html',
                           title="Main page Radiologary", 
                           menu = menu, 
                           db_connection_ok = db_connection_ok, 
                           db_conection_showing = True
                           )


# Edit table
@app.route('/edit_tab', methods=['POST', 'GET'])
def edit_tab():
    if request.method == "POST" and "new_tab_name" in request.form:
        tab_name = str(request.form.get("new_tab_name"))
        tab_add_query = f"CREATE TABLE radiologary.public.{tab_name} (id SMALLSERIAL PRIMARY KEY, tab_type VARCHAR(10) DEFAULT NULL,report_name VARCHAR(50) DEFAULT NULL, name_secton VARCHAR(255) DEFAULT NULL, position_number SMALLINT DEFAULT NULL, report_text VARCHAR(1000) DEFAULT NULL);"
        query_db(tab_add_query, commit=True, fetch=False)
        flash('New table added successfully.')
       

    tabs_list_query = """
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE';
                    """
    tabs_list = query_db(tabs_list_query, fetch=True)
    tabs_list = list((name[0] for name in tabs_list))  # Clean names from tuple syntax
    
    #Delete table from db
    if request.method == "POST" and "tab_delete" in request.form: 
        tab_del_name = request.form.get("tab_del_edit_name")
        tab_del_query = f"DROP TABLE {tab_del_name};"
        try:
            query_db(tab_del_query, commit=True)
            flash(f"Table {tab_del_name} deleted successfully.")
        except:
            flash(f"something goes wrong, try again.")
            return render_template("edit_tab.html", title="Edit table", menu=menu, tabs_list=tabs_list)

        # tab_type = request.form.get("tab_type")
        # print(f"get table info {tab_name} \n {tab_type}")
        # section_name = request.form.get("section_name")
        # position_number = request.form.get("position_number")
        # report_text = request.form.get("report_text")
        
    #Edit form
    if request.method == "POST" and "tab_edit" in request.form:
        tab_edit_name = request.form.get("tab_del_edit_name")
        print(tab_edit_name)
        
    return render_template("edit_tab.html", title="Edit table", menu=menu, tabs_list=tabs_list)
        
        
        


# Report page
@app.route('/report', methods=['POST', 'GET'])
def report():
    column_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'mri_lumbar_spine'"
    column_data = query_db(column_query, fetch=True)
    columns = [col[0] for col in column_data]
    print(f"column_data: {column_data} \n")                       # take out after testing
    print(f"column: {columns} \n")                                # take out after testing

    # Fetch distinct values for each column for populating dropdowns
    column_values = {}
    for column in columns:
        value_query = f"SELECT DISTINCT {column} FROM mri_lumbar_spine"
        values = query_db(value_query, fetch=True)
        print(f"values: {values} \n")                            # take out after testing
        column_values[column] = [val[0] for val in values]

    data = {}
    selections = request.form
    # print(selections)                            # take out after testing

    if request.method == "POST" and selections:
        selected_values = {key: value for key, value in selections.items() if value}
        if selected_values:
            where_clauses = ' AND '.join([f"{key} = %s" for key in selected_values.keys()])
            sql_query = f"SELECT * FROM mri_lumbar_spine WHERE {where_clauses}"
            data_rows = query_db(sql_query, list(selected_values.values()), fetch=True)
            print(data_rows, '\n')                       # take out after testing
            if data_rows:
                data = {col: [row[idx] for row in data_rows] for idx, col in enumerate(columns)}
                print(data)                        # take out after testing
    else:
            # Fetch the first row to display initially
            initial_query = "SELECT * FROM mri_lumbar_spine LIMIT 1"
            initial_data = query_db(initial_query, fetch=True, one=True)
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

# Editind data base
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
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO test (type, subtype, subsubtype, sentences) VALUES (%s, %s, %s, %s)",
                    (type, subtype, subsubtype, json.dumps(sentences_json)))
        conn.commit()
        cur.close()
        flash('New data added successfully.')
        return redirect(url_for('edit_db'))

    # Fetch existing data from the database
    rows = query_db("SELECT * FROM test", fetch=True)

    return render_template('edit_db.html', title="Edit page", menu=menu, rows=rows)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
