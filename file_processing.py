# file_processing.py

from flask import current_app
from flask_login import current_user
from docx import Document
import os
from unidecode import unidecode
from datetime import datetime
import glob
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_ALIGN_VERTICAL
from config import get_config


# Проверка допустимости расширения загружаемого файла
def allowed_file(file_name, file_type):
    if file_type == "doc":
        return '.' in file_name and file_name.rsplit('.', 1)[1].lower() in {'docx', "doc"}
    elif file_type == "tab":
        return '.' in file_name and file_name.rsplit('.', 1)[1].lower() in {"xlsx"}
    else:
        return False


# Function for saving word_template on server
def file_uploader (file, file_type):
    if file.filename == "":
            return "The file name is empty"
    if allowed_file(file.filename, file_type):
        name, ext = os.path.splitext(file.filename)
        name = "word_template"
        date_str = datetime.now().strftime("%d_%m_%y")
        filename_with_date = f"{name}_{date_str}{ext}"
        config_class = get_config()
        upload_folder = config_class.get_user_upload_folder()
        file_path = os.path.join(upload_folder, filename_with_date)
        try:
            file.save(file_path)
            return "The file was uploaded successfully"
        except Exception as e:
            return f"The file wasn't uploaded due to the following error: {e}"
    else:
        return "The file name or extension is not allowed"
    
    
# Function for file saving in the docx format 
def save_to_word(text, name, subtype, report_type, birthdate, reportnumber, scanParam, side=""):
    # Убираем лишние пробелы и проверяем на пустые строки
    name = name.strip() or "NoName"
    subtype = subtype.strip() or "NoSubtype"
    report_type = report_type.strip() or "NoReportType"

    try:
        date_str = datetime.now().strftime("%d_%m_%y")
        modified_date_str = date_str.replace("_", ".")
        # Преобразование строки в объект datetime
        trans_birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
        # Форматирование даты
        modified_birthdate = trans_birthdate.strftime("%d.%m.%y")
    except:
        print("date manipulation failed")
        pass
    try:
        # Используем функцию из Config для получения папки пользователя
        config_class = get_config()
        upload_folder = config_class.get_user_upload_folder()
            
            
        report_upload_folder_path = os.path.join(upload_folder, f"reports_{date_str}")
        # Создаем вложенную папку, если она не существует
        if not os.path.exists(report_upload_folder_path):
            os.makedirs(report_upload_folder_path)
            
        image_path = os.path.join(upload_folder, "Sugnatura.jpg")

        # Найти самый последний шаблон файла
        template_files = glob.glob(os.path.join(upload_folder, "word_template_*.docx"))
        # Проверяем, есть ли файлы-шаблоны
        if not template_files:
            # Сообщаем об ошибке, если нет шаблонов
            raise Exception("No template files found. Please upload a template file before generating the report.")
        # Найти самый последний по времени измененный файл
        template_path = max(template_files, key=os.path.getmtime)
        
        document = Document(template_path)
        
        def set_font_size(doc, size):
            for paragraph in doc.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(size)
                    
                    
        # Insert the required text at the beginning of the document
        paragraph = document.add_paragraph()
        run = paragraph.add_run(f"Протокол МРТ-Исследования № {reportnumber}")
        run.bold = True
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Add patient information
        p = document.add_paragraph()
        p.add_run("ФИО пациента: ").bold = True
        p.add_run(name)
        p.paragraph_format.space_before = Pt(0)  
        p.paragraph_format.space_after = Pt(0)

        p = document.add_paragraph()
        p.add_run("Дата рождения: ").bold = True
        p.add_run(modified_birthdate)
        p.add_run(" г.р.")
        p.paragraph_format.space_before = Pt(0)  
        p.paragraph_format.space_after = Pt(0)
        
        p = document.add_paragraph()
        p.add_run("Вид исследования: ").bold = True
        p.add_run(report_type)
        
        # Добавляем сторону, если она указана
        if side == "right":
            p.add_run(" правого")
        elif side == "left":
            p.add_run(" левого")
            
        p.add_run(" ")
        p.add_run(subtype)
        p.paragraph_format.space_before = Pt(0)  
        p.paragraph_format.space_after = Pt(0)
        
        p = document.add_paragraph()
        p.add_run("Техника сканирования: ").bold = True
        p.add_run(scanParam)
        p.paragraph_format.space_before = Pt(0)  
        p.paragraph_format.space_after = Pt(0)
        
        document.add_paragraph(text)

    # Create a table with one row and three columns
        table = document.add_table(rows=1, cols=3)
        table.autofit = False
        
        # Set column widths
        widths = [Inches(3), Inches(2), Inches(2)]
        for col_idx, width in enumerate(widths):
            for cell in table.columns[col_idx].cells:
                cell.width = width
                
        # First cell: Doctor's name
        cell1 = table.cell(0, 0)
        cell1.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        paragraph = cell1.paragraphs[0]
        run = paragraph.add_run("Врач-рентгенолог: Королёв Д.Г. ")
        run.bold = True
        run.font.size = Pt(12)

        # Second cell: Image
        cell2 = table.cell(0, 1)
        paragraph = cell2.paragraphs[0]
        run = paragraph.add_run()
        run.add_picture(image_path, width=Pt(70))  # Set the width as needed

        cell3 = table.cell(0, 2)
        cell3.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        paragraph = cell3.paragraphs[0]
        run = paragraph.add_run("Дата:  ")
        run.bold = True
        run.font.size = Pt(12)
        run = paragraph.add_run(modified_date_str)
        run.font.size = Pt(12)

        # Set font size for the rest of the document
        set_font_size(document, 12)
        

        # Save new document
        utf_filename = f"{name.replace(' ', '_').replace('-', '_')}_{report_type.replace(' ', '_').replace('-', '_')}_{subtype.replace(' ', '_').replace('-', '_')}_{date_str}.docx"
        new_filename = unidecode(utf_filename)
        new_file_path = os.path.join(report_upload_folder_path, new_filename)
        document.save(new_file_path)
        print(f"File saved with name: {os.path.basename(new_file_path)}")
        print(new_filename)
        print(new_file_path)
        return new_file_path
    except Exception as e:
        print(f"Error in save_to_word: {e}")
        raise Exception(f"Error in save_to_word: {e}")



