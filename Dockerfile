# Dockerfile
# Используем официальный образ Python 3.11-slim в качестве базового образа
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Если когда-нибудь потребуется poppler для PDF:
# RUN apt-get update && apt-get install -y poppler-utils
RUN apt-get update && apt-get install -y ca-certificates

# Копируем файл зависимостей
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install https://github.com/explosion/spacy-models/releases/download/ru_core_news_sm-3.5.0/ru_core_news_sm-3.5.0.tar.gz

# Копируем остальные файлы приложения
COPY . .

# Указываем команду запуска Flask-приложения
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]



