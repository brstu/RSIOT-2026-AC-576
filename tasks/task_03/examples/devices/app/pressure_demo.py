"""Демонстрация backpressure: N параллельных показаний против devices.

Запуск (из папки examples, alerts предварительно заморожен —
`docker compose pause alerts`):

    docker compose exec devices python -m app.pressure_demo --clients 12

Все показания выше порога, поэтому каждое требует вызова alerts. Пока
alerts заморожен и BREAKER=off, каждый вызов честно висит на таймаутах и
занимает слот (MAX_CONCURRENT). Лишние запросы получают мгновенный
503 + Retry-After — это и есть honest backpressure: система говорит
«мне плохо, приходи позже» вместо бесконечной очереди.

Сравните два прогона:
  BREAKER=off → почти все запросы либо висят секунды, либо 503;
  BREAKER=on  → после открытия breaker'а все запросы мгновенные 202.
"""

import argparse
import asyncio
import os
import statistics
import time

import httpx

DEVICES_URL = os.getenv("DEVICES_URL", "http://127.0.0.1:8080")


async def one_client(n: int, results: list[dict]) -> None:
    payload = {"device_id": f"press-{n}", "sensor": "pressure-demo", "value": 99.9}
    t0 = time.monotonic()
    outcome = "error"
    retry_after = "-"
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        try:
            resp = await client.post(f"{DEVICES_URL}/readings", json=payload)
            outcome = str(resp.status_code)
            retry_after = resp.headers.get("Retry-After", "-")
        except httpx.TransportError as exc:
            outcome = type(exc).__name__
    results.append({
        "client": n,
        "outcome": outcome,
        "retry_after": retry_after,
        "ms": (time.monotonic() - t0) * 1000,
    })


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backpressure demo")
    parser.add_argument("--clients", type=int, default=12)
    args = parser.parse_args()

    results: list[dict] = []
    t0 = time.monotonic()
    await asyncio.gather(*[one_client(n, results) for n in range(args.clients)])
    wall = time.monotonic() - t0

    print(f"clients={args.clients} wall={wall:.1f}s")
    print()
    by_outcome: dict[str, list[float]] = {}
    for r in sorted(results, key=lambda r: r["client"]):
        print(
            f"client {r['client']:2d}: {r['outcome']:>16s} "
            f"{r['ms']:8.0f} ms  Retry-After={r['retry_after']}"
        )
        by_outcome.setdefault(r["outcome"], []).append(r["ms"])
    print()
    for outcome, times in sorted(by_outcome.items()):
        print(
            f"{outcome:>16s}: {len(times):2d} шт, "
            f"медиана {statistics.median(times):7.0f} ms, max {max(times):7.0f} ms"
        )
    print()
    print("503 = honest backpressure (мгновенный отказ + Retry-After);")
    print("долгие 201/202 = запрос ждал таймауты alerts — сравните с BREAKER=on")


if __name__ == "__main__":
    asyncio.run(main())
