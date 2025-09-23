#!/bin/bash

# Скрипт развертывания приложения

#  Устанавливаем флаг "exit on error"
set -e

#  Переменные
BACKUP_DIR="/home/deniskorolev/backups"
DB_CONTAINER_NAME="flask_auto_report-db-1"  # Имя контейнера базы данных PostgreSQL
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Загружаем переменные из .env
set -a
[ -f /home/deniskorolev/flask_auto_report/.env ] && . /home/deniskorolev/flask_auto_report/.env
set +a

# Проверяем и запускаем все контейнеры из docker-compose, если они не запущены

echo "=============================="
echo "Checking and starting required containers if needed..."
echo "=============================="

ALL_SERVICES=$(docker-compose config --services)

for service in $ALL_SERVICES; do
    # Получаем имя текущего контейнера для сервиса (если он уже создан)
    CONTAINER_NAME=$(docker-compose ps -q $service | xargs -r docker inspect --format '{{.Name}}' 2>/dev/null | sed 's|/||')
    if [ -z "$CONTAINER_NAME" ]; then
        echo "Service $service: no container found, starting..."
        docker-compose up -d $service
    else
        if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "Container $CONTAINER_NAME for service $service is not running. Starting..."
            docker-compose up -d $service
        else
            echo "Container $CONTAINER_NAME for service $service is already running."
        fi
    fi
done


#  Создаем резервную копию базы данных
echo "=============================="
echo "Creating a backup of the database..."
echo "=============================="

# Проверяем, существует ли каталог резервных копий, если нет - создаем его
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

# Делаем резервную копию базы данных, используя контейнер PostgreSQL
docker exec -t $DB_CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "Database backup completed successfully: $BACKUP_FILE"
else
    echo "Failed to create a database backup."
    exit 1
fi

#  Переходим в каталог приложения
cd /home/deniskorolev/flask_auto_report/

#  Обновляем код приложения
echo "=============================="
echo "Pulling the latest code from the repository..."
echo "=============================="
git diff-index --quiet HEAD -- || git stash -m "Auto-stash before deployment"
git pull origin main

#  Создаем и активируем виртуальное окружение
echo "=============================="
echo "Setting up virtual environment..."
echo "=============================="
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

#  Устанавливаем pip-tools для управления зависимостями, если он еще не установлен
echo "=============================="
echo "Installing pip-tools (if not already installed)..."
echo "=============================="
pip show pip-tools >/dev/null 2>&1 || pip install --no-cache-dir pip-tools

#  Компилируем зависимости и разрешаем конфликты с помощью pip-compile
echo "=============================="
echo "Compiling dependencies..."
echo "=============================="
pip-compile requirements.in --output-file requirements.txt

#  Устанавливаем все зависимости из скомпилированного requirements.txt
echo "=============================="
echo "Installing dependencies from compiled requirements.txt..."
echo "=============================="
pip install --no-cache-dir -r requirements.txt

#  Деактивируем виртуальное окружение
deactivate

#  Пересобираем и перезапускаем контейнеры
echo "=============================="
echo "Building and restarting Docker containers..."
echo "=============================="

echo "Останавливаю старые контейнеры..."
docker-compose down

echo "Очищаю docker-мусор..."
docker system prune -af

echo "Запускаю сборку и старт новых контейнеров..."
docker-compose up --build -d

#  Выполняем миграции базы данных (если необходимо)
echo "=============================="
echo "Applying database migrations..."
echo "=============================="
docker-compose exec web flask db upgrade

echo "=============================="
echo "Deployment completed successfully!"
echo "=============================="
