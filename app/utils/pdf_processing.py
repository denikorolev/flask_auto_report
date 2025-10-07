# app/utils/pdf_utils.py

from io import BytesIO
from typing import Tuple, Optional
from pypdf import PdfReader
from app.utils.logger import logger


def has_text_layer(pdf_bytes: bytes) -> bool:
    """
    Проверяет, есть ли в PDF текстовый слой (а не просто изображения).
    Использует pypdf, потому что он стабильнее и быстрее, чем старый PyPDF2.
    """
    with BytesIO(pdf_bytes) as bio:
        reader = PdfReader(bio)
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
                if text.strip():
                    return True
            except Exception:
                # иногда отдельные страницы могут падать — игнорируем
                continue
    return False


def extract_text_from_pdf_textlayer(pdf_bytes: bytes) -> str:
    """
    Извлекает текст из PDF, если у него есть текстовый слой.
    Не выполняет OCR — работает только с PDF, где текст уже в кодировке.
    """
    texts = []
    with BytesIO(pdf_bytes) as bio:
        reader = PdfReader(bio)
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            texts.append(text)
    return "\n".join(texts).strip()