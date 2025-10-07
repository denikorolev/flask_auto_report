# ..utils/ai_processing.py

from flask import current_app
from openai import OpenAI
import tiktoken
import time
import json as pyjson
import re
from flask_security import current_user
from app.utils.logger import logger
from app.utils.redis_client import redis_get, redis_set, redis_delete
from app.utils.sentence_processing import convert_template_json_to_text




# Функция для подсчета токенов в тексте
def count_tokens(text: str, model: str) -> int:
    """
    Counts the number of tokens in the input text for the given OpenAI model.
    
    :param text: The input string.
    :param model: The OpenAI model to use for tokenization ("gpt-4", "gpt-3.5-turbo", etc).
    :return: Number of tokens.
    """
    from tasks.extensions import celery
    
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
    logger.info(f"(функция _process_openai_request) 🚀 Processing OpenAI request started.")

    thread_key = f"user:{user_id}:assistant:{assistant_id}:thread"
    
    api_key = current_app.config.get("OPENAI_API_KEY", None)
    if not api_key:
        logger.warning(f"(функция _process_openai_request) ⚠️ OpenAI API key not found in Flask config, trying to get it from Celery config.")
        from tasks.extensions import celery
        api_key = celery.conf.get("OPENAI_API_KEY", None)
        if not api_key:
            logger.error(f"(функция _process_openai_request) OpenAI API key is not configured.")
            raise ValueError("OpenAI API key is not configured.")
    client = OpenAI(api_key=api_key)

    thread_id = redis_get(thread_key) 
    logger.info(f"(функция _process_openai_request) Retrieved thread ID from Redis: {thread_id}")

    if not thread_id:
        logger.info(f"(функция _process_openai_request) No thread ID found, creating a new thread.")
        thread = client.beta.threads.create()
        thread_id = thread.id
        redis_set(thread_key, thread_id, ex=3600)  # Store thread ID in Redis for 1 hour
    else:
        logger.info(f"(функция _process_openai_request) Using existing thread ID: {thread_id}")
        thread = client.beta.threads.retrieve(thread_id)
        
        

    attachments = [{"file_id": file_id, "tools": [{"type": "file_search"}]}] if file_id else None

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text,
        attachments=attachments
    )
    
    if not message:
        logger.error(f"(функция _process_openai_request) Failed to create message in OpenAI thread.")
        
    
    run_args = {
        "thread_id": thread_id,
        "assistant_id": assistant_id,
    }
    
    run = client.beta.threads.runs.create(**run_args)

    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        time.sleep(1.5)
        
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc",
    )

    assistant_reply = ""
    assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]

    if assistant_messages:
        last = assistant_messages[-1]
        for content_block in last.content:
            logger.debug(f"(функция _process_openai_request) Content block: {content_block}")
            if hasattr(content_block, "text"):
                assistant_reply += content_block.text.value
    if not assistant_reply:
        logger.warning(f"(функция _process_openai_request) No assistant reply found in the messages.")
        return "Ответ ассистента не получен."
    
    # Очистка ответа от цитаты загруженного файла     
    if clean_response:
        clean_reply = re.sub(r"【.*?】", "", assistant_reply)
        logger.debug(f"(функция _process_openai_request) Cleaned reply: {clean_reply}")
        return clean_reply
    else:
        logger.debug(f"(функция _process_openai_request) Raw reply: {assistant_reply}")
        return assistant_reply



# Функция для сброса сессии OpenAI
def reset_ai_session(assistant_id: str, user_id: int):
    """
    Clears thread and message tracking for the given assistant from Redis.
    """
    try:
        thread_key = f"user:{user_id}:assistant:{assistant_id}:thread"
        redis_delete(thread_key)
        logger.info(f"(функция reset_ai_session) ✅ Сессия OpenAI для assistant_id {assistant_id} и user_id {user_id} успешно сброшена.")
    except Exception as e:
        logger.error(f"(функция reset_ai_session) ❌ Ошибка при сбросе сессии OpenAI: {str(e)}")
        


# Функция для проверки грамматики текста с помощью OpenAI API
def gramma_correction_ai(text: str, language: str, assistant_id: str) -> str:
    logger.info("(функция gramma_correction_ai) --------------------------------------")
    logger.info("🚀 Начата попытка проверки текста с помощью OpenAI API.")

    try:
        # Получение assistant_id по modality
        if language != "ru":
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
def clean_raw_text(raw_text: str, user_id: int, assistant_id: str, max_attempts: int = 2) -> str:
    logger.info("(Функция clean_raw_text) --------------------------------------")
    logger.info("[clean_raw_text] 🚀 Начата очистка текста с помощью OpenAI API.")
    logger.info("---------------------------------------------------")
    
    for attempt in range(max_attempts):
        try:
            cleaned = _process_openai_request(
                text=raw_text,
                assistant_id=assistant_id,
                user_id=user_id,
                file_id=None,
                clean_response=False
            )
            if cleaned:
                logger.info(f"[clean_raw_text] ✅ Очистка текста успешна на попытке {attempt + 1}.")
                logger.debug(f"[clean_raw_text] Очищенный текст: {cleaned}")
                logger.info("---------------------------------------------------")
                return cleaned
        except Exception as e:
            logger.warning(f"[clean_raw_text] ❌ Попытка {attempt + 1} не удалась: {e}")
        finally:
            reset_ai_session(assistant_id, user_id=user_id)

    logger.warning("[clean_raw_text] ⚠️ Все попытки не удались, возвращаю исходный текст")
    logger.info("---------------------------------------------------")
    return raw_text






















































