"""Сервис приёма показаний «СмартДом» — эталон лабы 3 (вариант 0).

Продолжение стенда лабы 2 (devices → alerts). Новое в лабе 3 (лекция 09):

  * circuit breaker вокруг вызова alerts (app/breaker.py) — при лежащей
    зависимости отказываем мгновенно вместо каскада таймаутов;
  * fallback: недоставленная тревога уходит в локальную очередь
    (app/fallback.py), жилец получает 202, а не 500;
  * догон (drain_loop): после восстановления alerts очередь доставляется,
    Idempotency-Key из лабы 2 защищает догон от дублей;
  * backpressure: не больше MAX_CONCURRENT одновременных обработок тревог;
    сверх лимита — честный 503 + Retry-After (без бесконечной очереди).

Флаги поведения (переменные окружения, см. compose.yaml):
  BREAKER=off|on             — из коробки off: стенд «сломан», заморозьте
                               alerts и смотрите каскад таймаутов
  FAIL_THRESHOLD/WINDOW_SIZE/RECOVERY_TIMEOUT/HALF_OPEN_MAX — параметры breaker
  MAX_CONCURRENT/RETRY_AFTER — лимит одновременности и подсказка клиенту
  DRAIN_INTERVAL             — период фонового догона очереди, секунд
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import fallback
from app.breaker import CircuitBreaker
from app.client import CallResult, new_idempotency_key, post_with_retries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("devices")

ALERTS_URL = os.getenv("ALERTS_URL", "http://localhost:8081")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "60.0"))
BREAKER = os.getenv("BREAKER", "off").lower() == "on"
FAIL_THRESHOLD = int(os.getenv("FAIL_THRESHOLD", "3"))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "10"))
RECOVERY_TIMEOUT = float(os.getenv("RECOVERY_TIMEOUT", "8.0"))
HALF_OPEN_MAX = int(os.getenv("HALF_OPEN_MAX", "1"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "4"))
RETRY_AFTER = int(os.getenv("RETRY_AFTER", "5"))
DRAIN_INTERVAL = float(os.getenv("DRAIN_INTERVAL", "2.0"))
CLIENT_READ_TIMEOUT = float(os.getenv("CLIENT_READ_TIMEOUT", "0.8"))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "2"))
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", "0.2"))
BACKOFF_CAP = float(os.getenv("BACKOFF_CAP", "1.0"))

STU_ID = os.getenv("STU_ID", "00000")
STU_GROUP = os.getenv("STU_GROUP", "AS-576")
STU_VARIANT = os.getenv("STU_VARIANT", "0")

breaker = CircuitBreaker(
    fail_threshold=FAIL_THRESHOLD,
    window_size=WINDOW_SIZE,
    recovery_timeout=RECOVERY_TIMEOUT,
    half_open_max=HALF_OPEN_MAX,
)
alert_slots = asyncio.Semaphore(MAX_CONCURRENT)  # backpressure: лимит слотов
in_flight = 0                                    # сколько тревог в обработке
readings: list[dict] = []


async def call_alerts(payload: dict, key: str) -> CallResult:
    """Один вызов alerts (с короткими ретраями) + учёт исхода в breaker'е."""
    result = await post_with_retries(
        f"{ALERTS_URL}/alerts",
        payload,
        read_timeout=CLIENT_READ_TIMEOUT,
        max_attempts=MAX_ATTEMPTS,
        backoff_base=BACKOFF_BASE,
        backoff_cap=BACKOFF_CAP,
        idempotency_key=key,
    )
    if BREAKER:
        if result.ok:
            breaker.record_success()
        else:
            breaker.record_failure()
    return result


async def drain_loop() -> None:
    """Догон: фоновая доставка очереди fallback после восстановления alerts.

    Каждый тик пробует доставить голову очереди. При включённом breaker'е
    именно догон становится «пробником» HALF_OPEN: alerts ожил → проба
    удалась → breaker закрылся → очередь уезжает целиком.
    """
    while True:
        await asyncio.sleep(DRAIN_INTERVAL)
        delivered = 0
        while (entry := fallback.peek()) is not None:
            if BREAKER and not breaker.allow():
                break  # OPEN и «остывание» не вышло — ждём следующего тика
            result = await call_alerts(entry["payload"], entry["idempotency_key"])
            if not result.ok:
                break  # alerts ещё лежит; голову НЕ теряем
            fallback.pop_first()
            delivered += 1
        if delivered:
            log.info(
                "догон: доставлено %d, осталось в очереди %d",
                delivered, fallback.size(),
            )


