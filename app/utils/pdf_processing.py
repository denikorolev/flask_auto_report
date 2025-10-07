# app/utils/pdf_utils.py

import io
from typing import Tuple
from pypdf import PdfReader
from app.utils.logger import logger

def has_text_layer(pdf_bytes: bytes) -> bool:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return False
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
            if txt.strip():
                return True
        except Exception:
            pass
    return False

def extract_text_from_pdf_textlayer(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)