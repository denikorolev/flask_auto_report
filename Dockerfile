# Dockerfile
# Используем официальный образ Python 3.9
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install https://github.com/explosion/spacy-models/releases/download/ru_core_news_sm-3.5.0/ru_core_news_sm-3.5.0.tar.gz
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.5.0/en_core_web_sm-3.5.0.tar.gz

# Копируем остальные файлы приложения
COPY . .

# Указываем команду запуска Flask-приложения
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
