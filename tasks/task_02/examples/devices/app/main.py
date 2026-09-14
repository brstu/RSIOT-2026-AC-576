"""Сервис приёма показаний «СмартДом» — эталон лабораторной работы 2 (вариант 0).

Принимает показания датчиков (Reading). Если значение выше порога —
вызывает сервис alerts (`POST /alerts`) через клиент с таймаутами и
ретраями (app/client.py). Межсервисный вызов — сердце лабы.

Флаги поведения (переменные окружения, см. compose.yaml):
  IDEMPOTENCY=off|on         — слать ли Idempotency-Key (out of the box: off,
                               поэтому пример «сломан из коробки» — дубли!)
  RETRY_JITTER=on|off        — джиттер в паузах между ретраями
  SIMULATE_LOST_RESPONSE=on|off — метить первую попытку как «потерянный
                               ответ», чтобы обрыв воспроизводился всегда
  ALERT_THRESHOLD            — порог тревоги (по умолчанию 60.0)
  CLIENT_READ_TIMEOUT, MAX_ATTEMPTS, BACKOFF_BASE, BACKOFF_CAP — параметры
                               клиента (лекция 03: таймаут по p99, потолок
                               попыток, экспоненциальный backoff)
"""

import logging
import os
import time

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.client import new_idempotency_key, post_with_retries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("devices")

ALERTS_URL = os.getenv("ALERTS_URL", "http://localhost:8081")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "60.0"))
IDEMPOTENCY = os.getenv("IDEMPOTENCY", "off").lower() == "on"
RETRY_JITTER = os.getenv("RETRY_JITTER", "on").lower() == "on"
SIMULATE_LOST_RESPONSE = os.getenv("SIMULATE_LOST_RESPONSE", "on").lower() == "on"
CLIENT_READ_TIMEOUT = float(os.getenv("CLIENT_READ_TIMEOUT", "0.8"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "4"))
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", "0.2"))
BACKOFF_CAP = float(os.getenv("BACKOFF_CAP", "2.0"))

STU_ID = os.getenv("STU_ID", "00000")
STU_VARIANT = os.getenv("STU_VARIANT", "0")

app = FastAPI(title="SmartHome Devices (вариант 0)")

readings: list[dict] = []  # история показаний (память процесса — фокус лабы не тут)

log.info(
    "start: STU_ID=%s STU_VARIANT=%s alerts=%s idempotency=%s jitter=%s",
    STU_ID, STU_VARIANT, ALERTS_URL,
    "on" if IDEMPOTENCY else "off", "on" if RETRY_JITTER else "off",
)


class ReadingIn(BaseModel):
    """Показание датчика (сущность Reading из словаря «СмартДома»)."""

    device_id: str = Field(min_length=1, examples=["dev-7"])
    sensor: str = Field(min_length=1, examples=["temperature"])
    value: float = Field(examples=[72.5])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/readings", status_code=201)
async def add_reading(reading: ReadingIn):
    """Принять показание; при превышении порога — создать тревогу в alerts."""
    item = reading.model_dump()
    item["ts"] = time.time()
    readings.append(item)

    if reading.value <= ALERT_THRESHOLD:
        return {"accepted": True, "alert": None}

    # Межсервисный вызов. Ключ идемпотентности — ДО первой попытки,
    # один на всю операцию (если включён флаг IDEMPOTENCY).
    key = new_idempotency_key() if IDEMPOTENCY else None
    result = await post_with_retries(
        f"{ALERTS_URL}/alerts",
        {
            "device_id": reading.device_id,
            "sensor": reading.sensor,
            "value": reading.value,
            "reason": f"value {reading.value} > threshold {ALERT_THRESHOLD}",
        },
        read_timeout=CLIENT_READ_TIMEOUT,
        max_attempts=MAX_ATTEMPTS,
        backoff_base=BACKOFF_BASE,
        backoff_cap=BACKOFF_CAP,
        jitter=RETRY_JITTER,
        idempotency_key=key,
        mark_first_attempt_lost=SIMULATE_LOST_RESPONSE,
    )
    log.info(
        "alert call: ok=%s attempts=%d key=%s", result.ok, result.attempts, key,
    )
    return {
        "accepted": True,
        "alert": {
            "sent": result.ok,
            "attempts": result.attempts,
            "idempotency_key": key,
            "attempt_log": result.attempt_log,
        },
    }


@app.get("/readings")
async def list_readings():
    return {"count": len(readings), "readings": readings[-20:]}
