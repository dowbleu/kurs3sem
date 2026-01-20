FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc || (sleep 5 && apt-get update && apt-get install -y gcc) && \
    rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Ожидание готовности базы данных и выполнение миграций
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    python manage.py runserver 0.0.0.0:8000

