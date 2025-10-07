# openai_api.py

import os
from werkzeug.utils import secure_filename
from flask import request, jsonify, current_app, Blueprint, render_template
from flask_security.decorators import auth_required
from app.utils.logger import logger
from flask_security import current_user
from app.utils.redis_client import redis_get
from tasks.celery_tasks import async_clean_raw_text, async_impression_generating, async_report_checking, template_generating, async_ocr_extract_text
from app.utils.ai_processing import _process_openai_request, reset_ai_session, count_tokens
from datetime import datetime, timezone

openai_api_bp = Blueprint("openai_api", __name__)


# Routs
# Страница для работы вручную с OpenAI API (просто загрузка страницы "ИИ")
@openai_api_bp.route("/start_openai_api", methods=["POST", "GET"])
@auth_required()
def start_openai_api():
    return render_template(
        "openai_api.html",
        title="GPT",
    )


# Функция для создания и ведения потока GENERAL
@openai_api_bp.route("/generate_general", methods=['POST'])
@auth_required()
def generate_general():
    logger.info("(Маршрут generate_general) --------------------------------------")
    logger.info("🚀 Начата попытка генерации текста с помощью OpenAI API.")
    
    data = request.get_json()
    text = data.get("text")
    logger.debug(f"Получены данные: {data}")
    new_conversation = data.get("new_conversation", True)
    ai_assistant = current_app.config.get("OPENAI_ASSISTANT_GENERAL")
    ai_model = "gpt-4o"
    tokens = count_tokens(text, ai_model)
    if not text:
        return jsonify({"status": "error", "message": "Ваш запрос пустой."}), 400
    if not ai_assistant:
        return jsonify({"status": "error", "message": "Не удалось получить доступ к ИИ ассистенту."}), 500
    if tokens > 4000:
        return jsonify({"status": "error", "message": f"Текст слишком длинный - { tokens } токенов, попробуйте сократить его."}), 400
    
    if new_conversation:
        reset_ai_session(ai_assistant, user_id=current_user.id)
    message = _process_openai_request(text, ai_assistant, user_id=current_user.id)
    if message:
        logger.info("✅ Ответ ассистента получен успешно")
        logger.debug(f"Ответ: {message}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "data": message}), 200
    else:
        logger.error("❌ Ошибка при получении ответа от ассистента.")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": "Ошибка при получении ответа от ассистента."}), 500


# Функция для обращения к ассистенту REDACTOR
@openai_api_bp.route("/generate_redactor", methods=['POST'])
@auth_required()
def generate_redactor():
    logger.info("(Маршрут generate_redactor) --------------------------------------")
    logger.info("🚀 Начата попытка генерации текста с помощью OpenAI API.")
    data = request.get_json()
    report_text = data.get("text")
    today_date = datetime.now(timezone.utc).isoformat()
    logger.debug(f"Получены данные: {data}")
    ai_assistant = current_app.config.get("OPENAI_ASSISTANT_REDACTOR")
    if not report_text:
        return jsonify({"status": "error", "message": "Your request is empty"}), 400
    if not ai_assistant:
        return jsonify({"status": "error", "message": "Assistant ID is not configured."}), 500
    try:
        task = async_report_checking.delay(ai_assistant, current_user.id, report_text, today_date)
        logger.info("✅ Задача по проверке отчета успешно запущена в Celery")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "message": "Запущена проверка отчета", "data": task.id}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске задачи по проверке отчета: {str(e)}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": str(e)}), 500
        
     
    
