"""Сервис тревог «СмартДом» — эталон лабы 3 (вариант 0).

Почти тот же alerts, что в лабе 2: POST /alerts создаёт тревогу (Alert),
Idempotency-Key защищает от дублей — в лабе 3 это критично для ДОГОНА:
devices доставляет очередь fallback с теми же ключами, что были у «живых»
попыток, поэтому догон не плодит дубли.

Инструменты хаоса (для экспериментов лабы):
  * POST /outage?seconds=N — окно, в котором POST /alerts отвечает 503
    до каких-либо эффектов (error-rate сбой);
  * POST /slow?seconds=N&delay=D — окно, в котором каждый ответ
    задерживается на D секунд ПОСЛЕ создания тревоги (latency-сбой:
    «медленный» на клиенте неотличим от «мёртвого» — таймаут);
  * заморозку и остановку контейнера делает Docker снаружи:
    docker compose pause alerts / docker compose stop alerts.
"""

import asyncio
import logging
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

app = FastAPI(title="SmartHome Alerts (лаба 3, вариант 0)")

# Состояние процесса. Один uvicorn-воркер + asyncio => проверка ключа,
# создание тревоги и запись ключа идут БЕЗ await между ними — атомарно.
alerts: list[dict] = []
idem_store: dict[str, dict] = {}  # Idempotency-Key -> сохранённое тело ответа
outage_until: float = 0.0
slow_until: float = 0.0
slow_delay: float = 0.0


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
async def start_outage(seconds: float = 10.0):
    """Включить окно отказа: POST /alerts будет отвечать 503 указанное время."""
    global outage_until
    outage_until = time.monotonic() + seconds
    log.info("outage window: %.1f s", seconds)
    return {"outage_seconds": seconds}


@app.post("/slow")
async def start_slow(seconds: float = 20.0, delay: float = 2.0):
    """Включить окно медленных ответов: каждый ответ задерживается на delay с."""
    global slow_until, slow_delay
    slow_until = time.monotonic() + seconds
    slow_delay = delay
    log.info("slow window: %.1f s, delay %.1f s", seconds, delay)
    return {"slow_seconds": seconds, "delay": delay}


@app.post("/alerts", status_code=201)
async def create_alert(alert: AlertIn, request: Request, response: Response):
    """Создать тревогу. Повтор с тем же Idempotency-Key дубль НЕ создаёт."""
    # 1. Окно отказа: отказываем ДО каких-либо эффектов — ретрай безопасен.
    if time.monotonic() < outage_until:
        raise HTTPException(status_code=503, detail="temporary outage (drill)")

    key = request.headers.get("Idempotency-Key")

    # 2. Ключ уже видели: возвращаем СОХРАНЁННЫЙ ответ, эффекта нет.
    #    Именно так догон очереди fallback не создаёт дублей.
    if key is not None and key in idem_store:
        log.info("replay by Idempotency-Key=%s — дубль не создан", key)
        return JSONResponse(
            status_code=201,
            content=idem_store[key],
            headers={"Idempotency-Replayed": "true"},
        )

    # 3. Эффект + запись ключа: между этими строками нет await — атомарно.
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

    # 4. Окно медленных ответов: тревога УЖЕ создана, но ответ задерживается.
    #    Если delay больше read-таймаута клиента — для клиента это «мёртвый»
    #    сервис (таймаут), хотя эффект случился. Slow ≠ dead, но снаружи
    #    неотличимо — поэтому breaker обязан считать таймауты ошибками.
    if time.monotonic() < slow_until:
        log.info("slow window: держим ответ %.1f s", slow_delay)
        await asyncio.sleep(slow_delay)

    response.headers["Idempotency-Replayed"] = "false"
    return body


@app.get("/alerts")
async def list_alerts():
    """Список тревог — здесь видно доставку, догон и отсутствие дублей."""
    return {"count": len(alerts), "alerts": alerts}


@app.delete("/alerts", status_code=204)
async def clear_alerts():
    """Очистить журнал тревог (для повторных прогонов экспериментов)."""
    alerts.clear()
    idem_store.clear()
    log.info("alerts cleared")
