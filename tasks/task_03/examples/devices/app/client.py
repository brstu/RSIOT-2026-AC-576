"""HTTP-клиент devices → alerts: таймауты + короткие ретраи (наследие лабы 2).

В лабе 3 клиент нарочно проще, чем в лабе 2: ретраев мало (по умолчанию 2
попытки), потому что над клиентом теперь стоит circuit breaker (breaker.py).
Ретраи лечат КОРОТКИЙ сбой (моргнула сеть), breaker — ДЛИННЫЙ (зависимость
лежит): без breaker'а каждый вызов честно отрабатывает все попытки и
таймауты, и devices «зависает» на каждой тревоге — это вы видите в первом
успехе лабы.

Idempotency-Key остаётся из лабы 2: он же защищает от дублей при догоне
очереди fallback (recovery), когда alerts оживает.
"""

import logging
import random
import uuid
from dataclasses import dataclass, field

import anyio
import httpx

log = logging.getLogger("devices.client")


@dataclass
class CallResult:
    """Итог вызова: чем кончилось и сколько было попыток."""

    ok: bool = False
    status: int | None = None
    body: dict | None = None
    attempts: int = 0
    attempt_log: list[str] = field(default_factory=list)


def new_idempotency_key() -> str:
    """Ключ генерирует клиент ДО первой попытки (лаба 2, семантика Stripe)."""
    return f"idem-{uuid.uuid4()}"


def backoff_delay(attempt: int, *, base: float, cap: float) -> float:
    """Экспоненциальный backoff с full jitter (лаба 2)."""
    return random.uniform(0.0, min(cap, base * 2 ** (attempt - 1)))


async def post_with_retries(
    url: str,
    payload: dict,
    *,
    connect_timeout: float = 1.0,
    read_timeout: float = 0.8,
    max_attempts: int = 2,
    backoff_base: float = 0.2,
    backoff_cap: float = 1.0,
    idempotency_key: str | None = None,
) -> CallResult:
    """POST с таймаутами; повторяет ТОЛЬКО сетевые ошибки, таймауты и 5xx."""
    result = CallResult()
    timeout = httpx.Timeout(
        connect=connect_timeout, read=read_timeout, write=1.0, pool=1.0,
    )
    headers = {}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_attempts + 1):
            result.attempts = attempt
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.TransportError as exc:
                # Сеть или таймаут: исход «неизвестно» из лекции 03.
                result.attempt_log.append(f"attempt {attempt}: {type(exc).__name__}")
                log.warning(
                    "attempt %d/%d: %s", attempt, max_attempts, type(exc).__name__,
                )
            else:
                result.status = resp.status_code
                result.attempt_log.append(f"attempt {attempt}: HTTP {resp.status_code}")
                if resp.status_code < 500:
                    # 2xx — успех; 4xx — чини запрос, повтор не поможет.
                    result.ok = resp.status_code < 400
                    result.body = resp.json()
                    return result
                log.warning(
                    "attempt %d/%d: HTTP %d", attempt, max_attempts, resp.status_code,
                )

            if attempt == max_attempts:
                break
            await anyio.sleep(
                backoff_delay(attempt, base=backoff_base, cap=backoff_cap),
            )

    return result