# Функция для генерации текста заключения (обращается к разным ассистентам в зависимости от модальности)
@openai_api_bp.route("/generate_impression", methods=['POST'])
@auth_required()
def generate_impression():
    logger.info("(Маршрут generate_impression) --------------------------------------")
    logger.info("🚀 Начата попытка генерации текста с помощью OpenAI API.")

    user_id = current_user.id
    
    try:
        data = request.get_json()
        text = data.get("text")
        modality = data.get("modality")
        logger.debug(f"Получены данные: {data}")

        if not text:
            return jsonify({"status": "error", "message": "Your request is empty"}), 400
        if not modality:
            return jsonify({"status": "error", "message": "Modality is missing"}), 400

        file_key = f"user:{user_id}:impression_file_id:{modality}"
        file_id = redis_get(file_key)
        if not file_id:
            logger.error(f"No impression file ID found in Redis for modality: {modality}")
            return jsonify({"status": "error", "message": "No impression file ID found, ATTENTION REQUIRED"}), 400

        # Получение assistant_id по modality
        if modality == "MRI":
            assistant_id = current_app.config.get("OPENAI_ASSISTANT_MRI")
        elif modality == "CT":
            assistant_id = current_app.config.get("OPENAI_ASSISTANT_CT")
        elif modality == "XRAY":
            assistant_id = current_app.config.get("OPENAI_ASSISTANT_XRAY")
        else:
            return jsonify({"status": "error", "message": f"Unknown modality: {modality}"}), 400

        if not assistant_id:
            return jsonify({"status": "error", "message": "Assistant ID is not configured."}), 500

        data = async_impression_generating.delay(assistant_id, user_id, text, file_id)
        logger.info("✅ Задача по генерации заключения успешно запущена в Celery")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "message": "Запущена генерация заключения", "data": data.id}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске задачи по генерации заключения: {str(e)}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": str(e)}), 500


# Маршрут для предварительной очистки текста испльзую в new_report_creation и в analyze_dinamics 
@openai_api_bp.route("/clean_raw_text", methods=['POST'])
@auth_required()
def clean_raw_text_route():
    logger.info("(Маршрут clean_raw_text_route) --------------------------------------")
    logger.info(f"(Маршрут clean_raw_text_route) 🚀 Начата очистка текста с помощью OpenAI API.")
    data = request.get_json()
    raw_text = data.get("raw_text", "")
    user_id = current_user.id
    if not raw_text.strip():
        logger.error(f"(Маршрут clean_raw_text_route) ❌ Не передан текст для очистки")
        return jsonify({"status": "error", "message": "Не передан текст"}), 400
    try:
        assistant_id=current_app.config.get("OPENAI_ASSISTANT_TEXT_CLEANER")
        logger.info(f"Assistant ID: {assistant_id}")
        task = async_clean_raw_text.delay(raw_text, user_id, assistant_id)
        logger.info(f"(Маршрут clean_raw_text_route) ✅ Очистка текста успешно запущена в Celery задачу")
        logger.info(f"(Маршрут clean_raw_text_route) ------------------------------------------")
        return jsonify({"status": "success", "message": "Запущена очистка текста", "data": task.id}), 200
    except Exception as e:
        logger.error(f"(Маршрут clean_raw_text_route) ❌ Ошибка при очистке текста: {str(e)}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": str(e)}), 500



# Маршрут для извлечения текста из загруженного файла
@openai_api_bp.route("/ocr_extract_text", methods=["POST"])
@auth_required()
def ocr_extract_text():
    logger.info("(OCR) 🚀 Start")

    if "file" not in request.files:
        logger.warning("(OCR) ⚠️ Файл не передан в запросе")
        return jsonify({"status": "error", "message": "Файл не передан ('file')."}), 400

    f = request.files["file"]
    if not f.filename:
        logger.warning("(OCR) ⚠️ Пустое имя файла")
        return jsonify({"status": "error", "message": "Пустое имя файла."}), 400

    filename = secure_filename(f.filename)

    try:
        file_bytes = f.read()
        if not file_bytes:
            logger.warning(f"(OCR) ⚠️ Файл '{filename}' пустой или не удалось прочитать содержимое")
            return jsonify({"status": "error", "message": "Файл пустой или повреждён."}), 400
        logger.info(f"(OCR) 📄 Файл '{filename}' получен, size={len(file_bytes)} bytes")
    except Exception as e:
        logger.exception(f"(OCR) ❌ Ошибка при чтении файла '{filename}': {e}")
        return jsonify({
            "status": "error",
            "message": f"Не удалось прочитать файл: {str(e)}"
        }), 500

    try:
        task = async_ocr_extract_text.delay(file_bytes, filename)
        logger.info(f"(OCR) ✅ queued task={task.id}")
        return jsonify({
            "status": "success",
            "message": "OCR задача запущена",
            "data": task.id
        }), 200
    except Exception as e:
        logger.exception(f"(OCR) ❌ Ошибка при запуске Celery-задачи OCR: {e}")
        return jsonify({
            "status": "error",
            "message": f"Ошибка при запуске OCR-задачи: {str(e)}"
        }), 500
        
        