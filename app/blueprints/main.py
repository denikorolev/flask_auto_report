# app/blueprints/main.py

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from flask_security import logout_user
import os
from app.utils.logger import logger
# Мои модули
from app.utils.mail_helpers import send_email_via_zeptomail
from app.utils.logger import logger

main_bp = Blueprint("main", __name__)


# Маршрут для главной страницы
@main_bp.route("/", methods=['POST', 'GET'])
def index():
    return render_template("index.html", title="Главная страница")


@main_bp.route("/feedback_form", methods=["POST"])
def feedback_form():
    form_data = request.form
    logger.info(f"Feedback form submitted: {form_data}")
    to_email = "support@radiologary.com"
    subject = f"Письмо с формы обратной связи от {form_data.get('name', 'Unknown')}"
    html_content = f"{form_data.get('message', 'No message provided')}  от {form_data.get('email', 'Unknown Email')}."
    token = os.environ.get("ZEPTOMAIL_API_TOKEN")
    from_email = "feedbackform_sender@radiologary.com"
    if not token:
        logger.error("❌ Не указан ZEPTOMAIL_API_TOKEN")
        return render_template("errors/error.html", message="Не удалось отправить сообщение. Пожалуйста, попробуйте позже.")
    try:
        send_email_via_zeptomail(to_email, subject, html_content, token, from_email)
        logger.info(f"📧 Feedback form submitted successfully: {form_data}")
        return render_template("info/feedback_form.html", title="Feedback Form")
    except Exception as e:
        logger.error(f"⚠️ Ошибка при отправке письма: {e}")
        return render_template("errors/error.html", message="Не удалось отправить сообщение. Пожалуйста, попробуйте позже.")
    
    
    
@main_bp.route("/custom_logout", methods=["POST", "GET"])
def custom_logout():
    logger.info("inside logout route")
    session.clear()
    logger.info("session cleared")
    logout_user()
    logger.info("user logged out")
    return redirect(url_for("main.index"))



@main_bp.route("/success_registered", methods=["GET"])
def success_registered():
    return render_template("info/success_registered.html")


@main_bp.route("/health", methods=["GET"])
def health():
    # простая проверка: процесс жив, Flask отвечает
    return jsonify({"status": "ok"}), 200




