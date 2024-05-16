from flask import Flask, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import pandas as pd
import os
import psycopg2

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
        {"name" : "upload", "url" : "upload"}
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

def query_db(query, args=(), one=False):
    cur = get_db().cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

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


# Upload page
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    return render_template('upload.html', title="Upload", menu=menu)


# Report page
@app.route('/report', methods=['POST', 'GET'])
def report():
    columns = []
    data = {}
    selections = None

    if request.method == "POST":
        if "filename" in request.form:
            column_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'mri_lumbar_spine'"
            column_data = query_db(column_query)
            columns = [col[0] for col in column_data]

        selected_values = {key: value for key, value in request.form.items() if not key.startswith('data_')}
        
        if selected_values:
            # Check if selected_values keys are valid columns
            for key in selected_values.keys():
                if key not in columns:
                    return f"Invalid column name: {key}", 400

            where_clauses = ' AND '.join([f"{key} = %s" for key in selected_values.keys()])
            sql_query = f"SELECT * FROM mri_lumbar_spine WHERE {where_clauses}"
            
            # Print the query and values for debugging purposes
            print("SQL Query:", sql_query)
            print("Values:", list(selected_values.values()))
            
            data_rows = query_db(sql_query, list(selected_values.values()))
            data = {col: [row[idx] for row in data_rows] for idx, col in enumerate(columns)}

            return render_template(
                'report.html',
                title="Report",
                menu=menu,
                columns=columns,
                data=data,
                selections=selected_values
            )

    column_query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'mri_lumbar_spine'"
    column_data = query_db(column_query)
    columns = [col[0] for col in column_data]

    data_query = "SELECT * FROM mri_lumbar_spine LIMIT 10"
    initial_data = query_db(data_query)
    data = {col: [row[idx] for row in initial_data] for idx, col in enumerate(columns)}

    return render_template(
        'report.html',
        title="Report",
        menu=menu,
        columns=columns,
        data=data,
        selections=selections
    )



if __name__ == "__main__":
    app.run(debug=True, port=5001)
