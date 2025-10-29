FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости включая Gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent

# Копируем весь проект
COPY . .

EXPOSE 5050

# Запуск через Gunicorn для продакшена
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "4", "--worker-class", "gevent", "run:app"]
