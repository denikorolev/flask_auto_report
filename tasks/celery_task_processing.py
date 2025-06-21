# tasks/celery_task_processing.py

from celery.result import AsyncResult
from datetime import datetime, timezone
from app.utils.redis_client import redis_set, redis_get, redis_delete, get_redis, redis_keys



# watchdog-функция для отмены зависших задач
def cancel_stuck_tasks(max_pending_sec=120):
    r = get_redis()
    now = datetime.now(timezone.utc)
    stuck_tasks = []
    for key in r.scan_iter("task_enqueue_time:*"):
        task_id = key.split(":", 1)[-1]
        enqueue_time_str = redis_get(key)
        if not enqueue_time_str:
            continue
        enqueue_time = datetime.fromisoformat(enqueue_time_str)
        if (now - enqueue_time).total_seconds() > max_pending_sec:
            res = AsyncResult(task_id)
            if res.state in ("PENDING", "RECEIVED"):
                res.revoke(terminate=True)
                stuck_tasks.append(task_id)
                redis_delete(key)
    return stuck_tasks


# watchdog-функция для отмены задач которые не были опрошены в течение 20 секунд
def cancel_stale_polled_tasks(timeout_sec=20):
    now = datetime.now(timezone.utc)
    killed = []
    for key in redis_keys("last_poll:*"):
        key_str = key if isinstance(key, str) else key.decode() 
        task_id = key_str.split(":", 1)[-1]
        last_poll_iso = redis_get(key_str)
        if not last_poll_iso:
            continue
        last_poll_time = datetime.fromisoformat(last_poll_iso)
        seconds_since_poll = (now - last_poll_time).total_seconds()
        if seconds_since_poll > timeout_sec:
            AsyncResult(task_id).revoke(terminate=True)
            killed.append(task_id)
            redis_delete(key_str)  
    return killed