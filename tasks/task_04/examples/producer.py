"""Продюсер телеметрии «СмартДома» (вариант 0: термостаты).

Шлёт события ReadingRecorded в топик readings.thermo с ключом device_id:
события одного устройства попадают в одну партицию и упорядочены (лекция 12).

Надёжность: acks=all (подтверждают все ISR) + идемпотентный продюсер
(ретраи не дублируют и не переставляют записи).

Запуск:  python producer.py [--broker localhost:9092] [--topic readings.thermo]
Остановка: Ctrl+C
"""
import argparse
import json
import random
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer

DEVICES = ["dev-11", "dev-17", "dev-23", "dev-42"]  # 4 термостата


def make_event(device_id: str) -> dict:
    """Конверт события (лекция 13): id, тип в прошедшем времени, версия, время."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "ReadingRecorded",
        "schema_version": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "device_id": device_id,
            "sensor": "temperature",
            "temperature_c": round(random.uniform(18.0, 31.0), 1),
        },
    }


def on_delivery(err, msg):
    """Колбэк подтверждения: видно, в какую партицию лёг каждый ключ."""
    if err is not None:
        print(f"!! доставка не удалась: {err}")
    else:
        print(f"-> key={msg.key().decode()} partition={msg.partition()} "
              f"offset={msg.offset()}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", default="localhost:9092")
    ap.add_argument("--topic", default="readings.thermo")
    args = ap.parse_args()

    producer = Producer({
        "bootstrap.servers": args.broker,
        "acks": "all",                 # ждём все ISR — не потеряем при смене лидера
        "enable.idempotence": True,    # ретраи без дублей и перестановок
    })

    print(f"продюсер: топик {args.topic}, устройства {DEVICES}; Ctrl+C — стоп")
    try:
        while True:
            device = random.choice(DEVICES)
            event = make_event(device)
            producer.produce(
                topic=args.topic,
                key=device.encode(),                    # ключ = агрегат
                value=json.dumps(event).encode(),
                on_delivery=on_delivery,
            )
            producer.poll(0)          # обслуживаем колбэки доставки
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush(10)            # дожать недоставленное перед выходом
        print("продюсер остановлен")


if __name__ == "__main__":
    main()
