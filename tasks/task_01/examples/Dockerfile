# syntax=docker/dockerfile:1
# Эталонный Dockerfile лабы 1: multi-stage, кэш слоёв, non-root, HEALTHCHECK.

# ---------- Стадия 1: «цех» — собираем зависимости ----------
FROM python:3.12-alpine AS builder
WORKDIR /app

# Сначала ТОЛЬКО файл зависимостей: пока requirements.txt не меняется,
# этот слой (и pip install) берётся из кэша при любых правках кода.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Стадия 2: «витрина» — только рантайм ----------
FROM python:3.12-alpine

# Метаданные студента (требование лабы). В своей работе замените значения.
LABEL org.bstu.student.fullname="Пример Преподавателя" \
      org.bstu.student.id="00000" \
      org.bstu.group="AS-576" \
      org.bstu.variant="0" \
      org.bstu.course="RSIOT"

WORKDIR /app

# Зависимости из «цеха»; компиляторов и pip-кэша в витрине нет.
COPY --from=builder /install /usr/local
# Код копируем последним — он меняется чаще всего.
COPY app/ ./app/

# Непривилегированный ЧИСЛОВОЙ UID: оркестраторы (лаба 2) умеют проверять
# runAsNonRoot только по числу, имя пользователя им ни о чём не говорит.
USER 10001:10001

# EXPOSE — документация; наружу порт публикует compose (ports:).
EXPOSE 8080

# Exec-форма и без curl: в slim/alpine-образах curl нет, а тащить его ради
# healthcheck — лишние мегабайты и поверхность атаки.
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2).status==200 else 1)"]

# Exec-форма CMD: PID 1 = python, SIGTERM доходит до процесса напрямую.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
