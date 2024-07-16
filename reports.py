# reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import Report, ReportType, ReportSubtype, ReportParagraph, Sentence
from file_processing import extract_paragraphs_and_sentences

reports_bp = Blueprint('reports', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'doc', 'docx'}

@reports_bp.route('/create_report', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        method = request.form.get('method')
        if method == 'manual':
            return redirect(url_for('reports.create_report_manual'))
        elif method == 'file':
            return redirect(url_for('reports.create_report_file'))
        elif method == 'existing':
            return redirect(url_for('reports.create_report_existing'))
    
    return render_template('create_report.html')

@reports_bp.route('/create_report_manual', methods=['GET', 'POST'])
@login_required
def create_report_manual():
    if request.method == 'POST':
        report_name = request.form['report_name']
        report_type = request.form['report_type']
        report_subtype = request.form['report_subtype']
        comment = request.form['comment']
        
        new_report = Report.create(
            userid=current_user.id,
            report_name=report_name,
            report_type=report_type,
            report_subtype=report_subtype,
            comment=comment
        )
        flash("Report created successfully", "success")
        return redirect(url_for('reports.edit_report', report_id=new_report.id))
    
    return render_template('create_report_manual.html', report_types=ReportType.query.all(), report_subtypes=ReportSubtype.query.all())

@reports_bp.route('/create_report_file', methods=['GET', 'POST'])
@login_required
def create_report_file():
    if request.method == 'POST':
        if 'report_file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['report_file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Extract content from the file
            paragraphs = extract_paragraphs_and_sentences(filepath)

            # Create new report
            new_report = Report.create(
                userid=current_user.id,
                report_name=request.form["report_name"],
                report_type=request.form["report_type"],
                report_subtype=request.form["report_subtype"],
                comment=request.form["comment"]
            )

            # Add paragraphs and sentences to the report
            for idx, paragraph in enumerate(paragraphs, start=1):
                new_paragraph = ReportParagraph.create(
                    paragraph_index=idx,
                    report_id=new_report.id,
                    paragraph=paragraph['title'],
                    paragraph_visible=True
                )
                for sidx, sentence in enumerate(paragraph['sentences'], start=1):
                    Sentence.create(
                        paragraph_id=new_paragraph.id,
                        index=sidx,
                        weight=1,
                        comment='',
                        sentence=sentence
                    )

            flash("Report created from file successfully", "success")
            return redirect(url_for("reports.edit_report", report_id=new_report.id))

    return render_template('create_report_file.html', report_types=ReportType.query.all(), report_subtypes=ReportSubtype.query.all())

@reports_bp.route('/create_report_existing', methods=['GET', 'POST'])
@login_required
def create_report_existing():
    if request.method == 'POST':
        existing_report_id = request.form['existing_report_id']
        existing_report = Report.query.get(existing_report_id)

        if existing_report:
            new_report = Report.create(
                userid=current_user.id,
                report_name=request.form['report_name'],
                report_type=existing_report.report_type,
                report_subtype=existing_report.report_subtype,
                comment=request.form['comment']
            )

            for paragraph in existing_report.report_paragraphs:
                new_paragraph = ReportParagraph.create(
                    paragraph_index=paragraph.paragraph_index,
                    report_id=new_report.id,
                    paragraph=paragraph.paragraph,
                    paragraph_visible=paragraph.paragraph_visible
                )
                for sentence in paragraph.sentences:
                    Sentence.create(
                        paragraph_id=new_paragraph.id,
                        index=sentence.index,
                        weight=sentence.weight,
                        comment=sentence.comment,
                        sentence=sentence.sentence
                    )

            flash("Report created from existing report successfully", "success")
            return redirect(url_for('reports.edit_report', report_id=new_report.id))

    return render_template('create_report_existing.html', reports=Report.query.filter_by(userid=current_user.id).all())

@reports_bp.route('/edit_report', methods=['GET', 'POST'])
@login_required
def edit_report():
    report_id = request.args.get("report_id")
    report = None
    
    if report_id:
        report = Report.query.get(report_id)
        if not report or report.userid != current_user.id:
            flash("Report not found or you don't have permission to edit it", "error")
            return redirect(url_for('reports.edit_report'))
    
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
            return redirect(url_for("reports.edit_report", report_id=report.id))
            
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
            return redirect(url_for("reports.edit_report", report_id=report.id))
        
        if "delete_paragraph" in request.form:
            try:
                ReportParagraph.delete_by_id(request.form["paragraph_id"])
                flash("Paragraph deleted successfully", "success")
            except Exception as e:
                flash("Paragraph not found", "error")
            return redirect(url_for("reports.edit_report", report_id=report.id))
        
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
            return redirect(url_for("reports.edit_report", report_id=report.id))
        
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
            return redirect(url_for("reports.edit_report", report_id=report.id))
        
        if "delete_sentence" in request.form:
            try:
                Sentence.delete_by_id(request.form["sentence_id"])
                flash("sentence deleted successfully", "success")
            except Exception as e:
                flash(f"can't delete sentence. error code: {e}", "error")
            return redirect(url_for("reports.edit_report", report_id=report.id))
        
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
            return redirect(url_for("reports.edit_report", report_id=report.id))
                
    return render_template('edit_report.html', 
                           title="Edit report", 
                           menu=menu, 
                           report=report,
                           report_paragraphs=report_paragraphs,
                           report_sentences=report_sentences
                           )
