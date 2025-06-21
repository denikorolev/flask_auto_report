# переименовать и закинуть в tasks/

from tasks.extensions import celery
from file_processing import prepare_impression_snippets
from app.blueprints.openai_api import clean_raw_text, run_first_look_assistant, structure_report_text
from tasks.celery_task_processing import cancel_stale_polled_tasks, cancel_stuck_tasks
from logger import logger
from tasks.extensions import celery


@celery.task
def celery_cancel_stale_polled_tasks():
    return cancel_stale_polled_tasks()

@celery.task
def celery_cancel_stuck_tasks():
    return cancel_stuck_tasks()



@celery.task()
def async_prepare_impression_snippets(profile_id):
    prepare_impression_snippets(profile_id)
    
    
# Здесь мы определяем асинхронную задачу для подготовки переноса страрого протокола в шаблон
@celery.task(name='async_analyze_dynamics', time_limit=120, soft_time_limit=110)
def async_analyze_dynamics(origin_text, template_text, user_id, skeleton, report_id):
    logger.info(f"Запущен анализ динамики для пользователя: {user_id} в Celery задаче")
    
    # 1. Первый взгляд
    rough_result = run_first_look_assistant(origin_text, template_text, user_id)

    # 2. Финальная структура
    final_structured_result = structure_report_text(template_text, rough_result, user_id)

    return {
        "result": final_structured_result,
        "skeleton": skeleton,
        "report_id": report_id
    }