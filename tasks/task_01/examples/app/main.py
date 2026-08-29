"""Сервис телеметрии «СмартДом» — эталон лабораторной работы 1 (вариант 0).

Принимает показания датчиков (Reading) и отдаёт историю по устройству
(Device). Хранение — Redis (список показаний на устройство). Конфигурация —
только через переменные окружения (двенадцатифакторный подход):

  REDIS_URL   — адрес Redis (по умолчанию redis://localhost:6379/0)
  KEY_PREFIX  — префикс ключей stu:<StudentID>:v<вариант>
  STU_ID, STU_GROUP, STU_VARIANT — метаданные студента, логируются при старте

Ключевые приёмы лабы, которые здесь показаны:
  * сервис НЕ падает при недоступном Redis — health отвечает 503 (частичный
    отказ вместо полного, лекция 01);
  * graceful shutdown: lifespan-хук закрывает соединение и пишет лог
    (uvicorn корректно обрабатывает SIGTERM от docker stop);
  * состояние — снаружи (Redis + volume), не в writable-слое контейнера.
"""

import json
import logging
import os
import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("telemetry")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KEY_PREFIX = os.getenv("KEY_PREFIX", "stu:00000:v0")
STU_ID = os.getenv("STU_ID", "00000")
STU_GROUP = os.getenv("STU_GROUP", "AS-576")
STU_VARIANT = os.getenv("STU_VARIANT", "0")

HISTORY_LIMIT = 100  # храним последние N показаний на устройство


class ReadingIn(BaseModel):
    """Показание датчика (сущность Reading из словаря «СмартДома»)."""

    device_id: str = Field(min_length=1, examples=["dev-42"])
    sensor: str = Field(min_length=1, examples=["temperature"])
    value: float = Field(examples=[21.5])
    ts: float | None = Field(default=None, description="Unix-время; если не задано — момент приёма")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт: логируем метаданные студента (требование лабы) и конфигурацию.
    log.info(
        "start: STU_ID=%s STU_GROUP=%s STU_VARIANT=%s redis=%s prefix=%s",
        STU_ID, STU_GROUP, STU_VARIANT, REDIS_URL, KEY_PREFIX,
    )
    # Подключение ленивое: если Redis ещё не готов, сервис всё равно стартует,
    # а health будет отвечать 503, пока зависимость не поднимется.
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    # Graceful shutdown: сюда мы попадаем по SIGTERM (docker compose stop).
    await app.state.redis.aclose()
    log.info("graceful shutdown: соединение с Redis закрыто, сервис завершён")


app = FastAPI(title="SmartHome Telemetry (вариант 0)", lifespan=lifespan)


def _key(device_id: str) -> str:
    return f"{KEY_PREFIX}:readings:{device_id}"


@app.get("/health")
async def health():
    """Health-эндпоинт для HEALTHCHECK: проверяет доступность Redis."""
    try:
        await app.state.redis.ping()
    except Exception:  # noqa: BLE001 — любой сбой зависимости = not ready
        raise HTTPException(status_code=503, detail="redis unavailable")
    return {"status": "ok"}


@app.post("/readings", status_code=201)
async def add_reading(reading: ReadingIn):
    """Принять показание и положить его в историю устройства."""
    item = reading.model_dump()
    if item["ts"] is None:
        item["ts"] = time.time()
    try:
        r = app.state.redis
        await r.lpush(_key(reading.device_id), json.dumps(item))
        await r.ltrim(_key(reading.device_id), 0, HISTORY_LIMIT - 1)
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        # Redis недоступен: честный 503, но процесс жив — Docker не должен
        # перезапускать сервис из-за чужого отказа.
        raise HTTPException(status_code=503, detail="storage unavailable, retry later")
    log.info("reading accepted: device=%s sensor=%s value=%s", reading.device_id, reading.sensor, reading.value)
    return {"accepted": True, "reading": item}


@app.get("/devices/{device_id}/readings")
async def get_readings(device_id: str, limit: int = 20):
    """История показаний устройства (свежие первыми)."""
    limit = max(1, min(limit, HISTORY_LIMIT))
    try:
        raw = await app.state.redis.lrange(_key(device_id), 0, limit - 1)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="storage unavailable, retry later")
    return {"device_id": device_id, "count": len(raw), "readings": [json.loads(x) for x in raw]}
