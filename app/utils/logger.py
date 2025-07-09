# logger.py

import logging
import os

# Получаем уровень логирования из .env (по умолчанию INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
logger = logging.getLogger("app_logger")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Формат сообщений
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

# Логирование в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Логирование в файл, если включено
if LOG_TO_FILE:
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logger.info(f"Логирование настроено. Уровень: {LOG_LEVEL}, Логи в файл: {LOG_TO_FILE}")