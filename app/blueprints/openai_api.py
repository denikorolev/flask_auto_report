# openai_api.py

from flask import request, jsonify, current_app, Blueprint, render_template, g
from openai import OpenAI
import tiktoken
import time
import json as pyjson
from flask_security.decorators import auth_required, roles_required
from sentence_processing import convert_template_json_to_text
from logger import logger
from flask_security import current_user
from models import FileMetadata
import re
from app.utils.redis_client import redis_get, redis_set, redis_delete

openai_api_bp = Blueprint("openai_api", __name__)


# Функция для подсчета токенов в тексте
def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in the input text for the given OpenAI model.
    
    :param text: The input string.
    :param model: The OpenAI model to use for tokenization ("gpt-4", "gpt-3.5-turbo", etc).
    :return: Number of tokens.
    """
    
    model = current_app.config.get('OPENAI_MODEL')
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


# Функция для обработки запроса к OpenAI
def _process_openai_request(text: str, assistant_id: str, user_id: int, file_id: str = None, clean_response: bool = True) -> str:
    """
    Internal helper that sends a user message to OpenAI Assistant and returns the assistant's reply.
    Thread and message state is automatically managed via Redis.
    """
    logger.info(f"Processing OpenAI request for assistant ID: {assistant_id} started.")

    thread_key = f"user:{user_id}:assistant:{assistant_id}:thread"
    
    api_key = current_app.config.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    thread_id = redis_get(thread_key) 
    logger.info(f"Retrieved thread ID from Redis: {thread_id}")

    if not thread_id:
        logger.info("No thread ID found, creating a new thread.")
        thread = client.beta.threads.create()
        thread_id = thread.id
        redis_set(thread_key, thread_id, ex=3600)  # Store thread ID in Redis for 1 hour
    else:
        logger.info(f"Using existing thread ID: {thread_id}")
        thread = client.beta.threads.retrieve(thread_id)
        
        

    attachments = [{"file_id": file_id, "tools": [{"type": "file_search"}]}] if file_id else None

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text,
        attachments=attachments
    )
    
    if not message:
        logger.error("Failed to create message in OpenAI thread.")
        
    
    run_args = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
    }
    
    run = client.beta.threads.runs.create(**run_args)

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        print(f"Run status: {run.status}")
        time.sleep(1)

    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc",
    )

    assistant_reply = ""
    assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]

    if assistant_messages:
        last = assistant_messages[-1]
        for content_block in last.content:
            logger.debug(f"Content block: {content_block}")
            if hasattr(content_block, "text"):
                assistant_reply += content_block.text.value
    if not assistant_reply:
        logger.warning("No assistant reply found in the messages.")
        return "Ответ ассистента не получен."
    
    # Очистка ответа от цитаты загруженного файла     
    if clean_response:
        clean_reply = re.sub(r"【.*?】", "", assistant_reply)
        logger.debug(f"Cleaned reply: {clean_reply}")
        return clean_reply
    else:
        logger.debug(f"Raw reply: {assistant_reply}")
        return assistant_reply



# Функция для сброса сессии OpenAI
def reset_ai_session(assistant_id: str, user_id: int):
    """
    Clears thread and message tracking for the given assistant from Redis.
    """
    thread_key = f"user:{user_id}:assistant:{assistant_id}:thread"
    redis_delete(thread_key)


# Функция для проверки грамматики текста с помощью OpenAI API
def gramma_correction_ai(text):
    logger.info("(функция gramma_correction_ai) --------------------------------------")
    logger.info("🚀 Начата попытка проверки текста с помощью OpenAI API.")

    try:
        language = current_app.config.get("APP_LANGUAGE", "ru")
    
        # Получение assistant_id по modality
        if language == "ru":
            assistant_id = current_app.config.get("OPENAI_ASSISTANT_GRAMMA_CORRECTOR_RU")
        else:
            raise ValueError(f"Unsupported language: {language}")

        if not assistant_id:
            raise ValueError("Assistant ID is not configured.")

        # Обработка запроса
        reset_ai_session(assistant_id, user_id=current_user.id)
        assistant_reply = _process_openai_request(text, assistant_id, user_id=current_user.id)

        logger.info("(функция gramma_correction_ai) ✅ Ответ ассистента получен успешно")
        logger.debug(f"(функция gramma_correction_ai) Ответ: {assistant_reply}")
        logger.info("---------------------------------------------------")
        return assistant_reply

    except Exception as e:
        logger.exception(f"(функция gramma_correction_ai) ❌ Unexpected error: {str(e)}")
        raise ValueError(f"Ошибка при обращении к ИИ: error {e}")
  
  
# Функция для очистки текста с помощью OpenAI. Использую в analyze_dinamics в working_with_reports.py
def clean_raw_text(raw_text: str, user_id: int, max_attempts: int = 2) -> str:
    logger.info("(Функция clean_raw_text) --------------------------------------")
    logger.info("[clean_raw_text] 🚀 Начата очистка текста с помощью OpenAI API.")
    logger.info("---------------------------------------------------")
    
    cleaner_assistant_id = current_app.config.get("OPENAI_ASSISTANT_TEXT_CLEANER")
    if not cleaner_assistant_id:
        logger.error("[clean_raw_text] ❌ Assistant ID for text cleaner is not configured.")
        raise ValueError("Assistant ID for text cleaner is not configured.")
    
    for attempt in range(max_attempts):
        try:
            cleaned = _process_openai_request(
                text=raw_text,
                assistant_id=cleaner_assistant_id,
                user_id=user_id,
                file_id=None,
                clean_response=False
            )
            if cleaned:
                logger.info(f"[clean_raw_text] ✅ Очистка текста успешна на попытке {attempt + 1}.")
                logger.info(f"[clean_raw_text] Очистка текста: {cleaned}")
                logger.info("---------------------------------------------------")
                return cleaned
        except Exception as e:
            logger.warning(f"[clean_raw_text] ❌ Попытка {attempt + 1} не удалась: {e}")
        finally:
            reset_ai_session(cleaner_assistant_id, user_id=user_id)

    logger.warning("[clean_raw_text] ⚠️ Все попытки не удались, возвращаю исходный текст")
    logger.info("---------------------------------------------------")
    return raw_text



# Функция для запуска ассистента первого взгляда. Использую в analyze_dinamics в working_with_reports.py
def run_first_look_assistant(cleaned_text: str, template_text: list, user_id: int, max_attempts: int = 2) -> str:
    logger.info("(Функция run_first_look_assistant) --------------------------------------")
    logger.info("[run_first_look_assistant] 🚀 Начата попытка получения первого взгляда с помощью OpenAI API.")
    logger.info("---------------------------------------------------")
    
    converted_template_text = convert_template_json_to_text(template_text)
    if not converted_template_text:
        logger.error("[run_first_look_assistant] ❌ Не удалось конвертировать шаблон в текст.")
        raise ValueError("Не удалось конвертировать шаблон в текст.")

    prompt = f"""TEMPLATE REPORT:
                {converted_template_text}
                RAW REPORT:
                {cleaned_text}
                """
                
    first_look_assistant_id = current_app.config.get("OPENAI_ASSISTANT_FIRST_LOOK_RADIOLOGIST")
    if not first_look_assistant_id:
        logger.error("[run_first_look_assistant] ❌ Assistant ID for first look is not configured.")
        raise ValueError("Assistant ID for first look is not configured.")

    for attempt in range(max_attempts):
        try:
            result = _process_openai_request(
                text=prompt,
                assistant_id=first_look_assistant_id,
                user_id=user_id,
                file_id=None,
                clean_response=False
            )
            if result:
                logger.info(f"[run_first_look_assistant] ✅ Получение первого взгляда успешно на попытке {attempt + 1}.")
                logger.info(f"[run_first_look_assistant] Ответ ассистента: {result}")
                logger.info("---------------------------------------------------")
                return result
        except Exception as e:
            logger.warning(f"[run_first_look_assistant] ❌ Попытка {attempt + 1} не удалась: {e}")
        finally:
            reset_ai_session(first_look_assistant_id, user_id=user_id)

    logger.error("[run_first_look_assistant] ❌ Все попытки получения первого взгляда не удались")
    logger.info("---------------------------------------------------")
    raise ValueError("Все попытки получения первого взгляда не удались.")


# Окончательное структурирование протокола с помощью OpenAI API
def structure_report_text(template_text: list, report_text: str, user_id: int, max_attempts: int = 2) -> list:
    logger.info("(Функция structure_report_text) --------------------------------------")
    logger.info("[structure_report_text] 🚀 Начата попытка структурирования отчета с помощью OpenAI API.")
    logger.info("---------------------------------------------------")

    prompt = f"""REPORT TEMPLATE:
                {template_text}
                ORIGINAL MEDICAL REPORT TEXT:
                {report_text}
                """

    structurer_assistant_id = current_app.config.get("OPENAI_ASSISTANT_DYNAMIC_STRUCTURER")
    if not structurer_assistant_id:
        logger.error("[structure_report_text] ❌ Assistant ID for structurer is not configured.")
        raise ValueError("Assistant ID for structurer is not configured.")

    for attempt in range(max_attempts):
        try:
            result_text = _process_openai_request(
                text=prompt,
                assistant_id=structurer_assistant_id,
                user_id=user_id,
                file_id=None,
                clean_response=False,
            )
            if not result_text:
                logger.warning(f"[structure_report_text] ❌ Попытка {attempt + 1} не удалась: пустой ответ от ассистента.")
                continue
            logger.info(f"[structure_report_text] Получен ответ от ассистента на попытке {attempt + 1}.")
            
            try:
                # Попытка загрузить ответ как JSON
                parsed = pyjson.loads(result_text)
            except pyjson.JSONDecodeError:
                logger.warning(f"[structure_report_text] ❌ Ответ ассистента не является корректным JSON.")
                raise ValueError("Ответ ассистента не является корректным JSON. Не удалось распарсить.")
            
            if isinstance(parsed, dict):
                logger.info("[structure_report_text] ✅ Ответ ассистента является словарем. Достаю report.")
                para_list = parsed.get("report", [])
                logger.info(f"[structure_report_text] ✅ Удалось достать report. Теперь report это список содержащий: {len(para_list)} элементов.")
            elif isinstance(parsed, list):
                logger.info(f"[structure_report_text] 🙌 Ответ ассистента является списком с {len(parsed)} элементами. Пробую обработать его")
                para_list = parsed
            else:
                logger.error("[structure_report_text] ❌ Ответ ассистента не является ни списком, ни словарем.")
                raise ValueError("Ответ ассистента не является ни списком, ни словарем.")
            
            if para_list:
                logger.info(f"[structure_report_text] ✅ Структурирование отчета успешно на попытке {attempt + 1}.")
                logger.info(f"[structure_report_text] Отчет ассистента по структурированию: {para_list}")
                logger.info("---------------------------------------------------")
                return para_list
        except Exception as e:
            logger.warning(f"[structure_report_text] ❌ Попытка {attempt + 1} не удалась: {e}")
        finally:
            reset_ai_session(structurer_assistant_id, user_id=user_id)

    logger.error("[structure_report_text] ❌ Все попытки структурирования отчета не удались")
    logger.info("---------------------------------------------------")
    raise ValueError("Все попытки структурирования отчета не удались.")
    
    
  
  
  
# Routs

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
    tokens = count_tokens(text)
    if not text:
        return jsonify({"status": "error", "message": "Your request is empty"}), 400
    if not ai_assistant:
        return jsonify({"status": "error", "message": "Assistant ID is not configured."}), 500
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



# Функция для создания и ведения потока REDACTOR
@openai_api_bp.route("/generate_redactor", methods=['POST'])
@auth_required()
def generate_redactor():
    logger.info("(Маршрут generate_redactor) --------------------------------------")
    logger.info("🚀 Начата попытка генерации текста с помощью OpenAI API.")
    data = request.get_json()
    text = data.get("text")
    logger.debug(f"Получены данные: {data}")
    ai_assistant = current_app.config.get("OPENAI_ASSISTANT_REDACTOR")
    if not text:
        return jsonify({"status": "error", "message": "Your request is empty"}), 400
    if not ai_assistant:
        return jsonify({"status": "error", "message": "Assistant ID is not configured."}), 500
    try:
        reset_ai_session(ai_assistant, user_id=current_user.id)
        message = _process_openai_request(text, ai_assistant, user_id=current_user.id)
        if not message:
            logger.error("❌ Ошибка при получении ответа от ассистента.")
            logger.info("---------------------------------------------------")
            return jsonify({"status": "error", "message": "Ошибка при получении ответа от ассистента."}), 500
        logger.info("✅ Ответ ассистента получен успешно")
        logger.info(f"Ответ: {message}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "data": message}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка при получении ответа от ассистента: {str(e)}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": "Ошибка при получении ответа от ассистента."}), 500
     
    

@openai_api_bp.route("/generate_impression", methods=['POST'])
@auth_required()
def generate_impression():
    logger.info("(Маршрут generate_impression) --------------------------------------")
    logger.info("🚀 Начата попытка генерации текста с помощью OpenAI API.")

    user_id = current_user.id if current_user.is_authenticated else None
    
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
            logger.error({f"No impression file ID found in Redis for modality: {modality}"}), 400

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

        # Обработка запроса
        reset_ai_session(assistant_id, user_id=user_id)
        assistant_reply = _process_openai_request(text, assistant_id, user_id=user_id, file_id=file_id)

        logger.info("✅ Ответ ассистента получен успешно")
        logger.debug(f"Ответ: {assistant_reply}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "data": assistant_reply}), 200

    except Exception as e:
        logger.exception(f"❌ Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обращении к ИИ: error {e}" }), 500


# Маршрут для предварительной очистки текста испльзую в new_report_creation (можно также использовать в analyze_dinamics если разбить ее на части)
@openai_api_bp.route("/clean_raw_text", methods=['POST'])
@auth_required()
def clean_raw_text_route():
    logger.info("(Маршрут clean_raw_text_route) --------------------------------------")
    logger.info(f"(Маршрут clean_raw_text_route) 🚀 Начата очистка текста с помощью OpenAI API.")
    data = request.get_json()
    raw_text = data.get("raw_text", "")
    if not raw_text.strip():
        logger.error(f"(Маршрут clean_raw_text_route) ❌ Не передан текст для очистки")
        return jsonify({"status": "error", "message": "Не передан текст"}), 400
    try:
        cleaned = clean_raw_text(raw_text, user_id=current_user.id)
        logger.info(f"(Маршрут clean_raw_text_route) ✅ Очистка текста успешна")
        logger.info(f"(Маршрут clean_raw_text_route) ------------------------------------------")
        return jsonify({"status": "success", "message": "Текст успешно очищен", "data": cleaned}), 200
    except Exception as e:
        logger.error(f"(Маршрут clean_raw_text_route) ❌ Ошибка при очистке текста: {str(e)}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "error", "message": str(e)}), 500



@openai_api_bp.route("/ocr_extract_text", methods=["POST"])
@auth_required()
def ocr_extract_text():
    logger.info(f"(Извлечение текста из загруженного файла) ------------------------------------")
    logger.info(f"(Извлечение текста из загруженного файла) 🚀 Начинаю обработку запроса на извлечение текста из загруженного файла")
    try:
        file = request.files.get("file")
        if not file:
            logger.error(f"(Извлечение текста из загруженного файла) ❌ Не получен файл для обработки")
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
        from file_processing import extract_text_from_uploaded_file
        text, error = extract_text_from_uploaded_file(file)
        if error:
            # Если pdf — отдать код 200, но сообщить что не поддерживается
            if "PDF files are not supported" in error:
                logger.info(f"(Извлечение текста из загруженного файла) 📄 PDF файл не поддерживается")
                return jsonify({"status": "success", "text": "", "message": error}), 200
            logger.error(f"(Извлечение текста из загруженного файла) ❌ Ошибка при извлечении текста: {error}")
            return jsonify({"status": "error", "message": error}), 400
        logger.info(f"(Извлечение текста из загруженного файла) ✅ Текст успешно извлечен")
        return jsonify({"status": "success", "text": text}), 200
    except Exception as e:
        logger.error(f"(Извлечение текста из загруженного файла) ❌ Ошибка при обработке файла: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
    
    