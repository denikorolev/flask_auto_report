# file_processing.py

from docx import Document

def extract_paragraphs_and_sentences(file_path):
    document = Document(file_path)
    paragraphs_from_file = []
    current_paragraph = None

    for para in document.paragraphs:
        if para.runs and para.runs[0].bold:
            if current_paragraph:
                paragraphs_from_file.append(current_paragraph)
            current_paragraph = {'title': para.text, 'sentences': []}
        else:
            if current_paragraph:
                current_paragraph['sentences'].append(para.text)

    if current_paragraph:
        paragraphs_from_file.append(current_paragraph)

    return paragraphs_from_file