@asynccontextmanager
async def lifespan(_: FastAPI):
    fallback.load_from_disk()
    task = asyncio.create_task(drain_loop())
    yield
    task.cancel()


app = FastAPI(title="SmartHome Devices (лаба 3, вариант 0)", lifespan=lifespan)

log.info(
    "start: STU_ID=%s STU_GROUP=%s STU_VARIANT=%s alerts=%s breaker=%s "
    "fail_threshold=%d window=%d recovery=%.1fs max_concurrent=%d",
    STU_ID, STU_GROUP, STU_VARIANT, ALERTS_URL,
    "on" if BREAKER else "off",
    FAIL_THRESHOLD, WINDOW_SIZE, RECOVERY_TIMEOUT, MAX_CONCURRENT,
)


class ReadingIn(BaseModel):
    """Показание датчика (сущность Reading из словаря «СмартДома»)."""

    device_id: str = Field(min_length=1, examples=["dev-7"])
    sensor: str = Field(min_length=1, examples=["temperature"])
    value: float = Field(examples=[72.5])


@app.get("/health")
async def health():
    """Живость + простые метрики: состояние breaker'а, очередь, слоты."""
    return {
        "status": "ok",
        "breaker": breaker.snapshot() if BREAKER else {"state": "disabled"},
        "fallback_queue": fallback.size(),
        "in_flight": in_flight,
        "max_concurrent": MAX_CONCURRENT,
    }


def _degraded_response(queued: int) -> JSONResponse:
    """202: тревога принята в локальную очередь, доставим после восстановления."""
    return JSONResponse(
        status_code=202,
        content={
            "accepted": True,
            "alert": {
                "delivered": False,
                "degraded": True,
                "queued": queued,
                "breaker": breaker.state if BREAKER else "disabled",
            },
        },
    )


@app.post("/readings", status_code=201)
async def add_reading(reading: ReadingIn):
    """Принять показание; при превышении порога — доставить тревогу.

    Порядок обороны (лекция 09): backpressure → breaker → вызов с
    таймаутами/ретраями → fallback-очередь. Пользователь никогда не
    получает 500 из-за лежащего alerts.
    """
    global in_flight
    item = reading.model_dump()
    item["ts"] = time.time()
    readings.append(item)

    if reading.value <= ALERT_THRESHOLD:
        return {"accepted": True, "alert": None}

    # 1. Backpressure: все слоты заняты → честный отказ, а не очередь навсегда.
    if alert_slots.locked():
        log.warning("backpressure: %d тревог уже в обработке — 503", in_flight)
        return JSONResponse(
            status_code=503,
            content={"detail": "too many alerts in flight, retry later"},
            headers={"Retry-After": str(RETRY_AFTER)},
        )

    async with alert_slots:
        in_flight += 1
        try:
            payload = {
                "device_id": reading.device_id,
                "sensor": reading.sensor,
                "value": reading.value,
                "reason": f"value {reading.value} > threshold {ALERT_THRESHOLD}",
            }
            key = new_idempotency_key()  # ДО первой попытки — переживёт догон

            # 2. Breaker: OPEN → мгновенный fallback, alerts не трогаем.
            if BREAKER and not breaker.allow():
                try:
                    return _degraded_response(fallback.enqueue(payload, key))
                except fallback.QueueFull:
                    return JSONResponse(
                        status_code=503,
                        content={"detail": "fallback queue full"},
                        headers={"Retry-After": str(RETRY_AFTER)},
                    )

            # 3. Обычный вызов с таймаутами и короткими ретраями (лаба 2).
            result = await call_alerts(payload, key)
            if result.ok:
                return {
                    "accepted": True,
                    "alert": {
                        "delivered": True,
                        "attempts": result.attempts,
                        "attempt_log": result.attempt_log,
                        "breaker": breaker.state if BREAKER else "disabled",
                    },
                }

            # 4. Вызов провалился → деградация вместо 500.
            log.warning("alerts недоступен (%s) — тревога в fallback", result.attempt_log)
            try:
                return _degraded_response(fallback.enqueue(payload, key))
            except fallback.QueueFull:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "fallback queue full"},
                    headers={"Retry-After": str(RETRY_AFTER)},
                )
        finally:
            in_flight -= 1


@app.get("/readings")
async def list_readings():
    return {"count": len(readings), "readings": readings[-20:]}
