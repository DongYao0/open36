FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

EXPOSE 8003

# 阶段7：gthread 模型 4 worker × 4 thread（=16 并发，与 PG 连接预算对齐）；
# 参数全部可由环境变量覆盖；开发环境 manage.py runserver 不受影响。
# max-requests + jitter 让 worker 定期重生，缓解长跑内存缓慢增长。
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8003 --worker-class gthread --workers ${FORUM_WORKERS:-4} --threads ${FORUM_THREADS:-4} --timeout ${FORUM_TIMEOUT:-30} --graceful-timeout 30 --keep-alive 5 --max-requests ${FORUM_MAX_REQUESTS:-2000} --max-requests-jitter 200 --access-logfile - config.wsgi:application"]
