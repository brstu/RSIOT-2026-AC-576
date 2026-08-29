# syntax=docker/dockerfile:1
# Сервис devices (лаба 3). Приёмы Dockerfile — из лабы 1: multi-stage,
# кэш слоёв (requirements до кода), non-root, HEALTHCHECK exec-формой.

FROM python:3.12-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine
LABEL org.bstu.course="RSIOT" org.bstu.lab="task_03" org.bstu.variant="0"
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2).status==200 else 1)"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
