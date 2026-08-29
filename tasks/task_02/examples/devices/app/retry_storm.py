"""Демонстрация retry storm: N клиентов ретраят в окно отказа alerts.

Запуск (из папки examples, оба сервиса подняты):

    docker compose exec devices python -m app.retry_storm --clients 30 --outage 3 --jitter off
    docker compose exec devices python -m app.retry_storm --clients 30 --outage 3 --jitter on

Сценарий: скрипт включает на alerts окно отказа (`POST /outage`), затем
одновременно запускает N клиентов; каждый POST-ит тревогу с ретраями.
Пока окно активно, alerts отвечает 503 — клиенты уходят в backoff.

БЕЗ джиттера все клиенты спят одинаковые паузы и возвращаются ВОЛНАМИ —
в гистограмме видны пики высотой почти в N запросов (это и есть retry
storm / herd effect, ср. сбой Google Cloud 12.06.2025 из лекции 03).
С джиттером паузы случайны, волна размазывается, пик падает в разы.

Сравнивайте строку «пик запросов в одном окне» двух прогонов.
"""

import argparse
import asyncio
import os
import time

import httpx

from app.client import backoff_delay

ALERTS_URL = os.getenv("ALERTS_URL", "http://localhost:8081")
BUCKET = 0.2  # ширина окна гистограммы, секунд


async def storm_client(
    n: int,
    t0: float,
    attempts_ts: list[float],
    *,
    max_attempts: int,
    base: float,
    cap: float,
    jitter: bool,
) -> bool:
    """Один клиент: POST /alerts с ретраями; пишет время каждой попытки."""
    payload = {
        "device_id": f"storm-{n}",
        "sensor": "storm",
        "value": 100.0,
        "reason": "retry-storm-demo",
    }
    timeout = httpx.Timeout(connect=1.0, read=2.0, write=1.0, pool=None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_attempts + 1):
            attempts_ts.append(time.monotonic() - t0)
            try:
                resp = await client.post(f"{ALERTS_URL}/alerts", json=payload)
                if resp.status_code < 500:
                    return resp.status_code < 400
            except httpx.TransportError:
                pass
            if attempt < max_attempts:
                await asyncio.sleep(backoff_delay(attempt, base=base, cap=cap, jitter=jitter))
    return False


def print_histogram(attempts_ts: list[float]) -> int:
    """ASCII-гистограмма: сколько запросов пришло в каждое окно BUCKET с."""
    if not attempts_ts:
        return 0
    horizon = max(attempts_ts)
    buckets: dict[int, int] = {}
    for ts in attempts_ts:
        buckets[int(ts / BUCKET)] = buckets.get(int(ts / BUCKET), 0) + 1
    peak = max(buckets.values())
    scale = max(1, peak // 50)  # не шире ~50 символов
    for i in range(int(horizon / BUCKET) + 1):
        count = buckets.get(i, 0)
        bar = "#" * (count // scale)
        print(f"{i * BUCKET:5.1f}-{(i + 1) * BUCKET:4.1f} s | {bar}{'' if count else '.'} {count}")
    return peak


async def main() -> None:
    parser = argparse.ArgumentParser(description="Retry storm demo")
    parser.add_argument("--clients", type=int, default=30)
    parser.add_argument("--outage", type=float, default=3.0, help="окно отказа alerts, секунд")
    parser.add_argument("--jitter", choices=["on", "off"], default="off")
    parser.add_argument("--attempts", type=int, default=7)
    parser.add_argument("--base", type=float, default=0.5)
    parser.add_argument("--cap", type=float, default=8.0)
    args = parser.parse_args()
    jitter = args.jitter == "on"

    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(f"{ALERTS_URL}/outage", params={"seconds": args.outage})

    print(f"clients={args.clients} outage={args.outage}s jitter={args.jitter} "
          f"base={args.base} cap={args.cap} attempts<={args.attempts}")

    attempts_ts: list[float] = []
    t0 = time.monotonic()
    results = await asyncio.gather(*[
        storm_client(
            n, t0, attempts_ts,
            max_attempts=args.attempts, base=args.base, cap=args.cap, jitter=jitter,
        )
        for n in range(args.clients)
    ])
    wall = time.monotonic() - t0

    print()
    peak = print_histogram(attempts_ts)
    print()
    print(f"итого запросов к alerts : {len(attempts_ts)}")
    print(f"пик запросов в одном окне {BUCKET} s : {peak}  <-- сравните off vs on")
    print(f"клиентов успешно        : {sum(results)}/{args.clients}")
    print(f"общее время             : {wall:.1f} s")


if __name__ == "__main__":
    asyncio.run(main())
