# Dockerfile
# Используем официальный образ Python 3.9
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt requirements.txt

# Генерируем requirements.txt
RUN pipreqs /app --force

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения
COPY . .

# Указываем команду запуска Flask-приложения
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
