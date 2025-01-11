# openai_api.py

from flask import request, jsonify, current_app, Blueprint, render_template
from flask_login import login_required
from openai import OpenAI
from errors_processing import print_object_structure
import time
from flask_security.decorators import auth_required, roles_required

openai_api_bp = Blueprint("openai_api", __name__)

@openai_api_bp.before_request
@roles_required("superadmin")  
def restrict_to_superadmin():
    pass



@openai_api_bp.route("/start_openai_api", methods=["POST", "GET"])
@auth_required()
def start_openai_api():
    # menu = current_app.config["MENU"]
    return render_template(
        "openai_api.html",
        title="GPT",
        # menu=menu
    )


@openai_api_bp.route("/generate_impression", methods=['POST'])
@auth_required()
def generate_impression():
    try:
        data = request.get_json()
        text = data.get("text")
        print(data)
        # Подготовка промпта для GPT
        if not text:
            print("problem with request json")
            return jsonify({"status": "error", "message": "Your request is empty"}), 500
        system_prompt = ""

        # Установка API ключа и модели
        api_key = current_app.config.get('OPENAI_API_KEY')
        # api_model = current_app.config.get('OPENAI_MODEL')
        # organization = current_app.config.get("OPENAI_ORGANIZATION")
        # project = current_app.config.get("OPENAI_PROJECT")
        api_assistant = current_app.config.get("OPENAI_ASSISTANT") 

        if not api_key:
            print("OpenAI API key is not configured")
            return jsonify({"status": "error", "message": "OpenAI API key is not configured."}), 500
        if not api_assistant:
            print("Assistant ID is not configured.")
            return jsonify({"status": "error", "message": "Assistant ID is not configured."}), 500
        
        # Функция для ожидания ответа от ассистента
        def wait_on_run(run, thread):
            while run.status == "queued" or run.status == "in_progress":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
                time.sleep(0.5)
            return run
        
        
        client = OpenAI(api_key=api_key)
        thread = client.beta.threads.create()
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=text
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=api_assistant
        )
        
        wait_on_run(run, thread)
        
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            order="asc",
            after=message.id)
        
        # Извлечение ответа ассистента
        assistant_message = messages.data[0]  # Получаем первое сообщение от ассистента

        # Проверяем, что это сообщение от ассистента
        if assistant_message.role == 'assistant':
            # Контент может состоять из нескольких блоков, объединяем их
            assistant_reply = ''
            for content_block in assistant_message.content:
                if hasattr(content_block, 'text'):
                    assistant_reply += content_block.text.value
        else:
            assistant_reply = "No assistant message found."
        
        return jsonify({"status": "success", "data": f"{assistant_reply}"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {e}"}), 500
   


    
    