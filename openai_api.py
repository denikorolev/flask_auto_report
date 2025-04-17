# openai_api.py

from flask import request, jsonify, current_app, Blueprint, render_template, session
from openai import OpenAI
import tiktoken
import time
from flask_security.decorators import auth_required, roles_required
from logger import logger
from flask_security import current_user

openai_api_bp = Blueprint("openai_api", __name__)

# Запрещалка для доступа к API OpenAI
@openai_api_bp.before_request
@roles_required("superadmin")  
def restrict_to_superadmin():
    pass

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
def _process_openai_request(text: str, assistant_id: str) -> str:
    """
    Internal helper that sends a user message to OpenAI Assistant and returns the assistant's reply.
    Thread and message state is automatically managed via Flask session.
    """
    print(f"Start openaiapi function. Assistant ID: {assistant_id}")
    
    api_key = current_app.config.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    thread_id = session.get(assistant_id)
    message_key = f"{assistant_id}_last_msg"

    if thread_id:
        thread = client.beta.threads.retrieve(thread_id)
        print(f"Thread ID: {thread_id}")
    else:
        print("Creating new thread")
        thread = client.beta.threads.create()
        thread_id = thread.id
        session[assistant_id] = thread_id

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

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
    
    print(messages.data)

    session[message_key] = message.id

    assistant_reply = ""
    assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
    print(f"Assistant messages: {assistant_messages}")

    if assistant_messages:
        last = assistant_messages[-1]
        for content_block in last.content:
            print(f"Content block: {content_block}")
            if hasattr(content_block, "text"):
                assistant_reply += content_block.text.value

    return assistant_reply or "Ответ ассистента не получен."



# Функция для сброса сессии OpenAI
def reset_ai_session(assistant_id: str):
    """
    Clears thread and message tracking for the given assistant from session.
    """
    session.pop(assistant_id, None)
    session.pop(f"{assistant_id}_last_msg", None)


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
    if tokens > 1000:
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
        assistant_reply = _process_openai_request(text, assistant_id)

        logger.info("✅ Ответ ассистента получен успешно")
        logger.debug(f"Ответ: {assistant_reply}")
        logger.info("---------------------------------------------------")
        return jsonify({"status": "success", "data": assistant_reply}), 200

    except Exception as e:
        logger.exception(f"❌ Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при обращении к ИИ"}), 500


    
    