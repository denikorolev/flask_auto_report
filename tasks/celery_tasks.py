# переименовать и закинуть в tasks/

from tasks.extensions import celery
from file_processing import prepare_impression_snippets
from app.utils.ai_processing import clean_raw_text, run_first_look_assistant, structure_report_text
from tasks.celery_task_processing import cancel_stale_polled_tasks, cancel_stuck_tasks
from logger import logger
from tasks.extensions import celery

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
    
    
# Здесь мы определяем асинхронную задачу для очистки сырых текстов
@celery.task(name='async_clean_raw_text', time_limit=120, soft_time_limit=110)
def async_clean_raw_text(raw_text, user_id, assistant_id):
    logger.info(f"Запущена очистка сырых текстов для пользователя: {user_id} в Celery задаче")
    cleaned_text = clean_raw_text(raw_text, user_id, assistant_id)
    return cleaned_text
    
    
# Здесь мы определяем асинхронную задачу для подготовки переноса страрого протокола в шаблон
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