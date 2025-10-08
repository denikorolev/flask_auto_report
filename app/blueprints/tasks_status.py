# tasks/analyze_dynamics.py

# tasks_status.py

from flask import Blueprint, jsonify, request
from celery.result import AsyncResult
from tasks.celery_task_processing import cancel_stuck_tasks
from datetime import datetime, timezone
from app.utils.redis_client import redis_set
from app.utils.logger import logger


tasks_status_bp = Blueprint("celery_tasks", __name__)

# Маршрут для проверки статуса задачи в Celery
@tasks_status_bp.route("/task_status/<task_id>", methods=["GET"])
def task_status(task_id):
    exclude_result = request.args.get("exclude_result", default="false").lower() == "true"
    logger.warning(f"Checking status for task_id: {task_id}, exclude_result: {exclude_result}")
    # Обновляем время последнего запроса статуса. 
    # Это нужно для watchdog-функции, которая отменяет задачи, если они не были опрошены в течение 10 секунд.
    now = datetime.now(timezone.utc).isoformat()
    redis_set(f"last_poll:{task_id}", now, ex=100)

    task = AsyncResult(task_id)

    if not task:
        return jsonify({"status": "task id not_found"}), 404

    if task.state == "PENDING":
        return jsonify({"status": "pending"}), 202
    elif task.state == "STARTED":
        return jsonify({"status": "started"}), 202
    elif task.state == "SUCCESS":
        payload = {"status": "success", "result": task.result}
        if exclude_result:
            logger.info(f"Task {task_id} completed successfully. Returning result.")
            payload["result"] = task.id # нужно будет переделать и добавлять task_id отдельным ключом
            logger.info(f"payload: {payload}")
        return jsonify(payload), 200
    elif task.state == "FAILURE":
        return jsonify({"status": "error", "details": str(task.info)}), 500
    else:
        return jsonify({"status": "unknown", "details": task.state}), 202
    
    
    
    
    
    
    
    
    
    
    