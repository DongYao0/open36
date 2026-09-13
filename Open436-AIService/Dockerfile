FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8008

# 阶段7：默认 2 个 worker（env 可覆盖）；全局流并发由 Redis 信号量限制，
# 不依赖单进程内存状态
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8008 --workers ${AI_WORKERS:-2}"]
