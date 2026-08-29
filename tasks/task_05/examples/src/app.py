"""SmartDom telemetry intake — эталонный stateless-сервис для ЛР05.

Принимает показания датчиков (Reading) от Hub'ов «СмартДома».
Демонстрирует: health-пробы по «золотому правилу» (лекция 18),
graceful shutdown, конфигурацию из ENV (ConfigMap/Secret),
идемпотентный приём (лекции 1 и 3).
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("telemetry")

WARMUP_SECONDS = float(os.getenv("WARMUP_SECONDS", "5"))
ALERT_THRESHOLD_C = float(os.getenv("ALERT_THRESHOLD_C", "60"))
START_TS = time.monotonic()

# In-memory: сервис намеренно stateless — данные живут до рестарта пода.
# Настоящее хранилище — тема лекции 19 и ЛР06.
readings: list[dict] = []
seen_keys: set[str] = set()
alerts = 0


class Reading(BaseModel):
    device_id: str
    sensor: str
    value: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "starting: STU_ID=%s STU_GROUP=%s STU_VARIANT=%s",
        os.getenv("STU_ID", "?"), os.getenv("STU_GROUP", "?"), os.getenv("STU_VARIANT", "?"),
    )
    log.info("config: ALERT_THRESHOLD_C=%s, DB_PASSWORD=%s",
             ALERT_THRESHOLD_C, "***set***" if os.getenv("DB_PASSWORD") else "missing")
    yield
    log.info("SIGTERM received, graceful shutdown: %d readings accepted", len(readings))


app = FastAPI(title="SmartDom Telemetry", lifespan=lifespan)


@app.get("/health/live")
async def live() -> dict:
    """Liveness: только «процесс жив» — никаких внешних зависимостей."""
    return {"status": "alive"}


@app.get("/health/ready")
async def ready() -> dict:
    """Readiness: готовы ли делать полезную работу (здесь — прогрев)."""
    if time.monotonic() - START_TS < WARMUP_SECONDS:
        raise HTTPException(status_code=503, detail="warming up")
    return {"status": "ready"}


@app.post("/readings", status_code=201)
async def accept_reading(reading: Reading, idempotency_key: str | None = Header(default=None)) -> dict:
    global alerts
    if idempotency_key and idempotency_key in seen_keys:
        return {"accepted": False, "duplicate": True}
    if idempotency_key:
        seen_keys.add(idempotency_key)
    readings.append(reading.model_dump())
    alerted = reading.sensor == "temp" and reading.value > ALERT_THRESHOLD_C
    if alerted:
        alerts += 1
        log.warning("ALERT: %s on %s = %.1f > %.1f", reading.sensor, reading.device_id,
                    reading.value, ALERT_THRESHOLD_C)
    return {"accepted": True, "alert": alerted}


@app.get("/stats")
async def stats() -> dict:
    return {"readings": len(readings), "alerts": alerts,
            "pod": os.getenv("HOSTNAME", "local")}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
