# openai_api.py

from flask import request, jsonify, current_app, Blueprint, render_template, session, g
from openai import OpenAI
import tiktoken
import time
from flask_security.decorators import auth_required, roles_required
from logger import logger
from flask_security import current_user
from models import FileMetadata
import re

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
def _process_openai_request(text: str, assistant_id: str, file_id: str = None, clean_response: bool = True) -> str:
    """
    Internal helper that sends a user message to OpenAI Assistant and returns the assistant's reply.
    Thread and message state is automatically managed via Flask session.
    """
    logger.info(f"Processing OpenAI request for assistant ID: {assistant_id}")
    
    api_key = current_app.config.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    thread_id = session.get(assistant_id)
    message_key = f"{assistant_id}_last_msg"
    

    if thread_id:
        thread = client.beta.threads.retrieve(thread_id)
        logger.info(f"Thread ID: {thread_id}")
    else:
        logger.info("Creating new thread")
        thread = client.beta.threads.create()
        thread_id = thread.id
        session[assistant_id] = thread_id
        
    print(f"file_id: {file_id}")
    attachments = [{"file_id": file_id, "tools": [{"type": "file_search"}]}] if file_id else None

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text,
        attachments=attachments
    )
    
    run_args = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
    }
    
    run = client.beta.threads.runs.create(**run_args)

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        print(f"Run status: {run.status}")
        time.sleep(1)

    after_id = session.get(message_key) or message.id
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc",
        after=after_id
    )
    
    session[message_key] = message.id

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
def reset_ai_session(assistant_id: str):
    """
    Clears thread and message tracking for the given assistant from session.
    """
    session.pop(assistant_id, None)
    session.pop(f"{assistant_id}_last_msg", None)


def gramma_correction_ai(text):
    logger.info("(функция gramma_correction_ai) --------------------------------------")
    logger.info("🚀 Начата попытка проверки текста с помощью OpenAI API.")

    try:
        language = session.get("lang", "ru")
    
        # Получение assistant_id по modality
        if language == "ru":
            assistant_id = current_app.config.get("OPENAI_ASSISTANT_GRAMMA_CORRECTOR_RU")
        else:
            raise ValueError(f"Unsupported language: {language}")

        if not assistant_id:
            raise ValueError("Assistant ID is not configured.")

        # Обработка запроса
        reset_ai_session(assistant_id)
        assistant_reply = _process_openai_request(text, assistant_id)

        logger.info("(функция gramma_correction_ai) ✅ Ответ ассистента получен успешно")
        logger.debug(f"(функция gramma_correction_ai) Ответ: {assistant_reply}")
        logger.info("---------------------------------------------------")
        return assistant_reply

    except Exception as e:
        logger.exception(f"(функция gramma_correction_ai) ❌ Unexpected error: {str(e)}")
        raise ValueError(f"Ошибка при обращении к ИИ: error {e}")
  
  
  
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
        reset_ai_session(ai_assistant)
    message = _process_openai_request(text, ai_assistant)
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
        reset_ai_session(ai_assistant)
        message = _process_openai_request(text, ai_assistant)
        
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

    try:
        data = request.get_json()
        text = data.get("text")
        modality = data.get("modality")
        logger.debug(f"Получены данные: {data}")

        if not text:
            return jsonify({"status": "error", "message": "Your request is empty"}), 400
        if not modality:
            return jsonify({"status": "error", "message": "Modality is missing"}), 400

        file_id = session.get("impression_file_ids", {}).get(modality)
        if not file_id:
            logger.error({f"No impression file ID found in session for modality: {modality}"}), 400
    
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
        reset_ai_session(assistant_id)
        assistant_reply = _process_openai_request(text, assistant_id, file_id)

        logger.info("✅ Ответ ассистента получен успешно")
        logger.debug(f"Ответ: {assistant_reply}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "data": assistant_reply}), 200

    except Exception as e:
        logger.exception(f"❌ Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обращении к ИИ: error {e}" }), 500





    
    