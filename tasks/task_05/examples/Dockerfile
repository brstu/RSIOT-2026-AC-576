# SmartDom telemetry — multi-stage, non-root, финальный образ < 150 MB
FROM python:3.12-alpine AS build
WORKDIR /app
COPY src/requirements.txt .
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-alpine
LABEL org.bstu.course="RSIOT" \
      org.opencontainers.image.title="smartdom-telemetry" \
      org.opencontainers.image.description="SmartDom telemetry intake (lab 05 example)"
RUN adduser -D -u 10001 app
COPY --from=build /venv /venv
COPY src/app.py /app/app.py
USER app
WORKDIR /app
EXPOSE 8080
ENV PATH="/venv/bin:$PATH"
# uvicorn сам корректно обрабатывает SIGTERM (graceful shutdown);
# лог остановки пишет lifespan-хук приложения
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