# Функция для запуска ассистента первого взгляда. Использую в analyze_dinamics в working_with_reports.py
def run_first_look_assistant(cleaned_text: str, template_text: list, user_id: int, assistant_id: str, max_attempts: int = 2) -> str:
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
                
    for attempt in range(max_attempts):
        try:
            result = _process_openai_request(
                text=prompt,
                assistant_id=assistant_id,
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
            reset_ai_session(assistant_id, user_id=user_id)

    logger.error("[run_first_look_assistant] ❌ Все попытки получения первого взгляда не удались")
    logger.info("---------------------------------------------------")
    raise ValueError("Все попытки получения первого взгляда не удались.")


# Окончательное структурирование протокола с помощью OpenAI API
def structure_report_text(template_text: list, report_text: str, user_id: int, assistant_id: str, max_attempts: int = 2) -> list:
    logger.info("(Функция structure_report_text) --------------------------------------")
    logger.info("[structure_report_text] 🚀 Начата попытка структурирования отчета с помощью OpenAI API.")
    logger.info("---------------------------------------------------")

    prompt = f"""REPORT TEMPLATE:
                {template_text}
                ORIGINAL MEDICAL REPORT TEXT:
                {report_text}
                """

    for attempt in range(max_attempts):
        try:
            result_text = _process_openai_request(
                text=prompt,
                assistant_id=assistant_id,
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
            reset_ai_session(assistant_id, user_id=user_id)

    logger.error("[structure_report_text] ❌ Все попытки структурирования отчета не удались")
    logger.info("---------------------------------------------------")
    raise ValueError("Все попытки структурирования отчета не удались.")


# Функция для генерации impression с помощью OpenAI.
def ai_impression_generation(assistant_id: str, user_id: int, report_text: str, file_id: str) -> str:
    logger.info("(Функция ai_impression_generation) --------------------------------------")
    logger.info("[ai_impression_generation] 🚀 Начата попытка генерации impression с помощью OpenAI API.")

    prompt = f"""
                MEDICAL REPORT TEXT:
                {report_text}
                """
    try:
        result = _process_openai_request(
            text=prompt,
            assistant_id=assistant_id,
            user_id=user_id,
            file_id=file_id,
            clean_response=False
        )
        if result:
            logger.info(f"[ai_impression_generation] ✅ Генерация impression успешна.")
            logger.info("---------------------------------------------------")
            return result
        else:
            logger.error("[ai_impression_generation] ❌ Ответ ассистента пуст.")
            raise ValueError("Ответ ассистента пуст.")
    except Exception as e:
        logger.error(f"[ai_impression_generation] ❌ Ошибка при обращении к ИИ: {e}")
        raise ValueError(f"Ошибка при обращении к ИИ: {e}")
    finally:
        reset_ai_session(assistant_id, user_id=user_id)


# Функция для запуска проверки протокола при помощи ассистента OPENAI_ASSISTANT_REDACTOR
def ai_report_check(assistant_id: str, user_id: int, report_text: str, today_date: str) -> str:
    logger.info("(Функция ai_report_check) --------------------------------------")
    logger.info("[ai_report_check] 🚀 Начата попытка проверки отчета с помощью OpenAI API.")

    prompt = f"""Today's date: 
                {today_date}
                MEDICAL REPORT TO CHECK:
                {report_text}
                """
    try:
        result = _process_openai_request(
            text=prompt,
            assistant_id=assistant_id,
            user_id=user_id,
            file_id=None,
            clean_response=False
        )
        if result:
            logger.info(f"[ai_report_check] ✅ Проверка отчета успешна. Ответ ассистента: {result}")
            logger.info("---------------------------------------------------")
            return result
        else:
            logger.error("[ai_report_check] ❌ Ответ ассистента пуст.")
            raise ValueError("Ответ ассистента пуст.")
    except Exception as e:
        logger.error(f"[ai_report_check] ❌ Ошибка при обращении к ИИ: {e}")
        raise ValueError(f"Ошибка при обращении к ИИ: {e}")
    finally:
        reset_ai_session(assistant_id, user_id=user_id)


# Функция для генерации шаблона отчета с помощью OpenAI. Использую в create_report_template в working_with_reports.py
def ai_template_generator(template_text: str, assistant_id: str, user_id: int) -> dict:
    """
    Generates a report template based on the provided template data.
    """
    logger.info("(Функция ai_template_generator) --------------------------------------")
    logger.info("[ai_template_generator] 🚀 Начата генерация шаблона отчета.")
    
    generated_template = _process_openai_request(
        text=template_text,
        assistant_id=assistant_id,
        user_id=user_id,
        file_id=None,
        clean_response=False
    )
    # распарсиваем ответ в JSON
    try:
        json_generated_template = pyjson.loads(generated_template)
        logger.info(f"[ai_template_generator] ✅ Шаблон успешно сгенерирован: {generated_template}")
        logger.info("---------------------------------------------------")
        return json_generated_template
    
    except pyjson.JSONDecodeError as e:
        logger.error(f"[ai_template_generator] ❌ Ошибка при распарсивании ответа ассистента: {e}")
        raise ValueError("Ответ ассистента не является корректным JSON. Не удалось распарсить.")
    finally:
        reset_ai_session(assistant_id, user_id=user_id)
    
    

    
    