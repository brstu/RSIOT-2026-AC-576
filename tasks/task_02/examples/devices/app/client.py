"""HTTP-клиент devices → alerts: таймауты, ретраи с backoff и джиттером.

Три правила надёжного межсервисного вызова (лекция 03):

1. ТАЙМАУТ. Без него зависший вызов держит соединение вечно. Read-таймаут
   выбирается по p99 задержки вызываемого сервиса, не «с потолка».
2. РЕТРАИ — только на то, что имеет смысл повторять: сетевые ошибки,
   таймауты и 5xx. 4xx повторять бессмысленно: запрос сломан, чини запрос.
   Пауза — экспоненциальный backoff с FULL JITTER (AWS):
       delay = min(cap, base * 2 ** (attempt - 1))
       sleep = random.uniform(0, delay)      # джиттер размазывает волну
3. КЛЮЧ ИДЕМПОТЕНТНОСТИ генерируется ДО первой попытки и один на ВСЕ
   попытки операции. Ключ на каждую попытку — классическая ошибка:
   сервер считает каждый повтор новой операцией, дубли возвращаются.
"""

import logging
import random
import uuid
from dataclasses import dataclass, field

import anyio
import httpx

log = logging.getLogger("devices.client")

RETRYABLE_STATUS = {500, 502, 503, 504}


@dataclass
class CallResult:
    """Итог вызова: сколько попыток, чем кончилось, какой ключ."""

    ok: bool = False
    status: int | None = None
    body: dict | None = None
    attempts: int = 0
    idempotency_key: str | None = None
    attempt_log: list[str] = field(default_factory=list)


def new_idempotency_key() -> str:
    """Ключ генерирует КЛИЕНТ до первой попытки (семантика Stripe)."""
    return f"idem-{uuid.uuid4()}"


def backoff_delay(attempt: int, *, base: float, cap: float, jitter: bool) -> float:
    """Пауза перед попыткой attempt+1. Full jitter: uniform(0, delay)."""
    delay = min(cap, base * 2 ** (attempt - 1))
    return random.uniform(0.0, delay) if jitter else delay


async def post_with_retries(
    url: str,
    payload: dict,
    *,
    read_timeout: float = 0.8,
    max_attempts: int = 4,
    backoff_base: float = 0.2,
    backoff_cap: float = 2.0,
    jitter: bool = True,
    idempotency_key: str | None = None,
    mark_first_attempt_lost: bool = False,
) -> CallResult:
    """POST с таймаутом и ретраями; повторяет ТОЛЬКО сетевые ошибки и 5xx.

    mark_first_attempt_lost: пометить первую попытку заголовком
    X-Debug-Lose-Response — сервис alerts задержит ответ дольше таймаута,
    воспроизводя «потерянный ответ» детерминированно (для демонстрации).
    """
    result = CallResult(idempotency_key=idempotency_key)
    timeout = httpx.Timeout(connect=1.0, read=read_timeout, write=1.0, pool=1.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_attempts + 1):
            result.attempts = attempt
            headers = {"X-Attempt": str(attempt)}
            if idempotency_key is not None:
                headers["Idempotency-Key"] = idempotency_key
            if mark_first_attempt_lost and attempt == 1:
                headers["X-Debug-Lose-Response"] = "1"
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.TransportError as exc:
                # Сетевая ошибка или таймаут: исход «неизвестно» —
                # сервер МОГ обработать запрос. Повторять без ключа опасно.
                result.attempt_log.append(f"attempt {attempt}: {type(exc).__name__}")
                log.warning("attempt %d/%d: %s", attempt, max_attempts, type(exc).__name__)
            else:
                result.status = resp.status_code
                if resp.status_code < 500:
                    # 2xx — успех; 4xx — чини запрос, повтор не поможет.
                    result.ok = resp.status_code < 400
                    result.body = resp.json()
                    replayed = resp.headers.get("Idempotency-Replayed", "-")
                    result.attempt_log.append(
                        f"attempt {attempt}: HTTP {resp.status_code} (replayed={replayed})"
                    )
                    log.info(
                        "attempt %d/%d: HTTP %d replayed=%s",
                        attempt, max_attempts, resp.status_code, replayed,
                    )
                    return result
                result.attempt_log.append(f"attempt {attempt}: HTTP {resp.status_code}")
                log.warning("attempt %d/%d: HTTP %d", attempt, max_attempts, resp.status_code)

            if attempt == max_attempts:
                break  # потолок попыток: не долбим сервис бесконечно
            pause = backoff_delay(attempt, base=backoff_base, cap=backoff_cap, jitter=jitter)
            result.attempt_log.append(f"backoff {pause:.3f} s (jitter={'on' if jitter else 'off'})")
            await anyio.sleep(pause)

    return result
