# tasks/analyze_dynamics.py

from extensions import celery
from openai_api import (
    clean_medical_report_text,
    analyze_first_impression,
    structure_report_text
)
import logging