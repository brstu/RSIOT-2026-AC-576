"""Fallback-очередь тревог в файле: деградация вместо 500 (лекция 09).

Когда alerts недоступен (breaker OPEN или вызов провалился), тревогу нельзя
просто выбросить и нельзя отдать жильцу 500 — её кладут в локальную очередь,
а фоновый догон (drain_loop в main.py) доставит её после восстановления.
Вместе с тревогой сохраняется её Idempotency-Key: если ответ alerts потерялся
ПОСЛЕ создания тревоги, догон не породит дубль (лаба 2).

Источник истины — список в памяти процесса; каждый успешный enqueue/pop
синхронно переписывает jsonl-файл (это артефакт для отчёта и защита от
docker stop/start). Ограничение честно: при пересоздании контейнера
(`docker compose up -d devices`) файл в /tmp теряется — в реальной системе
здесь Redis или диск-том.

Очередь ограничена: переполнение = ошибка (load shedding, лекция 09) —
бесконечный буфер лишь оттягивает и укрупняет отказ.
"""

import json
import logging
import os
import time

log = logging.getLogger("devices.fallback")

QUEUE_PATH = os.getenv("FALLBACK_QUEUE", "/tmp/fallback_queue.jsonl")
QUEUE_LIMIT = int(os.getenv("FALLBACK_QUEUE_LIMIT", "100"))

_queue: list[dict] = []


class QueueFull(Exception):
    """Очередь fallback переполнена — дальше только honest-отказ."""


def _flush() -> None:
    with open(QUEUE_PATH, "w", encoding="utf-8") as fh:
        for item in _queue:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def load_from_disk() -> int:
    """Подхватить очередь после рестарта процесса (docker stop/start)."""
    if not os.path.exists(QUEUE_PATH):
        return 0
    _queue.clear()
    with open(QUEUE_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                _queue.append(json.loads(line))
    log.info("fallback: из файла восстановлено %d тревог", len(_queue))
    return len(_queue)


def enqueue(payload: dict, idempotency_key: str) -> int:
    """Положить недоставленную тревогу в очередь; вернуть её размер."""
    if len(_queue) >= QUEUE_LIMIT:
        raise QueueFull(f"очередь fallback полна ({QUEUE_LIMIT})")
    _queue.append({
        "payload": payload,
        "idempotency_key": idempotency_key,
        "enqueued_at": time.time(),
    })
    _flush()
    log.info("fallback: тревога в очередь (size=%d)", len(_queue))
    return len(_queue)


def peek() -> dict | None:
    return _queue[0] if _queue else None


def pop_first() -> None:
    """Убрать доставленную тревогу из головы очереди."""
    _queue.pop(0)
    _flush()


def size() -> int:
    return len(_queue)
