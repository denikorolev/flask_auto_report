# переименовать и закинуть в tasks/

import base64
from tasks.extensions import celery
from app.utils.file_processing import prepare_impression_snippets
from app.utils.ai_processing import clean_raw_text, run_first_look_assistant, structure_report_text, ai_template_generator, ai_report_check, ai_impression_generation
from tasks.celery_task_processing import cancel_stale_polled_tasks, cancel_stuck_tasks
from app.utils.logger import logger
from app.utils.ocr_processing import get_ocr_provider
from app.utils.pdf_processing import has_text_layer, extract_text_from_pdf_textlayer
from celery import shared_task

# Таск для вочдога который проверяет наличие поллинговых задач и отменяет 
# их если они не были выполнены в течение долгого времени
@celery.task
def celery_cancel_stale_polled_tasks():
    return cancel_stale_polled_tasks()

# Таск для вочдога который проверяет наличие зависших в очереди задач и отменяет их
@celery.task
def celery_cancel_stuck_tasks():
    return cancel_stuck_tasks()

# Таск для подготовки файлов с заключениями и загрузки их в OpenAI
# Этот таск вызывается при каждом новом входе пользователя в систему (после очистки сессии)
@celery.task(name='async_prepare_impression_snippets', time_limit=120, soft_time_limit=110)
def async_prepare_impression_snippets(profile_id, user_id, user_email, exept_words):
    prepare_impression_snippets(profile_id, user_id, user_email, exept_words)
    return None
    
    
# Таск для очистки сырых текстов
@celery.task(name='async_clean_raw_text', time_limit=120, soft_time_limit=110)
def async_clean_raw_text(raw_text, user_id, assistant_id):
    logger.info(f"Запущена очистка сырых текстов для пользователя: {user_id} в Celery задаче")
    cleaned_text = clean_raw_text(raw_text, user_id, assistant_id)
    return cleaned_text


# Таск для формирования нового протокола из вставленного текста (динамика из working_with_reports)
@celery.task(name='async_analyze_dynamics', time_limit=160, soft_time_limit=160)
def async_analyze_dynamics(origin_text, template_text, user_id, skeleton, report_id, first_look_assistant_id, structure_assistant_id):
    logger.info(f"Запущен анализ динамики для пользователя: {user_id} в Celery задаче")
    
    # 1. Первый взгляд
    rough_result = run_first_look_assistant(origin_text, template_text, user_id, assistant_id=first_look_assistant_id)

    # 2. Финальная структура
    final_structured_result = structure_report_text(template_text, rough_result, user_id, assistant_id=structure_assistant_id)

    return {
        "result": final_structured_result,
        "skeleton": skeleton,
        "report_id": report_id
    }
    
    
# Таск для запуска ассистента по генерации impression протокола
@celery.task(name="async_impression_generating", time_limit=160, soft_time_limit=160)
def async_impression_generating(assistant_id, user_id, report_text, file_id):
    return ai_impression_generation(assistant_id, user_id, report_text, file_id)

    
# Таск для запуска ассистента по проверке протокола
@celery.task(name="async_report_checking", time_limit=160, soft_time_limit=160)
def async_report_checking(assistant_id, user_id, report_text, today_date):
    return ai_report_check(assistant_id, user_id, report_text, today_date)
    
    
# Таск для генерации шаблона на основе данных пользователя
@celery.task(name="template_generating", time_limit=160, soft_time_limit=160)
def template_generating(template_text, assistant_id, user_id):
    return ai_template_generator(template_text, assistant_id, user_id)


@shared_task(bind=True, name="async_ocr_extract_text", max_retries=0)
def async_ocr_extract_text(self, file_bytes_to_b64: str, filename: str, auto_prepare: bool, prepare_assistant_id: str, user_id: int) -> dict:
    """
    Универсальный OCR: если PDF с текстовым слоем — извлекаем сразу.
    Иначе — отдаём на облачный OCR провайдер.
    """
    logger.info(f"[async_ocr_extract_text] 🚀 {filename}, size={len(file_bytes_to_b64)}")
    try:
        file_bytes = base64.b64decode(file_bytes_to_b64.encode("ascii"))
        logger.info(f"[async_ocr_extract_text] ✅ Декодировка {filename} прошла успешно, декодированный файл размером={len(file_bytes)} bytes")
        provider = get_ocr_provider()
        text, method = provider.extract_text(content=file_bytes, filename=filename)
        logger.info(f"[async_ocr_extract_text] ✅ provider={method}, len={len(text)}")
        if auto_prepare:
            try:
                logger.info(f"[async_ocr_extract_text] 🤖 Автоподготовка включена, запускаю очистку текста с помощью OpenAI")
                text = clean_raw_text(text, user_id=user_id, assistant_id=prepare_assistant_id)
                logger.info(f"[async_ocr_extract_text] ✅ Очистка текста прошла успешно, новая длина текста={len(text)}")
            except Exception as e:
                logger.exception(f"[async_ocr_extract_text] ❌ Ошибка при очистке текста: {e}. Возвращаю неочищенный текст.")
        return {"text": text, "method": method}
    except Exception as e:
        logger.exception(f"[async_ocr_extract_text] ❌ {e}")
        raise
    
    
    
    