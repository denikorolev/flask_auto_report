
from flask import current_app
from flask_login import current_user
from docx import Document
import os
from datetime import datetime
import glob
from docx.shared import Pt, Inches
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
from models import Sentence, ReportParagraph, KeyWordsGroup


# Function for debugging. Using it you can show that is in the Alchemy object
def print_sqlalchemy_object(obj, indent=0):
    """ Recursively prints the attributes and relationships of a SQLAlchemy object """
    indent_str = ' ' * indent
    if isinstance(obj, list):
        for item in obj:
            print_sqlalchemy_object(item, indent)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            print(f"{indent_str}{key}:")
            print_sqlalchemy_object(value, indent + 2)
    elif hasattr(obj, '__dict__'):
        print(f"{indent_str}{obj.__class__.__name__} object:")
        for key, value in vars(obj).items():
            if key.startswith('_'):
                continue  # Skip internal attributes
            if isinstance(value, list) or hasattr(value, '__dict__'):
                print(f"{indent_str}  {key}:")
                print_sqlalchemy_object(value, indent + 4)
            else:
                print(f"{indent_str}  {key}: {value}")
    else:
        print(f"{indent_str}{obj}")