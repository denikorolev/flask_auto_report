# # mail_helpers.py

import requests
from flask import current_app
from app.utils.logger import logger
from flask_security.mail_util import MailUtil
from flask_security.forms import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired

def send_email_via_zeptomail(to_email, subject, html_content, token, from_email="noreply@radiologary.com"):
    """
    Отправляет электронное письмо через ZeptoMail API.
    :param to_email: Адрес электронной почты получателя
    :param subject: Тема письма
    :param html_content: HTML-содержимое письма
    :param token: Токен авторизации для ZeptoMail API
    :param from_email: Адрес электронной почты отправителя (по умолчанию "noreply@radiologary.com")
    """
    logger.info("📧 send_email_via_zeptomail вызван ----------------")
    url = "https://api.zeptomail.eu/v1.1/email"

    payload = {
        "from": {
            "address": from_email
        },
        "to": [
            {
                "email_address": {
                    "address": to_email
                }
            }
        ],
        "subject": subject,
        "htmlbody": html_content
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": token
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"📤 Email sent to {to_email}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return False


# CustomMailUtil - интеграция Flask-Security с ZeptoMail API
class CustomMailUtil(MailUtil):
    def send_mail(self, template, subject, recipient, sender, body, html, user, **kwargs):
        token = current_app.config.get("ZEPTOMAIL_API_TOKEN")
        from_email = current_app.config.get("NOREPLY_EMAIL", "noreply@example.com")
        if not token:
            logger.error("❌ Не указан ZEPTOMAIL_API_TOKEN")
            return False

        logger.info(f"📨 (CustomMailUtil) Отправка письма через ZeptoMail API: {subject} → {recipient}")
        return send_email_via_zeptomail(
            to_email=recipient,
            subject=subject,
            html_content=html,
            token=token,
            from_email=from_email
        )
        
class ExtendedRegisterForm(RegisterForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])