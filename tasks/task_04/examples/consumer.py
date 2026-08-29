"""Консюмер телеметрии «СмартДома» (вариант 0: термостаты).

Демонстрирует весь конвейер лекций 12–13:
- консюмер-группа rule-engine, auto-commit ВЫКЛЮЧЕН;
- обработка -> коммит offset ПОСЛЕ обработки = at-least-once;
- идемпотентность: дедупликация по event_id в SQLite (processed.db) —
  проверка и «бизнес-эффект» в одной транзакции;
- DLQ: битое сообщение после 3 попыток уезжает в <topic>.dlq;
- флаг --crash-before-commit: обработать одно сообщение и умереть ДО
  коммита — чтобы своими глазами поймать дубль после рестарта.

Запуск:  python consumer.py [--broker ...] [--topic readings.thermo]
         python consumer.py --crash-before-commit   # эксперимент «дубль»
"""
import argparse
import json
import sqlite3
import sys

from confluent_kafka import Consumer, KafkaError, Producer

ALERT_THRESHOLD_C = 28.0   # правило варианта 0: перегрев
MAX_ATTEMPTS = 3           # попыток обработки до отправки в DLQ


def open_dedup_db(path: str = "processed.db") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS processed_events "
               "(event_id TEXT PRIMARY KEY)")
    db.commit()
    return db


def handle(event: dict) -> None:
    """«Бизнес-обработка»: правило тревоги (в реальности — запись в БД, push)."""
    t = event["payload"]["temperature_c"]
    dev = event["payload"]["device_id"]
    if t > ALERT_THRESHOLD_C:
        print(f"  ALERT! {dev}: {t}°C > {ALERT_THRESHOLD_C}°C")
    else:
        print(f"  ok {dev}: {t}°C")


def process_idempotent(db: sqlite3.Connection, raw: bytes) -> None:
    """Разбор + дедупликация + эффект в ОДНОЙ транзакции SQLite.

    Бросает исключение на битом сообщении — его поймает retry/DLQ-контур.
    """
    event = json.loads(raw)                      # ядовитое сообщение упадёт тут
    event_id = event["event_id"]                 # или тут, если поля нет
    cur = db.execute(
        "INSERT OR IGNORE INTO processed_events(event_id) VALUES (?)",
        (event_id,))
    if cur.rowcount == 0:                        # уже видели: дубль
        print(f"  duplicate skipped: {event_id}")
        db.rollback()
        return
    handle(event)                                # эффект + отметка атомарны:
    db.commit()                                  # либо оба, либо ни одного


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="localhost:9092")
    ap.add_argument("--topic", default="readings.thermo")
    ap.add_argument("--group", default="rule-engine")
    ap.add_argument("--crash-before-commit", action="store_true",
                    help="обработать 1 сообщение и умереть ДО коммита offset")
    args = ap.parse_args()

    consumer = Consumer({
        "bootstrap.servers": args.broker,
        "group.id": args.group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,     # семантику задаём сами (лекция 12)
    })
    dlq = Producer({"bootstrap.servers": args.broker, "acks": "all"})
    db = open_dedup_db()

    consumer.subscribe(
        [args.topic],
        on_assign=lambda c, parts: print(
            f"назначены партиции: {[p.partition for p in parts]}"))

    print(f"группа {args.group}, топик {args.topic}; Ctrl+C — стоп")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"!! ошибка брокера: {msg.error()}")
                continue

            # --- обработка с ретраями и DLQ ---
            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    process_idempotent(db, msg.value())
                    break
                except Exception as exc:  # noqa: BLE001 — учебный обработчик
                    print(f"  попытка {attempt}/{MAX_ATTEMPTS} не удалась: {exc}")
                    if attempt == MAX_ATTEMPTS:
                        dlq.produce(
                            topic=f"{args.topic}.dlq",
                            key=msg.key(),
                            value=json.dumps({
                                "error": str(exc),
                                "original": msg.value().decode(errors="replace"),
                            }).encode())
                        dlq.flush(5)
                        print("  -> отправлено в DLQ, едем дальше")

            if args.crash_before_commit:
                print("CRASH до коммита offset (эксперимент части 4). "
                      "Перезапустите консюмера и наблюдайте дубль.")
                sys.exit(1)              # offset не закоммичен!

            consumer.commit(msg)         # коммит ПОСЛЕ обработки = at-least-once
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        db.close()
        print("консюмер остановлен")


if __name__ == "__main__":
    main()
