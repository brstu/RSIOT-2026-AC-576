"""Сервис тревог «СмартДом» — эталон лабораторной работы 2 (вариант 0).

Принимает запросы на создание тревоги (Alert) от сервиса devices.
POST /alerts — операция НЕидемпотентная по природе: каждый вызов создаёт
новую тревогу. Именно поэтому повтор запроса без ключа идемпотентности
плодит дубли — это и демонстрирует лаба.

Что здесь показано:
  * хранение «Idempotency-Key → сохранённый ответ»: повтор с тем же ключом
    возвращает ПЕРВЫЙ ответ и не создаёт вторую тревогу (семантика Stripe);
  * имитация «потерянного ответа»: если запрос помечен заголовком
    X-Debug-Lose-Response, тревога создаётся, но ответ задерживается дольше
    клиентского таймаута — клиент уходит в ретрай (третий исход «неизвестно»
    из лекции 03);
  * окно отказа POST /outage?seconds=N: пока окно активно, POST /alerts
    отвечает 503 ДО создания тревоги — безопасный для ретрая отказ; нужно
    для эксперимента retry storm.

Хранилище — память процесса (для лабы достаточно; в реальной системе ключи
живут в Redis с SET NX + TTL — см. методические материалы).
"""

import asyncio
import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("alerts")

# Задержка «потерянного ответа»: должна быть БОЛЬШЕ read-таймаута клиента
# devices (0.8 с), иначе обрыв не воспроизведётся.
LOST_RESPONSE_DELAY = float(os.getenv("LOST_RESPONSE_DELAY", "2.0"))

app = FastAPI(title="SmartHome Alerts (вариант 0)")

# Состояние процесса. Один uvicorn-воркер + asyncio => операции над dict/list
# между await атомарны. В коде ниже проверка ключа, создание тревоги и запись
# ключа идут БЕЗ await между ними — это и есть «атомарно с эффектом».
alerts: list[dict] = []
idem_store: dict[str, dict] = {}  # Idempotency-Key -> сохранённое тело ответа
outage_until: float = 0.0


class AlertIn(BaseModel):
    """Запрос на создание тревоги (сущность Alert из словаря «СмартДома»)."""

    device_id: str = Field(min_length=1, examples=["dev-7"])
    sensor: str = Field(min_length=1, examples=["temperature"])
    value: float = Field(examples=[72.5])
    reason: str = Field(min_length=1, examples=["value 72.5 > threshold 60.0"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/outage")
async def start_outage(seconds: float = 3.0):
    """Включить окно отказа: POST /alerts будет отвечать 503 указанное время.

    Нужно для эксперимента retry storm (см. app/retry_storm.py в devices).
    """
    global outage_until
    outage_until = time.monotonic() + seconds
    log.info("outage window: %.1f s", seconds)
    return {"outage_seconds": seconds}


@app.post("/alerts", status_code=201)
async def create_alert(alert: AlertIn, request: Request, response: Response):
    """Создать тревогу. Повтор с тем же Idempotency-Key дубль НЕ создаёт."""
    # 1. Окно отказа: отказываем ДО каких-либо эффектов. 503 = «повторяй
    #    с умом» — ретрай такого отказа безопасен даже без ключа.
    if time.monotonic() < outage_until:
        raise HTTPException(status_code=503, detail="temporary outage (drill)")

    key = request.headers.get("Idempotency-Key")

    # 2. Ключ уже видели: возвращаем СОХРАНЁННЫЙ ответ, эффекта нет.
    if key is not None and key in idem_store:
        log.info("replay by Idempotency-Key=%s — дубль не создан", key)
        return JSONResponse(
            status_code=201,
            content=idem_store[key],
            headers={"Idempotency-Replayed": "true"},
        )

    # 3. Эффект + запись ключа: между этими строками нет await,
    #    поэтому для одного процесса пара «эффект + ключ» атомарна.
    item = {
        "id": f"al-{uuid.uuid4().hex[:8]}",
        "device_id": alert.device_id,
        "sensor": alert.sensor,
        "value": alert.value,
        "reason": alert.reason,
        "created_at": time.time(),
    }
    alerts.append(item)
    body = {"alert": item}
    if key is not None:
        idem_store[key] = body
    log.info(
        "alert created: id=%s device=%s key=%s total=%d",
        item["id"], alert.device_id, key, len(alerts),
    )

    # 4. Имитация потерянного ответа: тревога УЖЕ создана, но ответ
    #    задерживается дольше клиентского таймаута. Клиент решит, что вызов
    #    не удался, и повторит — хотя эффект уже случился.
    if request.headers.get("X-Debug-Lose-Response") == "1":
        log.info("simulate lost response: держим ответ %.1f s", LOST_RESPONSE_DELAY)
        await asyncio.sleep(LOST_RESPONSE_DELAY)

    response.headers["Idempotency-Replayed"] = "false"
    return body


@app.get("/alerts")
async def list_alerts():
    """Список тревог — здесь видно дубли (или их отсутствие)."""
    return {"count": len(alerts), "alerts": alerts}


@app.delete("/alerts", status_code=204)
async def clear_alerts():
    """Очистить журнал тревог (для повторных прогонов демонстраций)."""
    alerts.clear()
    idem_store.clear()
    log.info("alerts cleared")
